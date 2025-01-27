async function fetchApproved() {
  try {
    const response = await fetch('/api/approved');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching approved data:', error);
    return [];
  }
}

async function updateTicker() {
  const approvedData = await fetchApproved();
  const tickerContent = approvedData
    .map(entry => `${entry.name} (${entry.location}): ${entry.comment}`)
    .join(' – ');

  const tickerElement = document.getElementById('ticker-content');
  tickerElement.textContent = tickerContent;
}

// Fetch on load
updateTicker();

// Refresh every 30 seconds (adjust as needed)
setInterval(updateTicker, 30000);
