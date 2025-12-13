from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

@app.route('/intro')
def intro():
    return render_template('intro.html')

@app.route('/')
def learn():
    return render_template('learn.html')

@app.route('/Login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, firstname, lastname, email 
            FROM users 
            WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            # Save user info in session
            session['user_id'] = user[0]
            session['firstname'] = user[1]
            session['lastname'] = user[2]
            session['email'] = user[3]

            return redirect(url_for('dashboard'))
        else:
            message = "Invalid email or password."

    return render_template('Login.html', message=message)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template(
        'dashboard.html',
        firstname=session['firstname'],
        lastname=session['lastname']
    )

@app.route('/career')
def career():
    return render_template('career.html')

@app.route('/earn')
def earn():
    return render_template('earn.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('INSERT INTO users (firstname, lastname, email, password) VALUES (?, ?, ?, ?)',
                       (firstname, lastname, email, password))

        conn.commit()
        conn.close()

        return render_template('Login.html')

    return render_template('register.html')

# Create database
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firstname TEXT,
        lastname TEXT,
        email TEXT,
        password TEXT
    )
''')
conn.commit()
conn.close()

@app.context_processor
def inject_user():
    return dict(
        firstname=session.get('firstname'),
        lastname=session.get('lastname')
    )

@app.route('/body')
def body():
    return render_template('body.html')
@app.route('/courses')
def courses():
    return render_template('courses.html')

if __name__ == '__main__':
    app.run(debug=True)
