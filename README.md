# AI Recipe Generator (Flask)

A full-stack college project: a pantry-aware AI recipe generator built with
Flask, SQLAlchemy, Flask-Login, and Flask-WTF, with a green food-tech UI.

## Features
- User registration / login / logout with hashed passwords, "remember me", and flash messages
- Dashboard with AI recipe generation (meal-type filters, generate button, recipe cards with AI match %, favourite/save/view actions)
- AI generation via Google Gemini, with an automatic **offline fallback generator** so the app fully works with zero API key
- Pantry module: add/delete/search ingredients, category filter, quick-add chips
- Weekly meal planner with a calendar layout, daily calorie progress ring, add/remove meals
- Favourites: heart-toggle, search, persisted in SQLite
- Profile: name, diet preference, allergies, daily calorie goal

## Setup

```bash
cd AI_Recipe_Generator
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional: add a GEMINI_API_KEY here
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The SQLite database (`database.db`) and all tables are created automatically
on first run — no manual migration step needed.

## Using the Gemini API (optional)

If you have a Gemini API key:
1. Put it in `.env` as `GEMINI_API_KEY=your-key-here` (or set it as an environment variable).
2. Restart the app.

Without a key, or if the Gemini call fails for any reason, the app
transparently falls back to a built-in rule-based recipe generator — the
"Generate Recipes" button always works.

## Project Structure

```
AI_Recipe_Generator/
├── app.py                # Routes / application entry point
├── config.py             # Configuration (secret key, DB URI, Gemini settings)
├── models.py              # SQLAlchemy models (User, Pantry, Recipe, Favorite, MealPlanner)
├── forms.py               # Flask-WTF forms
├── ai_engine.py           # Gemini call + offline fallback recipe generator
├── requirements.txt
├── templates/
│   ├── base.html, login.html, register.html, dashboard.html,
│   │   pantry.html, meal_plan.html, favorites.html, profile.html,
│   │   recipe_details.html, _recipe_card.html, 404.html, 500.html
└── static/
    ├── css/style.css
    └── js/script.js
```

## Notes
- Since no UI screenshots were attached to this build, the interface was
  designed from scratch following the brief's spec (green palette, sidebar,
  cards, rounded corners) rather than matched pixel-for-pixel to an existing
  mockup. Colours and components live in CSS variables at the top of
  `static/css/style.css` if you want to retheme anything.
