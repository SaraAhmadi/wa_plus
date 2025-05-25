#!/bin/sh
set -e

echo "WAPlus Dashboard Entrypoint: Starting up..."

# Database connection parameters - ensure these are set as environment variables
DB_HOST="${DB_HOST:-db}" # Default to 'db' if not set
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-user}" # User for pg_isready check

# Wait for the database to be ready
echo "Waiting for database at $DB_HOST:$DB_PORT..."
RETRY_COUNT=0
MAX_RETRIES=30 # Try for 30 seconds (e.g., 30 * 1s sleep)
# Note: pg_isready might not be available by default. This will be addressed in Dockerfile modification step.
# If using a non-PostgreSQL DB, this check needs to be different (e.g., using nc or a custom script).
until poetry run python -c "import socket; import os; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1); s.connect((os.environ['DB_HOST'], int(os.environ['DB_PORT']))); s.close()" > /dev/null 2>&1 || [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Database not ready (attempt $RETRY_COUNT/$MAX_RETRIES). Retrying in 1 second..."
  sleep 1
done

if [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; then
  echo "Error: Database at $DB_HOST:$DB_PORT not available after $MAX_RETRIES attempts. Exiting."
  exit 1
fi
echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
export POETRY_VCS_DISABLED=1
poetry run alembic upgrade head

# Execute the main container command
echo "Starting application..."
exec "$@"