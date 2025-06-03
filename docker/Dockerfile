# --- Stage 1: Build Stage (for compiling dependencies) ---
FROM python:3.11-slim AS builder

# Set environment variables for a cleaner build process
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on
ENV PIP_DEFAULT_TIMEOUT 100
ENV DEBIAN_FRONTEND=noninteractive

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Install build-time system dependencies from Debian Bookworm's repositories
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    pkg-config \
    curl \
    wget \
    gnupg \
    ca-certificates \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install "psycopg2-binary==2.9.9"

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION="1.8.2"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION"

WORKDIR /app

# Copy from app directory in project root
COPY app/pyproject.toml app/poetry.lock ./

# Install Python dependencies using Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# --- Stage 2: Final Production Stage ---
FROM python:3.11-slim AS final_stage

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_ENV="production"
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV DEBIAN_FRONTEND=noninteractive

# Copy Poetry installation from builder
COPY --from=builder /opt/poetry /opt/poetry

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    postgis \
    libgeos-c1v5 \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN groupadd -r appgroup && \
    useradd --no-log-init -m -r -g appgroup appuser

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

## Copy application code from app directory
COPY --chown=appuser:appgroup app/core /app/core
COPY --chown=appuser:appgroup app/gunicorn_conf.py /app/gunicorn_conf.py
COPY --chown=appuser:appgroup app/entrypoint.sh /app/entrypoint.sh
COPY --chown=appuser:appgroup app/pyproject.toml /app/pyproject.toml
COPY --chown=appuser:appgroup app/poetry.lock /app/poetry.lock

RUN chmod u+x /app/entrypoint.sh

USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn_conf.py", "core.wsgi:application"]