from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, Response, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import logging
import os
import re

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
    lower = text.lower()
    # Whole-word check (punctuation-stripped) — catches exact matches
    for word in lower.split():
        if word.strip(".,!?;:\"'") in BANNED_WORDS:
            return True
    # Normalized substring check — catches spacing tricks (f u c k) and
    # embedded forms (fucking). Note: may produce false positives on words
    # that contain a banned word as a substring (e.g. "classic" → "ass").
    normalized = re.sub(r'[^a-z]', '', lower)
    for banned in BANNED_WORDS:
        if banned in normalized:
            return True
    return False

# Each entry is a list of SQL statements for that schema version.
# To add a column or index in the future, append a new list — never modify existing entries.
MIGRATIONS = [
    # v1 — initial schema
    [
        '''CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            location TEXT NOT NULL,
            comment TEXT,
            newsletter_opt_in BOOLEAN DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''',
        'CREATE INDEX IF NOT EXISTS idx_guests_id ON guests (id DESC)',
        'CREATE INDEX IF NOT EXISTS idx_guests_email ON guests (email)',
    ],
    # v2 — user accounts for admin interface (role: 'admin' or 'viewer')
    [
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'viewer'))
        )''',
    ],
]

def migrate_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Bootstrap the version table and seed it at 0 if empty
    c.execute('CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)')
    if c.execute('SELECT COUNT(*) FROM schema_version').fetchone()[0] == 0:
        c.execute('INSERT INTO schema_version VALUES (0)')
        conn.commit()

    current = c.execute('SELECT version FROM schema_version').fetchone()[0]
    pending = MIGRATIONS[current:]

    if not pending:
        logger.info("Database schema is up to date at v%d.", current)
        conn.close()
        return

    for statements in pending:
        current += 1
        logger.info("Applying migration v%d...", current)
        for sql in statements:
            c.execute(sql)
        c.execute('UPDATE schema_version SET version = ?', (current,))
        conn.commit()

    logger.info("Database migrated to v%d.", current)
    conn.close()

def is_valid_email(email):
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

with app.app_context():
    migrate_db()

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

def _authenticate():
    """Returns (username, role) for the current request, or None if unauthenticated.
    Role is 'superadmin', 'admin', or 'viewer'."""
    auth = request.authorization
    if not auth:
        return None
    admin_user = os.environ.get('ADMIN_USER')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if admin_user and auth.username == admin_user and auth.password == admin_password:
        return (auth.username, 'superadmin')
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        row = c.execute(
            'SELECT password_hash, role FROM users WHERE username = ?', (auth.username,)
        ).fetchone()
        conn.close()
        if row and check_password_hash(row[0], auth.password):
            return (auth.username, row[1])
    except sqlite3.Error as e:
        logger.error("Database error during authentication: %s", e)
    return None

def _unauthorized():
    return Response('Authentication required.', 401, {'WWW-Authenticate': 'Basic realm="Admin"'})

def require_any_auth(f):
    """Allows superadmin, admin, and viewer roles."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not os.environ.get('ADMIN_USER') or not os.environ.get('ADMIN_PASSWORD'):
            logger.error("ADMIN_USER and ADMIN_PASSWORD must be set to enable the admin interface.")
            abort(503)
        user = _authenticate()
        if user is None:
            return _unauthorized()
        g.current_user, g.current_role = user
        return f(*args, **kwargs)
    return decorated

def require_superadmin(f):
    """Allows only the bootstrap superadmin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_user = os.environ.get('ADMIN_USER')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_user or not admin_password:
            abort(503)
        auth = request.authorization
        if not auth or auth.username != admin_user or auth.password != admin_password:
            return _unauthorized()
        g.current_user = auth.username
        g.current_role = 'superadmin'
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@require_any_auth
def admin():
    page = request.args.get('page', 1, type=int)
    per_page = 25
    offset = (page - 1) * per_page
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        total = c.execute('SELECT COUNT(*) FROM guests').fetchone()[0]
        c.execute('''
            SELECT id, first_name, last_name, email, location, comment, newsletter_opt_in, timestamp
            FROM guests ORDER BY id DESC LIMIT ? OFFSET ?
        ''', (per_page, offset))
        guests = c.fetchall()
        conn.close()
    except sqlite3.Error as e:
        logger.error("Database error in admin: %s", e)
        guests = []
        total = 0
    total_pages = (total + per_page - 1) // per_page
    return render_template('admin.html', guests=guests, page=page, total_pages=total_pages,
                           total=total, current_role=g.current_role)

@app.route('/admin/delete/<int:entry_id>', methods=['POST'])
@require_any_auth
def admin_delete(entry_id):
    if g.current_role == 'viewer':
        abort(403)
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('DELETE FROM guests WHERE id = ?', (entry_id,))
        conn.commit()
        conn.close()
        logger.info("Admin deleted guest entry id=%d", entry_id)
    except sqlite3.Error as e:
        logger.error("Database error deleting guest %d: %s", entry_id, e)
    return redirect(url_for('admin', page=request.args.get('page', 1)))

@app.route('/admin/logout')
def admin_logout():
    return Response(
        '<p style="font-family:sans-serif">You have been logged out. '
        '<a href="/admin">Log in again</a></p>',
        401,
        {'WWW-Authenticate': 'Basic realm="Admin"', 'Content-Type': 'text/html'}
    )

@app.route('/admin/users')
@require_superadmin
def admin_users():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        users = c.execute('SELECT id, username, role FROM users ORDER BY username').fetchall()
        conn.close()
    except sqlite3.Error as e:
        logger.error("Database error in admin_users: %s", e)
        users = []
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@require_superadmin
def admin_users_add():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', '').strip()
    if not username or not password or role not in ('admin', 'viewer'):
        return redirect(url_for('admin_users'))
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            (username, generate_password_hash(password), role)
        )
        conn.commit()
        conn.close()
        logger.info("Superadmin added user '%s' with role '%s'", username, role)
    except sqlite3.IntegrityError:
        logger.warning("Attempted to add duplicate username '%s'", username)
    except sqlite3.Error as e:
        logger.error("Database error adding user: %s", e)
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@require_superadmin
def admin_users_delete(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        logger.info("Superadmin deleted user id=%d", user_id)
    except sqlite3.Error as e:
        logger.error("Database error deleting user %d: %s", user_id, e)
    return redirect(url_for('admin_users'))

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
    migrate_db()
    logger.info("Starting development server at http://0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000)
