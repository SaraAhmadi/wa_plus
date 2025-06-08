# --- Stage 1: Optimized Builder Stage ---
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    libgdal-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and system packages
RUN pip install --no-cache-dir poetry==1.8.2

WORKDIR /app

# Copy dependency files
COPY /src/pyproject.toml src/poetry.lock ./

# Install Python dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# Explicitly install gunicorn
RUN pip install gunicorn==21.2.0
RUN pip install "psycopg2-binary==2.9.9"

# Verify installations
RUN pip list | grep gunicorn && \
    ls -l $(which gunicorn)

# --- Stage 2: Lean Production Stage ---
FROM python:3.11-slim AS final_stage

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    postgis \
    && rm -rf /var/lib/apt/lists/*

# Create application user and group
RUN groupadd -r appgroup && \
    useradd -r -g appgroup appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin /usr/local/bin/

# Verify gunicorn in final stage
RUN ls -l $(which gunicorn) && \
    gunicorn --help >/dev/null 2>&1

# Copy application files with proper ownership
COPY --chown=appuser:appgroup /src /app/

# Create staticfiles directory and set ownership
RUN mkdir -p /app/staticfiles && chown appuser:appgroup /app/staticfiles

# Create staticfiles directory and set ownership
RUN mkdir -p /app/staticfiles && chown appuser:appgroup /app/staticfiles

# Set permissions for entrypoint
RUN chmod u+x /app/entrypoint.sh

USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn_conf.py", "core.wsgi:application"]