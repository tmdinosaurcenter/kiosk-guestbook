#!/bin/sh
set -e

# Fix ownership of the data directory so appuser can write the database.
# This runs as root (no USER directive in Dockerfile) and is safe because
# we immediately drop privileges via gosu before starting the app.
DATA_DIR=$(dirname "${DATABASE_PATH:-/data/guestbook.db}")
chown -R appuser:appuser "$DATA_DIR"

# Process index.html.template to create index.html
envsubst < /app/templates/index.html.template > /app/templates/index.html

# Drop to appuser and start Gunicorn
exec gosu appuser gunicorn \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout 30 \
    app:app
