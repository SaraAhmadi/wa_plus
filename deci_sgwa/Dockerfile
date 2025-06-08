# --- Stage 1: Build Stage (for compiling dependencies) ---
FROM python:3.11-slim AS builder

# Set environment variables for a cleaner build process
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on
ENV PIP_DEFAULT_TIMEOUT 100
ENV DEBIAN_FRONTEND=noninteractive

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
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && echo "--- GDAL version installed in builder stage: ---" \
    && (gdalinfo --version || echo "gdalinfo not found, gdal-bin might not be fully installed or in PATH") \
    && echo "--------------------------------------------" \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install "psycopg2-binary==2.9.9"

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION="1.7.1"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry --version

WORKDIR /app
COPY /src/pyproject.toml src/poetry.lock ./

# Install Python dependencies using Poetry
# This also installs executables like gunicorn, uvicorn, alembic, celery
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main && \
    echo "--- Verifying key executables in builder stage PATH: ---" && \
    (which poetry || echo "poetry not in PATH") && \
    (which alembic || echo "alembic not in PATH") && \
    (which gunicorn || echo "gunicorn not in PATH") && \
    (which uvicorn || echo "uvicorn not in PATH") && \
    (which celery || echo "celery not in PATH") && \
    echo "----------------------------------------------------"


# --- Stage 2: Final Production Stage ---
FROM python:3.11-slim AS final_stage

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_ENV="production"
ENV POETRY_HOME="/opt/poetry"
# Critical: Ensure all relevant bin paths are included.
# /usr/local/bin is where pip often installs global scripts from packages.
# /opt/poetry/bin is where Poetry's shims/main executable might be.
ENV PATH="$POETRY_HOME/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=builder /opt/poetry /opt/poetry
COPY --from=builder /usr/local/bin/ /usr/local/bin/
# Install runtime system dependencies
# *** YOU MUST VERIFY libprojXX and libgeos-cXX names ***
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    libgdal32 \
    libproj25 \
    libgeos-c1v5 \
    postgresql-client \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN groupadd -r appgroup && \
    useradd --no-log-init -m -r -g appgroup appuser

# Copy installed Python packages (site-packages) from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages/

# Copy ALL potentially relevant bin directories where executables might be installed
# This is more comprehensive to catch tools installed by pip/poetry into system paths.
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /opt/poetry/ /opt/poetry/

# Copy application files with proper ownership
COPY --chown=appuser:appgroup /src /app/

# Optional: Debugging step to list contents of bin directories in final image
# RUN ls -lA /usr/local/bin && ls -lA /opt/poetry/bin

# --- Create and set permissions for Celery data directory ---
RUN mkdir -p /app/celery_data && \
    chown appuser:appgroup /app/celery_data

USER appuser

# Optional: Debugging step to check PATH and executables as appuser
# RUN echo "PATH as appuser: $PATH" && which poetry && which gunicorn && which uvicorn && which alembic

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "app.main:app"]