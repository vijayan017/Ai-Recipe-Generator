# ---------------------------------------------------------------------------
# Dockerfile - AI Recipe Generator (Flask)
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# Prevents Python from writing .pyc files & buffers stdout/stderr (good for logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS deps needed to build some Python packages (kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application code
COPY . .

# Make sure the SQLite/uploads folders exist and are writable
RUN mkdir -p /app/static/uploads

EXPOSE 5000

# Use gunicorn in production instead of Flask's dev server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]