#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB','support_tickets'),
        user=os.environ.get('POSTGRES_USER','postgres'),
        password=os.environ.get('POSTGRES_PASSWORD','postgres'),
        host=os.environ.get('POSTGRES_HOST','db'),
        port=os.environ.get('POSTGRES_PORT','5432'),
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
  echo "  DB not ready — retrying in 1s..."
  sleep 1
done

echo "PostgreSQL is ready."

python manage.py makemigrations tickets --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60