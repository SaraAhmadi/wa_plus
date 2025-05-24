#!/bin/sh
set -e

echo "WAPlus Dashboard Entrypoint: Starting up..."

# Run database migrations
echo "Running database migrations..."
export POETRY_VCS_DISABLED=1
/opt/poetry/bin/poetry run alembic upgrade head

# Execute the main container command
echo "Starting application..."
exec "$@"