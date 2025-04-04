#!/bin/sh
# Process index.html.template to create index.html
# Adjust the path if your template is located somewhere else
envsubst < /templates/index.html.template > /templates/index.html

# Start Gunicorn; using an environment variable for workers (default is 3)
exec gunicorn --bind 0.0.0.0:8000 app:app --workers ${WORKERS:-3}
