from flask import Flask, render_template, request, redirect, url_for
import sqlite3

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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        location = request.form.get('location')
        if first_name and last_name and email and location:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute(
                'INSERT INTO guests (first_name, last_name, email, location) VALUES (?, ?, ?, ?)',
                (first_name, last_name, email, location)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    # Retrieve guest entries to display only first name and location.
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT first_name, location FROM guests ORDER BY id DESC')
    guests = c.fetchall()
    conn.close()
    return render_template('index.html', guests=guests)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
