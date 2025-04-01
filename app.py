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
            name TEXT NOT NULL,
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
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        if name and email and location:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('INSERT INTO guests (name, email, location) VALUES (?, ?, ?)',
                      (name, email, location))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    # Retrieve guest entries to display on the page.
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT name, email, location, timestamp FROM guests ORDER BY id DESC')
    guests = c.fetchall()
    conn.close()
    return render_template('index.html', guests=guests)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
