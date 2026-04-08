from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret123'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ===== DATABASE =====
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            user TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ===== AUTH =====
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)",(user,pw))
            conn.commit()
        except:
            return "User đã tồn tại!"
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        conn = get_db()
        result = conn.execute("SELECT * FROM users WHERE username=? AND password=?",(user,pw)).fetchone()
        if result:
            session['user'] = user
            return redirect('/')
        return "Sai tài khoản!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# ===== HOME =====
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db()
    files = conn.execute("SELECT * FROM files").fetchall()
    return render_template('index.html', files=files, user=session['user'])

# ===== UPLOAD =====
@app.route('/upload', methods=['GET','POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = get_db()
            conn.execute("INSERT INTO files (filename,user) VALUES (?,?)",(filename,session['user']))
            conn.commit()
            return redirect('/')

    return render_template('upload.html')

# ===== DOWNLOAD =====
@app.route('/uploads/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)