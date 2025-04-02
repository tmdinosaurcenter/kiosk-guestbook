FROM python:3.9-slim

WORKDIR /app

# Copy and install Python dependencies.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code.
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
