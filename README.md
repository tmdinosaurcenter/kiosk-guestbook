# Kiosk Guestbook (html-form Branch)

This branch implements a minimal HTML form-based guestbook for our museum visitor kiosk project. It uses a Python Flask backend with an SQLite database to store visitor entries. The application is containerized with Docker for easy deployment and testing.

## Features
- Visitor Form: Collects visitor name, email, and location.
- Data Storage: Uses SQLite to persist guest entries.
- Dockerized: Easily build and run the application in a Docker container.
- Minimal Viable Product: A simple, extendable starting point for your project.

## Project Structure
```
kiosk-guestbook/
├── app.py               # Main Flask application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration file
└── templates/
    └── index.html       # HTML template for the guestbook form and entries list
```

## Installation and Setup

### Prerequisites
- Git: To clone the repository.
- Python 3.9+: To run the app locally (optional if using Docker).
- Docker: To build and run the container.

#### Checkout the Branch
If the repository is already initialized on the server (on the `main` branch), follow these steps:

1. Navigate to your repository directory:
`cd /path/to/kiosk-guestbook`
2. Fetch the latest branches:

`git fetch origin`
3. Checkout the html-form branch:

`git checkout -b html-form origin/html-form`
#### Running Locally

1. (Optional) Set up a virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```

2. Install the dependencies:
`pip install -r requirements.txt`
3. Start the Flask application:
`python app.py`
4. Open your browser and navigate to <http://localhost:5000> to view the guestbook.

#### Running with Docker

1. Build the Docker Image:

`docker build -t guestbook .`
2. Run the Docker Container:
`docker run -p 5000:5000 guestbook`
3. Open your browser and navigate to <http://localhost:5000>.
### Troubleshooting
If you encounter issues during the Docker build (e.g., hanging during the `pip install` step):
- Use the Host Network:
`docker build --network=host -t guestbook .`
- Clear the Docker Build Cache:
`docker builder prune`
## Future Improvements
- Persistent Storage: Implement Docker volumes or a more robust database for data persistence.
- Enhanced Security: Add input validation, sanitization, and CSRF protection.
- Feature Expansion: Integrate additional museum kiosk features or analytics.

## License
TBD