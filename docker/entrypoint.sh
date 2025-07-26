#!/bin/sh

echo "Waiting for postgres..."

# Wait for PostgreSQL to be ready
/wait-for-it.sh db:5432 --timeout=30 --strict -- echo "Postgres is up"

echo "Running migrations..."
python manage.py migrate

echo "Starting server..."
exec "$@"

