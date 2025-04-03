# Museum Visitor Guestbook

A simple Flask-based guestbook application designed for an internal museum kiosk. This application collects visitor details (first name(s), last name, email, location, and an optional comment) while dynamically revealing the comment field only after the required fields are filled out with at least 3 characters each. The app includes basic input validation, profanity filtering using a custom banned words list, and logging for easier troubleshooting. It uses SQLite for data storage and is containerized with Docker and Docker Compose for easy deployment on an intranet.

![Museum Visitor Guestbook Screenshot](screenshot.png)

## Features

- Dynamic Form Behavior:
The comment field is hidden by default and only revealed when the first name, last name, and location fields each contain at least 3 characters.
-Input Validation:
Ensures required fields (first name, last name, and location) are filled.
- Validates email format (if provided).
Uses a profanity filter loaded from en.txt to prevent inappropriate language in comments.
- Logging:
Logs key events and validation errors to help with debugging and monitoring.
- SQLite Database:
Stores guest entries locally, with persistence ensured by mounting a Docker volume.
- Containerized Deployment:
Uses Docker and Docker Compose to create a production-ready environment with Gunicorn as the WSGI server.

## Project Structure

``` bash
kiosk-guestbook/
├── scripts/
│   └── guestbook_export.py    # Script to export guest entries (e.g., for Mailchimp)
├── static/
│   └── images/
│       └── logo.png           # Logo for display in the application
├── templates/
│   └── index.html             # Main HTML template for the guestbook
├── .env                       # Environment variables for Docker Compose (production settings)
├── app.py                     # Main Flask application code
├── docker-compose.yml         # Docker Compose configuration for container orchestration
├── Dockerfile                 # Default Dockerfile (development or general usage)
├── en.txt                     # Profanity list file (one banned word per line)
├── development.Dockerfile      # Optional Dockerfile optimized for production
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies (Flask, Gunicorn, etc.)
```

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Building and Running the Application

### Build and Start Containers

1. From the project root, run:
`docker-compose up --build -d`
This command will build the Docker image, start the container in detached mode, and mount the persistent volume at `/data` for the SQLite database.

2. Access the Application:
Open a web browser and navigate to `http://<your-server-ip>:8000` (or the port specified in your .env file).

### Deployment with Docker Compose

The `docker-compose.yml` is configured to:

- Build the image from the Dockerfile.
- Expose the service on the specified port.
- Mount a volume (named `guestbook_data`) at `/data` to persist your database.
- Load environment variables from the `.env` file

### Logging and Monitoring

- The application uses Python's built-in logging module.
- Key events (like database initialization, form submissions, and validation errors) are logged.
- Logs can be viewed by running:
`docker-compose logs -f`

### API Access

You can access the API to export contacts by navigating your web browser to `http://<your-server-ip>:8000/guests/api`. Uses a Flask API Endpoint, and can be integrated with on prem automation tools like n8n. 
## Additional Notes

- Intranet-Only Deployment:
This application is designed for internal use only. It is not exposed to the public internet.
- Database Persistence:
The SQLite database is stored in a Docker volume (guestbook_data), ensuring that data persists even if containers are rebuilt.
- Production Considerations:

The app runs with Gunicorn as a production-ready WSGI server. Make sure to adjust worker counts and resource limits as needed based on your server’s specifications.
