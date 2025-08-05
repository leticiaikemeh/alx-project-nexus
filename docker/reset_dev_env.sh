#!/bin/bash

echo "⚠️  WARNING: This will wipe your dev database and migration history."
read -p "Continue? (y/N): " confirm
if [[ "$confirm" != "y" ]]; then
  echo "Aborted."
  exit 1
fi

echo "🔻 Stopping containers..."
docker-compose down

echo "🧨 Removing Docker volumes (Postgres/Redis)..."
docker volume prune -f

echo "🧼 Deleting all migration files..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

echo "🔨 Rebuilding containers..."
docker-compose build

echo "🚀 Starting up containers..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10  # adjust based on your app's startup time

echo "💥 Running migrations..."
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

echo "✅ Dev environment reset complete."
