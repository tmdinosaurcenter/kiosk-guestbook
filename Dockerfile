# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (including gettext for envsubst and gosu for privilege dropping)
RUN apt-get update && apt-get install -y gettext gosu && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and template files
COPY . .

# Copy the entrypoint script into the container and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables (can be overridden by .env)
ENV FLASK_ENV=production

# Expose the port (Gunicorn will run on 8000)
EXPOSE 8000

# Create a non-root user. UID/GID match the PID/GID vars in example.env (default 1000).
# Override at build time with: docker build --build-arg UID=1001 --build-arg GID=1001
ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appuser && useradd -u ${UID} -g ${GID} -s /bin/sh -M appuser
RUN chown -R appuser:appuser /app /entrypoint.sh
# Entrypoint runs as root, fixes volume permissions, then drops to appuser via gosu

# Use the entrypoint script as the container's command
CMD ["/entrypoint.sh"]
