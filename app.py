from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import re
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
DATABASE = os.environ.get('DATABASE_PATH', 'guestbook.db')
limiter = Limiter(get_remote_address, app=app, default_limits=[])

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
    # TODO: This filter is easily bypassed (spacing, leet-speak, numbers). Consider a more robust NLP-based approach.
    words = text.lower().split()
    for word in words:
        word_clean = word.strip(".,!?;:\"'")
        if word_clean in BANNED_WORDS:
            return True
    return False

def init_db():
    # TODO: No schema versioning — adding columns in the future requires manual DB updates. Consider a migration tool (e.g. Alembic).
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
    c.execute('CREATE INDEX IF NOT EXISTS idx_guests_id ON guests (id DESC)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_guests_email ON guests (email)')
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def is_valid_email(email):
    # TODO: This regex allows edge cases like consecutive dots and leading/trailing hyphens. Consider using the `email-validator` package.
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

with app.app_context():
    init_db()

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
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
            try:
                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                c.execute('SELECT first_name, location FROM guests ORDER BY id DESC LIMIT 100')
                guests = c.fetchall()
                conn.close()
            except sqlite3.Error as e:
                logger.error("Database error loading guests: %s", e)
                guests = []
            return render_template('index.html', error=error, guests=guests)

        try:
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
        except sqlite3.Error as e:
            logger.error("Database error saving guest: %s", e)
            return render_template('index.html',
                                   error="Unable to save your entry. Please try again.",
                                   guests=[])
        logger.info("Added guest: %s %s from %s", first_name, last_name, location)
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT first_name, location FROM guests ORDER BY id DESC LIMIT 100')
        guests = c.fetchall()
        conn.close()
    except sqlite3.Error as e:
        logger.error("Database error loading guests: %s", e)
        guests = []
    logger.info("Rendering index with %d guests.", len(guests))
    return render_template('index.html', error=error, guests=guests)

@app.route('/api/guests', methods=['GET'])
def api_guests():
    api_key = request.headers.get('X-API-Key')
    if api_key != os.environ.get("API_KEY"):
        abort(403)

    try:
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
    except sqlite3.Error as e:
        logger.error("Database error in api_guests: %s", e)
        return jsonify({"error": "Database unavailable"}), 503

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
