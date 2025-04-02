# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables (can be overridden by .env)
ENV FLASK_ENV=production

# Expose the port (Gunicorn will run on 8000)
EXPOSE 8000

# Run the app with Gunicorn; use 3 workers (can be tuned via .env)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app", "--workers", "3"]
