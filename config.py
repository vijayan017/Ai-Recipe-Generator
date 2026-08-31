"""
Configuration settings for the AI Recipe Generator application.
Loads secrets/keys from environment variables when available,
falling back to sane defaults for local development.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask settings ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Session / Remember Me ---
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # --- File uploads ---
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # --- AI (Gemini) ---
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

    # --- WTForms / CSRF ---
    WTF_CSRF_ENABLED = True
