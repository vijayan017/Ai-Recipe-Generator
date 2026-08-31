"""
AI Recipe Generation Engine.

Tries Google Gemini first (if an API key is configured). If the key is
missing, the request fails, or the response can't be parsed, it falls
back to a built-in intelligent recipe generator so the app always works
end to end, even completely offline.
"""

import json
import random
import re

# --- Small built-in knowledge base used by the fallback generator ---

CUISINE_STYLES = ["Indian", "Italian", "Mexican", "Chinese", "Continental", "Thai", "Mediterranean"]

COOKING_VERBS = ["Saute", "Simmer", "Toss", "Grill", "Stir-fry", "Roast", "Bake"]

BASE_TEMPLATES = {
    "Breakfast": ["{main} Breakfast Bowl", "{main} Omelette", "Quick {main} Toast", "{main} Smoothie Bowl"],
    "Lunch": ["{main} Power Bowl", "{main} Wrap", "{main} Fried Rice", "{main} Salad"],
    "Dinner": ["{main} Curry", "{main} Stir-fry", "Baked {main}", "{main} Pasta"],
    "Snack": ["{main} Bites", "Crispy {main} Fritters", "{main} Sandwich", "{main} Chaat"],
}


def _pick_main_ingredient(pantry_items):
    """Pick a 'hero' ingredient to build the recipe name/story around."""
    priority = ["chicken", "paneer", "egg", "rice", "potato", "tofu", "fish", "mushroom", "lentil", "beans"]
    lowered = [i.lower() for i in pantry_items]
    for p in priority:
        for item in lowered:
            if p in item:
                return item.title()
    if pantry_items:
        return pantry_items[0].title()
    return "Veggie"


def _estimate_calories(meal_type, calorie_goal):
    ratios = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30, "Snack": 0.10}
    base = int(calorie_goal * ratios.get(meal_type, 0.3))
    return max(150, base + random.randint(-40, 60))


def generate_fallback_recipes(pantry_items, meal_type="Dinner", diet="None",
                               allergies="", calorie_goal=2000, cuisine="Any", count=3):
    """
    Rule-based recipe generator used whenever the Gemini API is not
    available. Produces realistic, varied recipes using the user's
    pantry ingredients.
    """
    allergy_list = [a.strip().lower() for a in allergies.split(",") if a.strip()]
    usable = [i for i in pantry_items if not any(a in i.lower() for a in allergy_list)]
    if not usable:
        usable = ["Onion", "Garlic", "Tomato", "Rice", "Oil", "Salt", "Pepper"]

    recipes = []
    templates = BASE_TEMPLATES.get(meal_type, BASE_TEMPLATES["Dinner"])

    for i in range(count):
        main = _pick_main_ingredient(usable)
        template = random.choice(templates)
        title = template.format(main=main)

        # Ingredients used: a rotating subset of the pantry plus staples
        random.shuffle(usable)
        used_ingredients = list(dict.fromkeys(usable[: min(len(usable), 5)] + ["Salt", "Oil", "Pepper"]))

        # Missing ingredients: a couple of common extras not in pantry
        common_extras = ["Garlic", "Ginger", "Lemon", "Coriander leaves", "Butter", "Cheese"]
        missing = [x for x in common_extras if x.lower() not in [u.lower() for u in used_ingredients]]
        random.shuffle(missing)
        missing = missing[:2]

        cook_time = random.choice([15, 20, 25, 30, 40, 45])
        difficulty = random.choice(["Easy", "Easy", "Medium", "Hard"])
        chosen_cuisine = cuisine if cuisine and cuisine != "Any" else random.choice(CUISINE_STYLES)
        calories = _estimate_calories(meal_type, calorie_goal)
        match_percent = int(100 * len(used_ingredients[:-3] if len(used_ingredients) > 3 else used_ingredients) /
                             max(1, len(used_ingredients) + len(missing)))
        match_percent = min(98, max(55, match_percent + random.randint(-5, 10)))

        verb = random.choice(COOKING_VERBS)
        steps = [
            f"Prep all ingredients: wash, peel and chop {main.lower()} and vegetables into even pieces.",
            f"Heat oil in a pan and {verb.lower()} the aromatics (onion, garlic, ginger) until fragrant.",
            f"Add {main.lower()} along with the remaining pantry ingredients, season with salt and pepper.",
            f"Cook on medium heat for about {max(5, cook_time - 10)} minutes, stirring occasionally.",
            "Adjust seasoning, garnish with fresh herbs, and serve hot." if missing else
            "Adjust seasoning to taste and serve hot.",
        ]

        description = (
            f"A {difficulty.lower()}-difficulty {chosen_cuisine} {meal_type.lower()} built around "
            f"{main.lower()}, ready in about {cook_time} minutes and tuned for a "
            f"{diet.lower() if diet and diet != 'None' else 'balanced'} diet."
        )

        nutrition = {
            "calories": calories,
            "protein_g": random.randint(8, 35),
            "carbs_g": random.randint(15, 60),
            "fat_g": random.randint(5, 25),
        }

        recipes.append({
            "title": title,
            "description": description,
            "ingredients": used_ingredients,
            "missing_ingredients": missing,
            "instructions": steps,
            "cook_time": cook_time,
            "calories": calories,
            "difficulty": difficulty,
            "cuisine": chosen_cuisine,
            "meal_type": meal_type,
            "match_percent": match_percent,
            "nutrition": nutrition,
        })

    return recipes


def _build_prompt(pantry_items, meal_type, diet, allergies, calorie_goal, cuisine, count):
    return f"""
You are a professional chef and nutritionist API. Generate {count} distinct recipes as a
JSON array only, with NO markdown fences and NO extra commentary. Each recipe object must
have EXACTLY these keys:
title (string), description (string, 1-2 sentences), ingredients (array of strings the
user already has), missing_ingredients (array of strings the user needs to buy),
instructions (array of short step strings), cook_time (integer minutes), calories
(integer), difficulty ("Easy"|"Medium"|"Hard"), cuisine (string), meal_type (string),
match_percent (integer 0-100 estimating how well the pantry matches),
nutrition (object with protein_g, carbs_g, fat_g integers).

Constraints:
- Pantry ingredients available: {", ".join(pantry_items) if pantry_items else "none listed"}
- Meal type: {meal_type}
- Diet preference: {diet}
- Allergies to avoid completely: {allergies if allergies else "none"}
- Daily calorie goal: {calorie_goal} (portion calories should be reasonable for one meal)
- Preferred cuisine: {cuisine}

Return ONLY the JSON array.
""".strip()


def _extract_json_array(text):
    """Best-effort extraction of a JSON array from a raw model response."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def generate_recipes(api_key, model_name, pantry_items, meal_type="Dinner", diet="None",
                      allergies="", calorie_goal=2000, cuisine="Any", count=3):
    """
    Main entry point used by the Flask routes. Tries Gemini, falls back
    to the rule-based generator on any failure.
    """
    if api_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            prompt = _build_prompt(pantry_items, meal_type, diet, allergies, calorie_goal, cuisine, count)
            response = model.generate_content(prompt)
            data = _extract_json_array(response.text)

            # Basic validation / normalization
            cleaned = []
            for r in data:
                cleaned.append({
                    "title": r.get("title", "AI Recipe"),
                    "description": r.get("description", ""),
                    "ingredients": r.get("ingredients", []),
                    "missing_ingredients": r.get("missing_ingredients", []),
                    "instructions": r.get("instructions", []),
                    "cook_time": int(r.get("cook_time", 30) or 30),
                    "calories": int(r.get("calories", 400) or 400),
                    "difficulty": r.get("difficulty", "Easy"),
                    "cuisine": r.get("cuisine", cuisine),
                    "meal_type": r.get("meal_type", meal_type),
                    "match_percent": int(r.get("match_percent", 70) or 70),
                    "nutrition": r.get("nutrition", {}),
                })
            if cleaned:
                return cleaned, "gemini"
        except Exception:
            # Silently fall through to the offline generator
            pass

    return generate_fallback_recipes(
        pantry_items, meal_type, diet, allergies, calorie_goal, cuisine, count
    ), "fallback"
