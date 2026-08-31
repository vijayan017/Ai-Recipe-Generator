"""
Flask-WTF form definitions for authentication and profile management.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    diet = SelectField(
        "Diet Preference",
        choices=[
            ("None", "None"), ("Vegetarian", "Vegetarian"), ("Vegan", "Vegan"),
            ("Keto", "Keto"), ("Low Carb", "Low Carb"), ("Gluten Free", "Gluten Free"),
            ("Halal", "Halal"), ("Kosher", "Kosher"),
        ],
    )
    allergies = TextAreaField("Allergies (comma separated)", validators=[Optional(), Length(max=255)])
    calorie_goal = IntegerField("Daily Calorie Goal", validators=[DataRequired(), NumberRange(min=800, max=6000)])


class PantryForm(FlaskForm):
    ingredient = StringField("Ingredient", validators=[DataRequired(), Length(min=1, max=150)])
    category = SelectField(
        "Category",
        choices=[
            ("Vegetables", "Vegetables"), ("Fruits", "Fruits"), ("Grains", "Grains"),
            ("Dairy", "Dairy"), ("Protein", "Protein"), ("Spices", "Spices"),
            ("Condiments", "Condiments"), ("Other", "Other"),
        ],
    )
    quantity = StringField("Quantity", validators=[Optional(), Length(max=50)])
