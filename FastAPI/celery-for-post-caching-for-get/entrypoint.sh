#!/bin/sh


echo "Running Alembic migrations..."
alembic upgrade head

pip freeze > requirements.txt

echo "🚀 Starting Gunicorn + Uvicorn..."
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2