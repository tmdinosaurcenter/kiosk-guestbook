const express = require('express');
const path = require('path');
// const { google } = require('googleapis'); // only if you're using Google Sheets API

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from the 'public' folder
app.use(express.static(path.join(__dirname, 'public')));

// Example route to serve index.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Example (placeholder) route for approved data
app.get('/api/approved', async (req, res) => {
  // TODO: connect to Google Sheets or n8n to fetch approved entries

  // For now, just return some sample data
  const dummyData = [
    { name: 'Alice', location: 'Paris', comment: 'Loving this exhibit!' },
    { name: 'Bob', location: 'New York', comment: 'Very insightful museum.' }
  ];

  res.json(dummyData);
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
