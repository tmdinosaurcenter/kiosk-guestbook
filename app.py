from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
import sqlite3
import re
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATABASE = os.environ.get('DATABASE_PATH', 'guestbook.db')

def load_banned_words():
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
        logger.warning("Banned words file not found. Using fallback list.")
        banned_words = {"fuck", "shit", "damn", "bitch", "asshole", "cunt", "dick", "piss", "crap", "hell"}
    return banned_words

BANNED_WORDS = load_banned_words()

def contains_banned_words(text):
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
            newsletter_opt_in BOOLEAN DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

@app.before_first_request
def initialize_database():
    init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        logger.info("Received POST request.")
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        location = request.form.get('location', '').strip()
        comment = request.form.get('comment', '').strip()
        newsletter_opt_in = request.form.get('newsletter_opt_in') == 'on'

        if not (first_name and last_name and location):
            error = "First name, last name, and location are required."
            logger.warning("Missing required fields.")
        elif email and not is_valid_email(email):
            error = "Invalid email address."
            logger.warning("Invalid email: %s", email)
        elif comment and contains_banned_words(comment):
            error = "Your comment contains inappropriate language. Please revise."
            logger.warning("Profanity detected in comment.")

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
            '''
            INSERT INTO guests (first_name, last_name, email, location, comment, newsletter_opt_in)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (first_name, last_name, email, location, comment, newsletter_opt_in)
        )
        conn.commit()
        conn.close()
        logger.info("Added guest: %s %s from %s", first_name, last_name, location)
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT first_name, location FROM guests ORDER BY id DESC')
    guests = c.fetchall()
    conn.close()
    logger.info("Rendering index with %d guests.", len(guests))
    return render_template('index.html', error=error, guests=guests)

@app.route('/api/guests', methods=['GET'])
def api_guests():
    api_key = request.headers.get('X-API-Key')
    if api_key != os.environ.get("API_KEY"):
        abort(403)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        SELECT first_name, last_name, email, location, comment, newsletter_opt_in, timestamp
        FROM guests
        WHERE email IS NOT NULL AND email != ''
        ORDER BY id DESC
    ''')
    rows = c.fetchall()
    conn.close()

    guests = [
        {
            "first_name": row[0],
            "last_name": row[1],
            "email": row[2],
            "location": row[3],
            "comment": row[4],
            "newsletter_opt_in": bool(row[5]),
            "timestamp": row[6]
        }
        for row in rows
    ]
    return jsonify(guests)

if __name__ == '__main__':
    init_db()
    logger.info("Starting development server at http://0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000)
