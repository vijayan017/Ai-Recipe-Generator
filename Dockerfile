FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the app
COPY . .

# Make sure the folders the app writes to exist
RUN mkdir -p static/uploads instance

# The app defaults to a local sqlite db + file uploads dir, both inside /app
EXPOSE 5000

# Run with gunicorn (production WSGI server) instead of Flask's dev server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
