import os
import sqlite3
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'zip'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('eschool.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'learner',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create courses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            instructor_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES users (id)
        )
    ''')
    
    # Create course_enrollments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS course_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            UNIQUE(user_id, course_id)
        )
    ''')
    
    # Create files table
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT NOT NULL,
            storage_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            course_id TEXT NOT NULL,
            assignment TEXT,
            description TEXT,
            privacy TEXT DEFAULT 'private',
            user_id INTEGER NOT NULL,
            downloads INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            status TEXT DEFAULT 'approved',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create comments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert sample data
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'john'")
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO users (username, password, firstname, lastname, email, role)
            VALUES ('john', 'password123', 'John', 'Doe', 'john@eschool.com', 'learner')
        ''')
        c.execute('''
            INSERT INTO users (username, password, firstname, lastname, email, role)
            VALUES ('jane', 'password123', 'Jane', 'Smith', 'jane@eschool.com', 'learner')
        ''')
        c.execute('''
            INSERT INTO users (username, password, firstname, lastname, email, role)
            VALUES ('bob', 'password123', 'Bob', 'Johnson', 'bob@eschool.com', 'learner')
        ''')
        
        c.execute('''
            INSERT INTO courses (code, name, description)
            VALUES ('math101', 'Mathematics 101', 'Calculus and Algebra'),
                   ('physics201', 'Physics 201', 'Mechanics and Thermodynamics'),
                   ('cs301', 'Computer Science 301', 'Data Structures and Algorithms'),
                   ('english101', 'English Literature 101', 'Classic English Literature')
        ''')
        
        # Enroll sample users in courses
        c.execute("SELECT id FROM users WHERE username = 'john'")
        john_id = c.fetchone()[0]
        
        c.execute("SELECT id FROM courses WHERE code = 'math101'")
        math101_id = c.fetchone()[0]
        c.execute("SELECT id FROM courses WHERE code = 'physics201'")
        physics201_id = c.fetchone()[0]
        
        c.execute('''
            INSERT INTO course_enrollments (user_id, course_id)
            VALUES (?, ?), (?, ?)
        ''', (john_id, math101_id, john_id, physics201_id))
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # In production, use proper authentication
        if username == 'john' and password == 'password123':
            session['user_id'] = 1
            session['username'] = 'john'
            session['firstname'] = 'John'
            session['lastname'] = 'Doe'
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html', 
                         firstname=session.get('firstname'),
                         lastname=session.get('lastname'))

@app.route('/courses')
def courses():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('eschool.db')
    c = conn.cursor()
    
    # Get user's enrolled courses
    c.execute('''
        SELECT c.code, c.name, c.description 
        FROM courses c
        JOIN course_enrollments ce ON c.id = ce.course_id
        WHERE ce.user_id = ?
    ''', (session['user_id'],))
    
    user_courses = []
    for row in c.fetchall():
        course = {
            'code': row[0],
            'name': row[1],
            'description': row[2]
        }
        
        # Get shared files for this course
        c.execute('''
            SELECT f.original_name, f.storage_name, f.file_size, f.file_type,
                   f.description, f.downloads, f.views, f.uploaded_at,
                   u.firstname || ' ' || u.lastname as owner
            FROM files f
            JOIN users u ON f.user_id = u.id
            WHERE f.course_id = ? AND f.privacy = 'class'
            ORDER BY f.uploaded_at DESC
        ''', (course['code'],))
        
        course_files = []
        for file_row in c.fetchall():
            course_files.append({
                'name': file_row[0],
                'storage_name': file_row[1],
                'size': f"{file_row[2] / (1024*1024):.1f} MB",
                'type': file_row[3],
                'description': file_row[4],
                'downloads': file_row[5],
                'views': file_row[6],
                'date': file_row[7],
                'owner': file_row[8]
            })
        
        course['files'] = course_files
        user_courses.append(course)
    
    conn.close()
    
    return render_template('courses.html',
                         courses=user_courses,
                         firstname=session.get('firstname'),
                         lastname=session.get('lastname'))

@app.route('/files')
def files_page():
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('files.html',
                         firstname=session.get('firstname'),
                         lastname=session.get('lastname'))

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    course = request.form.get('course', '')
    assignment = request.form.get('assignment', '')
    description = request.form.get('description', '')
    privacy = request.form.get('privacy', 'private')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Secure the filename and make it unique
        filename = secure_filename(file.filename)
        unique_filename = f"{session['user_id']}_{int(time.time())}_{filename}"
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Get file type
        file_type = filename.split('.')[-1].lower()
        
        # Save to database
        conn = sqlite3.connect('eschool.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO files (original_name, storage_name, file_path, file_size, 
                              file_type, course_id, assignment, description, 
                              privacy, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filename, unique_filename, file_path, file_size, file_type,
              course, assignment, description, privacy, session['user_id']))
        
        file_id = c.lastrowid
        
        conn.commit()
        
        # Get the inserted file record
        c.execute('''
            SELECT f.*, u.firstname || ' ' || u.lastname as owner
            FROM files f
            JOIN users u ON f.user_id = u.id
            WHERE f.id = ?
        ''', (file_id,))
        
        file_record = c.fetchone()
        conn.close()
        
        # Format the response
        response = {
            'success': True,
            'file': {
                'id': file_record[0],
                'name': file_record[1],
                'storage_name': file_record[2],
                'size': f"{file_record[4] / (1024*1024):.1f} MB",
                'type': file_record[5],
                'course': file_record[6],
                'assignment': file_record[7],
                'description': file_record[8],
                'privacy': file_record[9],
                'owner': file_record[16],
                'ownerInitials': f"{session.get('firstname', '')[0]}{session.get('lastname', '')[0]}",
                'downloads': file_record[11],
                'views': file_record[12],
                'date': file_record[14].split()[0] if file_record[14] else datetime.now().strftime('%Y-%m-%d'),
                'status': file_record[13]
            }
        }
        
        return jsonify(response), 200
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/uploads/<filename>')
def get_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get_files')
def get_files():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    file_type = request.args.get('type', 'all')  # all, shared, myfiles
    course_filter = request.args.get('course', '')
    
    conn = sqlite3.connect('eschool.db')
    c = conn.cursor()
    
    query = '''
        SELECT f.*, u.firstname || ' ' || u.lastname as owner
        FROM files f
        JOIN users u ON f.user_id = u.id
        WHERE 1=1
    '''
    
    params = []
    
    if file_type == 'shared':
        query += " AND f.privacy = 'class'"
    elif file_type == 'myfiles':
        query += " AND f.user_id = ?"
        params.append(session['user_id'])
    
    if course_filter:
        query += " AND f.course_id = ?"
        params.append(course_filter)
    
    query += " ORDER BY f.uploaded_at DESC"
    
    c.execute(query, params)
    
    files = []
    for row in c.fetchall():
        files.append({
            'id': row[0],
            'name': row[1],
            'storage_name': row[2],
            'size': f"{row[4] / (1024*1024):.1f} MB",
            'type': row[5],
            'course': row[6],
            'assignment': row[7],
            'description': row[8],
            'privacy': row[9],
            'user_id': row[10],
            'downloads': row[11],
            'views': row[12],
            'status': row[13],
            'date': row[14].split()[0] if row[14] else '',
            'owner': row[16],
            'ownerInitials': f"{row[16].split()[0][0]}{row[16].split()[-1][0] if len(row[16].split()) > 1 else ''}"
        })
    
    conn.close()
    return jsonify(files)

@app.route('/update_file/<int:file_id>', methods=['PUT'])
def update_file(file_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    conn = sqlite3.connect('eschool.db')
    c = conn.cursor()
    
    # Check if user owns the file
    c.execute('SELECT user_id FROM files WHERE id = ?', (file_id,))
    result = c.fetchone()
    
    if not result or result[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Not authorized'}), 403
    
    # Update file
    c.execute('''
        UPDATE files 
        SET original_name = ?, course_id = ?, description = ?, privacy = ?
        WHERE id = ?
    ''', (data['name'], data['course'], data['description'], data['privacy'], file_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect('eschool.db')
    c = conn.cursor()
    
    # Check if user owns the file
    c.execute('SELECT user_id, storage_name FROM files WHERE id = ?', (file_id,))
    result = c.fetchone()
    
    if not result or result[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Not authorized'}), 403
    
    # Delete file from storage
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], result[1])
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass
    
    # Delete from database
    c.execute('DELETE FROM files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)