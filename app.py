from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re
import logging
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATABASE = 'guestbook.db'

def load_banned_words():
    """Load a set of banned words from a local file.

    Expects 'en.txt' to be in the same directory as this script.
    If the file is missing, a minimal fallback set is used.
    """
    banned_words = set()
    file_path = os.path.join(os.path.dirname(__file__), 'en.txt')
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        banned_words.add(word)
            logger.info("Loaded %d banned words from file.", len(banned_words))
        except Exception as e:
            logger.error("Error reading banned words file: %s", e)
            banned_words = {"fuck", "shit", "damn", "bitch", "asshole", "cunt", "dick", "piss", "crap", "hell"}
    else:
        logger.warning("Banned words file not found. Using fallback minimal list.")
        banned_words = {"fuck", "shit", "damn", "bitch", "asshole", "cunt", "dick", "piss", "crap", "hell"}
    return banned_words

# Load the banned words using the helper function.
BANNED_WORDS = load_banned_words()

def contains_banned_words(text):
    """Check if the provided text contains any banned words."""
    words = text.lower().split()
    for word in words:
        word_clean = word.strip(".,!?;:\"'")
        if word_clean in BANNED_WORDS:
            return True
    return False

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            location TEXT NOT NULL,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        logger.info("Received POST request with form data.")
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        location = request.form.get('location', '').strip()
        comment = request.form.get('comment', '').strip()

        if not (first_name and last_name and location):
            error = "First name, last name, and location are required."
            logger.warning("Validation error: Missing required fields.")
        elif email and not is_valid_email(email):
            error = "Invalid email address."
            logger.warning("Validation error: Invalid email address '%s'.", email)
        elif comment and contains_banned_words(comment):
            error = "Your comment contains inappropriate language. Please revise."
            logger.warning("Validation error: Inappropriate language detected in comment.")

        if error:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('SELECT first_name, location FROM guests ORDER BY id DESC')
            guests = c.fetchall()
            conn.close()
            return render_template('index.html', error=error, guests=guests)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            'INSERT INTO guests (first_name, last_name, email, location, comment) VALUES (?, ?, ?, ?, ?)',
            (first_name, last_name, email, location, comment)
        )
        conn.commit()
        conn.close()
        logger.info("New guest entry added: %s from %s.", first_name, location)
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT first_name, location FROM guests ORDER BY id DESC')
    guests = c.fetchall()
    conn.close()
    logger.info("Rendering guestbook page with %d entries.", len(guests))
    return render_template('index.html', error=error, guests=guests)

if __name__ == '__main__':
    init_db()
    logger.info("Starting Flask app on host 0.0.0.0, port 5000.")
    app.run(host='0.0.0.0', port=5000)
