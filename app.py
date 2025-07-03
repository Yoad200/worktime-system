from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

# יצירת טבלאות אם לא קיימות
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="שם המשתמש כבר קיים.")
        conn.close()
        return redirect('/')
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        session['user_id'] = user[0]
        session['username'] = username
        return redirect('/dashboard')
    return render_template("login.html", error="שם משתמש או סיסמה לא נכונים")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('dashboard.html', username=session['username'])

@app.route('/report', methods=['POST', 'GET'])
def report():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO reports (user_id, date, time) VALUES (?, ?, ?)", (session['user_id'], date, time))
        conn.commit()
        conn.close()
        return redirect('/my_summary')
    return render_template('report.html')

@app.route('/my_summary')
def my_summary():
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""
        SELECT date, time
        FROM reports
        WHERE user_id = ?
        ORDER BY date DESC, time DESC
    """, (session['user_id'],))
    records = c.fetchall()
    conn.close()
    return render_template('summary.html', records=records, name=session.get('username'))

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('username') != 'admin':
        return redirect('/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""
        SELECT users.username, reports.date, reports.time
        FROM reports
        JOIN users ON users.id = reports.user_id
        ORDER BY reports.date DESC, reports.time DESC
    """)
    records = c.fetchall()
    conn.close()
    return render_template('admin.html', records=records)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)




