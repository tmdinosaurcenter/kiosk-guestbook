from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re

app = Flask(__name__)
DATABASE = 'guestbook.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            location TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_valid_email(email):
    # A simple regex for basic email validation
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        location = request.form.get('location', '').strip()

        # Basic validation checks
        if not (first_name and last_name and email and location):
            error = "All fields are required."
        elif not is_valid_email(email):
            error = "Invalid email address."

        if error:
            # Retrieve guest entries to display on the page.
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('SELECT first_name, location FROM guests ORDER BY id DESC')
            guests = c.fetchall()
            conn.close()
            return render_template('index.html', error=error, guests=guests)

        # If all validations pass, insert the data into the database.
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            'INSERT INTO guests (first_name, last_name, email, location) VALUES (?, ?, ?, ?)',
            (first_name, last_name, email, location)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    # For GET requests, retrieve guest entries to display.
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT first_name, location FROM guests ORDER BY id DESC')
    guests = c.fetchall()
    conn.close()
    return render_template('index.html', error=error, guests=guests)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
