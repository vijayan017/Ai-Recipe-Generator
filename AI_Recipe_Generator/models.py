"""
SQLAlchemy models for the AI Recipe Generator application.
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile / preferences
    diet = db.Column(db.String(50), default="None")
    allergies = db.Column(db.String(255), default="")
    calorie_goal = db.Column(db.Integer, default=2000)
    avatar = db.Column(db.String(255), default="default_avatar.png")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    pantry_items = db.relationship(
        "Pantry", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    favorites = db.relationship(
        "Favorite", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    meal_plans = db.relationship(
        "MealPlanner", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    recipes = db.relationship(
        "Recipe", backref="creator", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Pantry(db.Model):
    __tablename__ = "pantry"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ingredient = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), default="Other")
    quantity = db.Column(db.String(50), default="")
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Pantry {self.ingredient}>"


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    ingredients = db.Column(db.Text, default="[]")        # JSON string list
    missing_ingredients = db.Column(db.Text, default="[]")  # JSON string list
    instructions = db.Column(db.Text, default="[]")       # JSON string list of steps
    nutrition = db.Column(db.Text, default="{}")          # JSON string dict

    calories = db.Column(db.Integer, default=0)
    cook_time = db.Column(db.Integer, default=0)  # minutes
    difficulty = db.Column(db.String(30), default="Easy")
    meal_type = db.Column(db.String(30), default="Dinner")
    cuisine = db.Column(db.String(60), default="Any")
    image = db.Column(db.String(255), default="default_recipe.jpg")
    match_percent = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Recipe {self.title}>"


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipe = db.relationship("Recipe", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_favorite"),
    )


class MealPlanner(db.Model):
    __tablename__ = "meal_planner"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)
    meal_type = db.Column(db.String(30), default="Dinner")

    recipe = db.relationship("Recipe", lazy=True)
