# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (including gettext for envsubst)
RUN apt-get update && apt-get install -y gettext && rm -rf /var/lib/apt/lists/*

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

# Use the entrypoint script as the container's command
CMD ["/entrypoint.sh"]
