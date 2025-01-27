This is a simple kiosk landing page that embeds a Google Form and displays approved submissions on a scrolling ticker.

Features
Embeds an existing Google Form in an iframe
Fetches approved entries (Name, Location, Comment) from an API endpoint
Displays approved entries in a scrolling ticker at the bottom of the page
Getting Started
Install Node.js if not using Docker.
Clone this repo and change to the project folder.
Install dependencies:
` npm install `

Run locally:
` node app.js `

Or:

` npm start `

Then open http://localhost:3000 in your browser.

Running in Docker
Build the image:
` docker build -t museum-kiosk . `

Run a container:
` docker run -p 3000:3000 museum-kiosk `

Then open http://localhost:3000 (or the server’s IP) in your browser.

Configuration
Google Sheets API credentials: Place them as credentials.json (this file should remain uncommitted).
Adjust environment variables or code as needed for your specific form and sheet.
License
MIT License. See LICENSE for details.