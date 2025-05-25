#!/bin/sh
set -e

echo "WAPlus Dashboard Entrypoint: Starting up..."

# Use POSTGRES_ variables as these are standard for PostgreSQL images and your app config
DB_WAIT_HOST="${POSTGRES_SERVER:-db}"
DB_WAIT_PORT="${POSTGRES_PORT:-5432}"
DB_WAIT_USER="${POSTGRES_USER:-waplus_user}" # Needs to be a valid DB user

echo "Waiting for PostgreSQL at $DB_WAIT_HOST:$DB_WAIT_PORT as user $DB_WAIT_USER..."
RETRY_COUNT=0
MAX_RETRIES=30

# The -q flag makes pg_isready quiet on success
until pg_isready -h "$DB_WAIT_HOST" -p "$DB_WAIT_PORT" -U "$DB_WAIT_USER" -q || [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "PostgreSQL not ready (attempt $RETRY_COUNT/$MAX_RETRIES). Retrying in 1 second..."
  sleep 1
done

if [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; then
  echo "Error: PostgreSQL at $DB_WAIT_HOST:$DB_WAIT_PORT not available after $MAX_RETRIES attempts. Exiting."
  exit 1
fi
echo "PostgreSQL is ready!"

echo "Running database migrations..."
# export POETRY_VCS_DISABLED=1 # Might not be needed unless specific VCS interaction happens
poetry run alembic upgrade head
echo "Database migrations complete."

echo "Starting application with command: $@"
exec "$@"