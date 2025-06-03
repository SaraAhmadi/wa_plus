#!/bin/sh
set -e
echo "WAPlus Dashboard Entrypoint: Starting up for service role: ${SERVICE_ROLE:-unknown}..."

# Use POSTGRES_ variables
DB_WAIT_HOST="${POSTGRES_SERVER:-db}"
DB_WAIT_PORT="${POSTGRES_PORT:-5432}"
DB_WAIT_USER="${POSTGRES_USER:-waplus_user}"

# Only run migrations if SERVICE_ROLE is 'app' (or 'web', 'api', etc.)
if [ "$SERVICE_ROLE" = "app" ]; then
    echo "SERVICE_ROLE is 'app'. Waiting for PostgreSQL at $DB_WAIT_HOST:$DB_WAIT_PORT..."
    RETRY_COUNT=0
    MAX_RETRIES=30
    until pg_isready -h "$DB_WAIT_HOST" -p "$DB_WAIT_PORT" -U "$DB_WAIT_USER" -q || [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; do
      RETRY_COUNT=$((RETRY_COUNT + 1))
      echo "PostgreSQL not ready (attempt $RETRY_COUNT/$MAX_RETRIES). Retrying in 1 second..."
      sleep 1
    done

    if [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; then
      echo "Error: PostgreSQL at $DB_WAIT_HOST:$DB_WAIT_PORT not available after $MAX_RETRIES attempts. Exiting for 'app' service."
      exit 1
    fi
    echo "PostgreSQL is ready for 'app' service!"

    echo "Running database migrations (as SERVICE_ROLE='app')..."
    python /app/core/manage.py migrate --noinput
    echo "Database migrations complete (as SERVICE_ROLE='app')."
else
    echo "SERVICE_ROLE is '${SERVICE_ROLE}'. Skipping migrations."
    # Still wait for DB if other services need it, but don't run migrations
    echo "Waiting for PostgreSQL at $DB_WAIT_HOST:$DB_WAIT_PORT (for non-migrating service)..."
    # (You might want a shorter wait or different logic here if they don't strictly need DB for immediate startup before app)
    # For simplicity, let's assume they also wait.
    RETRY_COUNT_NON_APP=0
    until pg_isready -h "$DB_WAIT_HOST" -p "$DB_WAIT_PORT" -U "$DB_WAIT_USER" -q || [ "$RETRY_COUNT_NON_APP" -eq "$MAX_RETRIES" ]; do
      RETRY_COUNT_NON_APP=$((RETRY_COUNT_NON_APP + 1))
      sleep 1
    done
    if [ "$RETRY_COUNT_NON_APP" -eq "$MAX_RETRIES" ]; then
      echo "Warning: PostgreSQL at $DB_WAIT_HOST:$DB_WAIT_PORT not available after $MAX_RETRIES attempts for '${SERVICE_ROLE}' service. Proceeding with caution."
    else
        echo "PostgreSQL is ready for '${SERVICE_ROLE}' service!"
    fi
fi

echo "Starting application with command: $@"
exec "$@"