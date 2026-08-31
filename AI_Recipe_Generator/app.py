"""
AI Recipe Generator - Main Flask Application
==============================================
A college-project web app that lets users store pantry ingredients,
generate AI-powered recipes (Gemini API with an intelligent offline
fallback), plan meals for the week, and save favourites.
"""

import json
import os
from datetime import datetime, date, timedelta

from flask import (
    Flask, render_template, redirect, url_for, flash, request, jsonify, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Pantry, Recipe, Favorite, MealPlanner
from forms import RegisterForm, LoginForm, ProfileForm, PantryForm
from ai_engine import generate_recipes

# --------------------------------------------------------------------------
# App factory / initialization
# --------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def recipe_to_dict(r: Recipe, is_favorite=False):
    return {
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "ingredients": json.loads(r.ingredients or "[]"),
        "missing_ingredients": json.loads(r.missing_ingredients or "[]"),
        "instructions": json.loads(r.instructions or "[]"),
        "nutrition": json.loads(r.nutrition or "{}"),
        "calories": r.calories,
        "cook_time": r.cook_time,
        "difficulty": r.difficulty,
        "meal_type": r.meal_type,
        "cuisine": r.cuisine,
        "image": r.image,
        "match_percent": r.match_percent,
        "is_favorite": is_favorite,
    }


def get_user_favorite_ids():
    if not current_user.is_authenticated:
        return set()
    return {f.recipe_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}


# --------------------------------------------------------------------------
# Authentication Routes
# --------------------------------------------------------------------------

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("An account with that email already exists. Please log in.", "danger")
            return redirect(url_for("login"))

        user = User(name=form.name.data.strip(), email=form.email.data.lower().strip())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
# Dashboard + AI Recipe Generation
# --------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    meal_type = request.args.get("meal_type", "Dinner")
    pantry_count = Pantry.query.filter_by(user_id=current_user.id).count()

    # Show the most recently generated recipes for this user (if any),
    # otherwise an empty state prompting generation.
    recent_recipes = (
        Recipe.query.filter_by(user_id=current_user.id, meal_type=meal_type)
        .order_by(Recipe.created_at.desc())
        .limit(6)
        .all()
    )
    fav_ids = get_user_favorite_ids()
    recipes = [recipe_to_dict(r, r.id in fav_ids) for r in recent_recipes]

    return render_template(
        "dashboard.html",
        recipes=recipes,
        active_meal_type=meal_type,
        pantry_count=pantry_count,
    )


@app.route("/api/generate-recipes", methods=["POST"])
@login_required
def api_generate_recipes():
    payload = request.get_json(silent=True) or {}
    meal_type = payload.get("meal_type", "Dinner")
    diet = payload.get("diet") or current_user.diet or "None"
    allergies = payload.get("allergies") or current_user.allergies or ""
    cuisine = payload.get("cuisine") or "Any"
    calorie_goal = int(payload.get("calorie_goal") or current_user.calorie_goal or 2000)

    pantry_items = [p.ingredient for p in Pantry.query.filter_by(user_id=current_user.id).all()]

    generated, source = generate_recipes(
        api_key=app.config["GEMINI_API_KEY"],
        model_name=app.config["GEMINI_MODEL"],
        pantry_items=pantry_items,
        meal_type=meal_type,
        diet=diet,
        allergies=allergies,
        calorie_goal=calorie_goal,
        cuisine=cuisine,
        count=3,
    )

    saved = []
    for g in generated:
        recipe = Recipe(
            user_id=current_user.id,
            title=g["title"],
            description=g.get("description", ""),
            ingredients=json.dumps(g.get("ingredients", [])),
            missing_ingredients=json.dumps(g.get("missing_ingredients", [])),
            instructions=json.dumps(g.get("instructions", [])),
            nutrition=json.dumps(g.get("nutrition", {})),
            calories=g.get("calories", 0),
            cook_time=g.get("cook_time", 0),
            difficulty=g.get("difficulty", "Easy"),
            meal_type=g.get("meal_type", meal_type),
            cuisine=g.get("cuisine", cuisine),
            match_percent=g.get("match_percent", 70),
            image="default_recipe.jpg",
        )
        db.session.add(recipe)
        saved.append(recipe)

    db.session.commit()

    return jsonify({
        "success": True,
        "source": source,
        "recipes": [recipe_to_dict(r) for r in saved],
    })


@app.route("/recipe/<int:recipe_id>")
@login_required
def recipe_details(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        abort(404)
    fav_ids = get_user_favorite_ids()
    return render_template(
        "recipe_details.html",
        recipe=recipe_to_dict(recipe, recipe.id in fav_ids),
    )


# --------------------------------------------------------------------------
# Pantry Module
# --------------------------------------------------------------------------

@app.route("/pantry", methods=["GET", "POST"])
@login_required
def pantry():
    form = PantryForm()
    if form.validate_on_submit():
        item = Pantry(
            user_id=current_user.id,
            ingredient=form.ingredient.data.strip(),
            category=form.category.data,
            quantity=form.quantity.data.strip() if form.quantity.data else "",
        )
        db.session.add(item)
        db.session.commit()
        flash(f"Added '{item.ingredient}' to your pantry.", "success")
        return redirect(url_for("pantry"))

    search = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    query = Pantry.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(Pantry.ingredient.ilike(f"%{search}%"))
    if category_filter:
        query = query.filter_by(category=category_filter)

    items = query.order_by(Pantry.added_at.desc()).all()
    categories = ["Vegetables", "Fruits", "Grains", "Dairy", "Protein", "Spices", "Condiments", "Other"]

    return render_template(
        "pantry.html",
        form=form,
        items=items,
        categories=categories,
        search=search,
        category_filter=category_filter,
    )


@app.route("/pantry/quick-add", methods=["POST"])
@login_required
def pantry_quick_add():
    payload = request.get_json(silent=True) or {}
    ingredient = (payload.get("ingredient") or "").strip()
    category = payload.get("category") or "Other"

    if not ingredient:
        return jsonify({"success": False, "message": "No ingredient provided."}), 400

    exists = Pantry.query.filter_by(user_id=current_user.id, ingredient=ingredient).first()
    if exists:
        return jsonify({"success": False, "message": "Already in your pantry."}), 200

    item = Pantry(user_id=current_user.id, ingredient=ingredient, category=category)
    db.session.add(item)
    db.session.commit()

    return jsonify({"success": True, "item": {"id": item.id, "ingredient": item.ingredient, "category": item.category}})


@app.route("/pantry/delete/<int:item_id>", methods=["POST"])
@login_required
def pantry_delete(item_id):
    item = db.session.get(Pantry, item_id)
    if not item or item.user_id != current_user.id:
        abort(404)
    db.session.delete(item)
    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True})
    flash("Ingredient removed from pantry.", "info")
    return redirect(url_for("pantry"))


# --------------------------------------------------------------------------
# Meal Planner
# --------------------------------------------------------------------------

@app.route("/meal-plan")
@login_required
def meal_plan():
    # Build the current week (Mon - Sun)
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]

    plans = MealPlanner.query.filter(
        MealPlanner.user_id == current_user.id,
        MealPlanner.date.in_(week_dates),
    ).all()

    plan_by_day = {d.isoformat(): [] for d in week_dates}
    for p in plans:
        plan_by_day.setdefault(p.date.isoformat(), []).append(p)

    todays_plans = [p for p in plans if p.date == today]
    todays_calories = sum(p.recipe.calories for p in todays_plans if p.recipe)
    calorie_goal = current_user.calorie_goal or 2000
    progress_percent = min(100, int((todays_calories / calorie_goal) * 100)) if calorie_goal else 0

    favorite_recipes = [f.recipe for f in Favorite.query.filter_by(user_id=current_user.id).all()]
    recent_recipes = (
        Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).limit(12).all()
    )

    return render_template(
        "meal_plan.html",
        week_dates=week_dates,
        plan_by_day=plan_by_day,
        today=today,
        todays_calories=todays_calories,
        calorie_goal=calorie_goal,
        progress_percent=progress_percent,
        favorite_recipes=favorite_recipes,
        recent_recipes=recent_recipes,
    )


@app.route("/meal-plan/add", methods=["POST"])
@login_required
def meal_plan_add():
    payload = request.get_json(silent=True) or {}
    recipe_id = payload.get("recipe_id")
    plan_date = payload.get("date")
    meal_type = payload.get("meal_type", "Dinner")

    recipe = db.session.get(Recipe, recipe_id) if recipe_id else None
    if not recipe:
        return jsonify({"success": False, "message": "Recipe not found."}), 404

    try:
        parsed_date = datetime.strptime(plan_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        parsed_date = date.today()

    entry = MealPlanner(
        user_id=current_user.id, recipe_id=recipe.id, date=parsed_date, meal_type=meal_type
    )
    db.session.add(entry)
    db.session.commit()

    return jsonify({"success": True, "id": entry.id})


@app.route("/meal-plan/remove/<int:entry_id>", methods=["POST"])
@login_required
def meal_plan_remove(entry_id):
    entry = db.session.get(MealPlanner, entry_id)
    if not entry or entry.user_id != current_user.id:
        abort(404)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"success": True})


# --------------------------------------------------------------------------
# Favourites
# --------------------------------------------------------------------------

@app.route("/favorites")
@login_required
def favorites():
    search = request.args.get("search", "").strip()

    query = (
        db.session.query(Favorite, Recipe)
        .join(Recipe, Favorite.recipe_id == Recipe.id)
        .filter(Favorite.user_id == current_user.id)
    )
    if search:
        query = query.filter(Recipe.title.ilike(f"%{search}%"))

    results = query.order_by(Favorite.added_at.desc()).all()
    recipes = [recipe_to_dict(r, True) for (_, r) in results]

    return render_template("favorites.html", recipes=recipes, search=search)


@app.route("/favorites/toggle/<int:recipe_id>", methods=["POST"])
@login_required
def favorites_toggle(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        return jsonify({"success": False, "message": "Recipe not found."}), 404

    existing = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"success": True, "favorited": False})

    fav = Favorite(user_id=current_user.id, recipe_id=recipe_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({"success": True, "favorited": True})


# --------------------------------------------------------------------------
# Profile
# --------------------------------------------------------------------------

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.diet = form.diet.data
        current_user.allergies = form.allergies.data.strip() if form.allergies.data else ""
        current_user.calorie_goal = form.calorie_goal.data
        db.session.commit()
        flash("Preferences saved successfully.", "success")
        return redirect(url_for("profile"))

    if request.method == "GET":
        form.name.data = current_user.name
        form.diet.data = current_user.diet
        form.allergies.data = current_user.allergies
        form.calorie_goal.data = current_user.calorie_goal

    return render_template("profile.html", form=form)


# --------------------------------------------------------------------------
# Error Handlers
# --------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
