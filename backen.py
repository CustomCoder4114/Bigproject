from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash, Response
import sqlite3
import os
import uuid
import json
import random
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
import math

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'mov', 'avi', 'mkv', 
    'webm', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'zip', 'rar', '7z', 
    'py', 'js', 'html', 'css', 'java', 'c', 'cpp', 'php', 'sql', 'json', 'xml',
    'md', 'rtf', 'odt', 'epub', 'key', 'odp', 'ods', 'csv'
}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB max file size
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks

# ============ QUOTES ============
QUOTES = [
    {"text": "Success is not the key to happiness. Happiness is the key to success. If you love what you are doing, you will be successful.", "author": "Albert Schweitzer"},
    {"text": "Education is the most powerful weapon which you can use to change the world.", "author": "Nelson Mandela"},
    {"text": "An investment in knowledge pays the best interest.", "author": "Benjamin Franklin"},
    {"text": "One child, one teacher, one book, one pen can change the world.", "author": "Malala Yousafzai"},
    {"text": "The roots of education are bitter, but the fruit is sweet.", "author": "Aristotle"},
    {"text": "Every expert was once a beginner. Keep learning, keep growing.", "author": "Anonymous"},
    {"text": "The beautiful thing about learning is that nobody can take it away from you.", "author": "B.B. King"},
    {"text": "Learning never exhausts the mind.", "author": "Leonardo da Vinci"},
    {"text": "Live as if you were to die tomorrow. Learn as if you were to live forever.", "author": "Mahatma Gandhi"},
    {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
    {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
    {"text": "It does not matter how slowly you go as long as you do not stop.", "author": "Confucius"},
    {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
    {"text": "Strive not to be a success, but rather to be of value.", "author": "Albert Einstein"},
    {"text": "The only person you are destined to become is the person you decide to be.", "author": "Ralph Waldo Emerson"},
    {"text": "Everything you've ever wanted is sitting on the other side of fear.", "author": "George Addair"},
    {"text": "Success usually comes to those who are too busy to be looking for it.", "author": "Henry David Thoreau"},
    {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
    {"text": "Don't watch the clock; do what it does. Keep going.", "author": "Sam Levenson"},
    {"text": "The only impossible journey is the one you never begin.", "author": "Tony Robbins"},
    {"text": "Your limitation—it's only your imagination.", "author": "Anonymous"},
    {"text": "Push yourself, because no one else is going to do it for you.", "author": "Anonymous"},
    {"text": "Great things never come from comfort zones.", "author": "Anonymous"},
    {"text": "Dream it. Wish it. Do it.", "author": "Anonymous"},
    {"text": "Success doesn't just find you. You have to go out and get it.", "author": "Anonymous"},
    {"text": "The harder you work for something, the greater you'll feel when you achieve it.", "author": "Anonymous"},
    {"text": "Dream bigger. Do bigger.", "author": "Anonymous"},
    {"text": "Don't stop when you're tired. Stop when you're done.", "author": "Anonymous"},
    {"text": "Wake up with determination. Go to bed with satisfaction.", "author": "Anonymous"},
    {"text": "Do something today that your future self will thank you for.", "author": "Anonymous"},
    {"text": "Little things make big days.", "author": "Anonymous"},
    {"text": "It's going to be hard, but hard does not mean impossible.", "author": "Anonymous"},
    {"text": "The best time to start was yesterday. The next best time is now.", "author": "Anonymous"},
    {"text": "You don't have to be great to start, but you have to start to be great.", "author": "Zig Ziglar"},
    {"text": "The expert in anything was once a beginner.", "author": "Helen Hayes"},
    {"text": "The only source of knowledge is experience.", "author": "Albert Einstein"},
    {"text": "Tell me and I forget. Teach me and I remember. Involve me and I learn.", "author": "Benjamin Franklin"},
    {"text": "Knowledge is power.", "author": "Francis Bacon"},
    {"text": "Learning is a treasure that will follow its owner everywhere.", "author": "Chinese Proverb"},
    {"text": "The capacity to learn is a gift; the ability to learn is a skill; the willingness to learn is a choice.", "author": "Brian Herbert"},
    {"text": "Education is not preparation for life; education is life itself.", "author": "John Dewey"},
    {"text": "The beautiful thing about learning is that no one can take it away from you.", "author": "B.B. King"},
    {"text": "Change is the end result of all true learning.", "author": "Leo Buscaglia"},
    {"text": "Wisdom is not a product of schooling but of the lifelong attempt to acquire it.", "author": "Albert Einstein"},
    {"text": "The mind is not a vessel to be filled, but a fire to be kindled.", "author": "Plutarch"},
    {"text": "Education is the passport to the future, for tomorrow belongs to those who prepare for it today.", "author": "Malcolm X"},
    {"text": "Learning never stops, it just changes direction.", "author": "Anonymous"},
    {"text": "The more that you read, the more things you will know. The more that you learn, the more places you'll go.", "author": "Dr. Seuss"},
    {"text": "You are never too old to set another goal or to dream a new dream.", "author": "C.S. Lewis"},
    {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
    {"text": "The only limit to our realization of tomorrow is our doubts of today.", "author": "Franklin D. Roosevelt"},
    {"text": "It always seems impossible until it's done.", "author": "Nelson Mandela"},
]

def get_random_quote():
    """Get a random quote - changes on every page load"""
    return random.choice(QUOTES)

def get_daily_quote():
    """Get a quote based on the day of the year - changes daily"""
    today = datetime.now()
    day_of_year = today.timetuple().tm_yday
    return QUOTES[day_of_year % len(QUOTES)]

def get_user_quote(user_email):
    """
    Get a quote based on user's email hash - consistent per user
    Changes only when the user logs in again
    """
    hash_value = int(hashlib.md5(user_email.encode()).hexdigest(), 16)
    return QUOTES[hash_value % len(QUOTES)]

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'temp'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'avatars'), exist_ok=True)

# Allowed file extensions for upload
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Get file type category
def get_file_category(filename):
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v', 'mpg', 'mpeg']:
        return 'video'
    elif ext in ['mp3', 'wav', 'aac', 'flac', 'm4a', 'wma', 'ogg']:
        return 'audio'
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'bmp', 'tiff', 'ico', 'webp']:
        return 'image'
    elif ext == 'pdf':
        return 'pdf'
    elif ext in ['doc', 'docx', 'txt', 'rtf', 'odt', 'epub', 'md']:
        return 'doc'
    elif ext in ['ppt', 'pptx', 'key', 'odp']:
        return 'presentation'
    elif ext in ['xls', 'xlsx', 'csv', 'ods']:
        return 'spreadsheet'
    elif ext in ['js', 'html', 'css', 'py', 'java', 'c', 'cpp', 'php', 'sql', 'json', 'xml', 'yml', 'yaml', 'sh', 'bat']:
        return 'code'
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']:
        return 'zip'
    else:
        return 'other'

# Get file icon
def get_file_icon(file_category):
    icons = {
        'video': 'fa-video',
        'audio': 'fa-music',
        'image': 'fa-image',
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'presentation': 'fa-file-powerpoint',
        'spreadsheet': 'fa-file-excel',
        'code': 'fa-file-code',
        'zip': 'fa-file-archive',
        'other': 'fa-file'
    }
    return icons.get(file_category, 'fa-file')

# Get thumbnail URL
def get_thumbnail_url(file_category, course='general'):
    thumbnails = {
        'mathematics': 'https://images.unsplash.com/photo-1509228468518-180dd4864904?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'science': 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'programming': 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'business': 'https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'arts': 'https://images.unsplash.com/photo-1545239351-ef35f43d514b?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'languages': 'https://images.unsplash.com/photo-1516321497487-e288fb19713f?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'projects': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'assignments': 'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80',
        'general': 'https://images.unsplash.com/photo-1551989137-294a2c6a2c2b?ixlib=rb-4.0.3&auto=format&fit=crop&w=300&h=169&q=80'
    }
    
    if file_category == 'image':
        return 'https://images.unsplash.com/photo-1579546929662-711aa81148cf?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&h=150&q=80'
    elif file_category == 'pdf':
        return 'https://images.unsplash.com/photo-1588666309990-d68f08e3d4c6?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&h=150&q=80'
    elif file_category == 'doc':
        return 'https://images.unsplash.com/photo-1586281380349-632531db7ed4?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&h=150&q=80'
    elif file_category == 'code':
        return 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&h=150&q=80'
    else:
        return thumbnails.get(course, thumbnails['general'])

# SQLite's CURRENT_TIMESTAMP stores naive UTC values like "2026-08-02 10:00:00"
# with no timezone marker. If sent to the browser as-is, `new Date(...)`
# interprets it as LOCAL time instead of UTC, throwing every displayed time
# off by the viewer's UTC offset. Tag it explicitly as UTC before returning it.
def to_iso_utc(sqlite_timestamp):
    if not sqlite_timestamp:
        return sqlite_timestamp
    return sqlite_timestamp.replace(' ', 'T') + 'Z'

# Initialize database tables
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Users table (already exists)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT,
            lastname TEXT,
            email TEXT,
            password TEXT
        )
    ''')
    
    # Resources table for storing file metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            resource_type TEXT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            file_category TEXT,
            file_extension TEXT,
            privacy TEXT DEFAULT 'public',
            difficulty TEXT DEFAULT 'beginner',
            views INTEGER DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            featured INTEGER DEFAULT 0,
            duration TEXT,
            pages INTEGER DEFAULT 0,
            thumbnail_url TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Messages table for real, persisted direct messages between users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')

    # Add an avatar column to the existing users table if it isn't there
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN avatar_filename TEXT')
    except sqlite3.OperationalError:
        pass  # column already exists

    # Add a role column so we can tell admins apart from regular users.
    # Existing rows (and any inserted without specifying a role) default
    # to 'student', so nothing currently in the DB accidentally becomes admin.
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
    except sqlite3.OperationalError:
        pass  # column already exists
    
    conn.commit()
    conn.close()

# Call init_db to create tables
init_db()

# ============ EXISTING ROUTES ===============

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
            SELECT id, firstname, lastname, email, role
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
            # Older rows created before the role column existed will read
            # as None here, so treat anything falsy as a regular student.
            session['role'] = user[4] or 'student'
            
            # Store a quote for this user session
            # Option 1: Random quote (changes every page load)
            quote = get_random_quote()
            # Option 2: User-based quote (changes only when user logs in again)
            # quote = get_user_quote(user[3])
            # Option 3: Daily quote (same for everyone all day)
            # quote = get_daily_quote()
            
            session['quote_text'] = quote['text']
            session['quote_author'] = quote['author']

            # Admins land on the admin dashboard, everyone else on the
            # regular student dashboard.
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            message = "Invalid email or password."

    return render_template('Login.html', message=message)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Keep admins on their own dashboard even if they navigate here directly
    # (e.g. via a bookmark or by typing the URL).
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # If quote is not in session (e.g., user directly accessed dashboard without login),
    # set a default quote
    if 'quote_text' not in session:
        quote = get_random_quote()
        session['quote_text'] = quote['text']
        session['quote_author'] = quote['author']

    return render_template(
        'dashboard.html',
        firstname=session['firstname'],
        lastname=session['lastname'],
        quote_text=session.get('quote_text'),
        quote_author=session.get('quote_author')
    )

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Non-admins who somehow land here (typed URL, stale bookmark, etc.)
    # get sent back to the regular dashboard instead of seeing admin data.
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    if 'quote_text' not in session:
        quote = get_random_quote()
        session['quote_text'] = quote['text']
        session['quote_author'] = quote['author']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    total_admins = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resources")
    total_resources = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, firstname, lastname, email, role
        FROM users
        ORDER BY id DESC
        LIMIT 10
    """)
    recent_users = cursor.fetchall()

    conn.close()

    return render_template(
        'admin_dashboard.html',
        firstname=session['firstname'],
        lastname=session['lastname'],
        quote_text=session.get('quote_text'),
        quote_author=session.get('quote_author'),
        total_users=total_users,
        total_admins=total_admins,
        total_resources=total_resources,
        recent_users=recent_users
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

        # Registrations always come in as regular students. Admin accounts
        # are created separately (see create_admin.py) - never through
        # this public-facing form.
        cursor.execute('''
            INSERT INTO users (firstname, lastname, email, password, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (firstname, lastname, email, password, 'student'))

        conn.commit()
        conn.close()

        return render_template('Login.html')

    return render_template('register.html')

@app.context_processor
def inject_user():
    avatar_url = None
    if 'user_id' in session:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT avatar_filename FROM users WHERE id = ?', (session['user_id'],))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            avatar_url = f"/static/uploads/avatars/{session['user_id']}/{row[0]}"

    return dict(
        firstname=session.get('firstname'),
        lastname=session.get('lastname'),
        user_id=session.get('user_id'),
        role=session.get('role'),
        avatar_url=avatar_url,
        quote_text=session.get('quote_text'),
        quote_author=session.get('quote_author')
    )

@app.route('/body')
def body():
    return render_template('body.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

@app.route('/careerD')
def careerD():
    return render_template('careerD.html')

@app.route('/progres')
def progres():
    return render_template('progres.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('settings.html')

@app.route('/strategies')
def strategies():
    return render_template('strategies.html')

@app.route('/skills')
def skills():
    return render_template('skills.html')

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('messages.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============ MESSAGING: USER SEARCH ============

@app.route('/messages/search_users', methods=['GET'])
def search_users():
    """Search existing accounts by name for the messages page.
    Excludes the logged-in user and returns a small JSON list the
    frontend can render directly."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Search first name / last name / full name, exclude yourself
    like_term = f'%{q}%'
    cursor.execute('''
        SELECT id, firstname, lastname
        FROM users
        WHERE id != ?
          AND (
              firstname LIKE ?
              OR lastname LIKE ?
              OR (firstname || ' ' || lastname) LIKE ?
          )
        ORDER BY firstname, lastname
        LIMIT 20
    ''', (session['user_id'], like_term, like_term, like_term))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        user_id, firstname, lastname = row
        firstname = (firstname or '').strip()
        lastname = (lastname or '').strip()
        full_name = f"{firstname} {lastname}".strip()

        if not full_name:
            continue

        initial = (firstname[:1] or lastname[:1]).upper()

        results.append({
            'id': user_id,
            'name': full_name,
            'avatar': initial,
            'online': False,
            'lastSeen': ''
        })

    return jsonify(results)


@app.route('/messages/send', methods=['POST'])
def send_message():
    """Send a message to a specific user and persist it."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    data = request.get_json(silent=True) or {}
    receiver_id = data.get('receiver_id')
    text = (data.get('text') or '').strip()

    if not receiver_id or not text:
        return jsonify({'success': False, 'message': 'receiver_id and text are required'}), 400

    sender_id = session['user_id']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM users WHERE id = ?', (receiver_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Recipient not found'}), 404

    cursor.execute('''
        INSERT INTO messages (sender_id, receiver_id, text, is_read)
        VALUES (?, ?, ?, 0)
    ''', (sender_id, receiver_id, text))
    conn.commit()

    message_id = cursor.lastrowid
    cursor.execute('SELECT id, sender_id, receiver_id, text, timestamp, is_read FROM messages WHERE id = ?', (message_id,))
    row = cursor.fetchone()
    conn.close()

    message = {
        'id': row[0],
        'sender_id': row[1],
        'receiver_id': row[2],
        'text': row[3],
        'timestamp': to_iso_utc(row[4]),
        'read': bool(row[5])
    }

    return jsonify({'success': True, 'message': message})


@app.route('/messages/conversation/<int:other_user_id>', methods=['GET'])
def get_conversation(other_user_id):
    """Return the full message thread between the logged-in user and
    another specific user, and mark any unread messages from them as read."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    my_id = session['user_id']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, sender_id, receiver_id, text, timestamp, is_read
        FROM messages
        WHERE (sender_id = ? AND receiver_id = ?)
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC, id ASC
    ''', (my_id, other_user_id, other_user_id, my_id))

    rows = cursor.fetchall()

    cursor.execute('''
        UPDATE messages SET is_read = 1
        WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
    ''', (other_user_id, my_id))
    conn.commit()
    conn.close()

    thread = [{
        'id': row[0],
        'sender_id': row[1],
        'receiver_id': row[2],
        'text': row[3],
        'timestamp': to_iso_utc(row[4]),
        'read': bool(row[5])
    } for row in rows]

    return jsonify(thread)


@app.route('/messages/conversations', methods=['GET'])
def list_conversations():
    """Return every account the logged-in user has exchanged messages
    with, each with the other user's name/avatar, the last message
    preview, and how many messages from them are unread."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    my_id = session['user_id']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT other_id FROM (
            SELECT receiver_id AS other_id FROM messages WHERE sender_id = ?
            UNION
            SELECT sender_id AS other_id FROM messages WHERE receiver_id = ?
        )
    ''', (my_id, my_id))
    other_ids = [row[0] for row in cursor.fetchall()]

    conversations = []
    for other_id in other_ids:
        cursor.execute('SELECT firstname, lastname FROM users WHERE id = ?', (other_id,))
        user_row = cursor.fetchone()
        if not user_row:
            continue

        firstname = (user_row[0] or '').strip()
        lastname = (user_row[1] or '').strip()
        full_name = f"{firstname} {lastname}".strip()
        if not full_name:
            continue
        initial = (firstname[:1] or lastname[:1]).upper()

        cursor.execute('''
            SELECT sender_id, text, timestamp
            FROM messages
            WHERE (sender_id = ? AND receiver_id = ?)
               OR (sender_id = ? AND receiver_id = ?)
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
        ''', (my_id, other_id, other_id, my_id))
        last_row = cursor.fetchone()

        last_message = None
        last_timestamp = None
        if last_row:
            prefix = 'You: ' if last_row[0] == my_id else ''
            last_message = f"{prefix}{last_row[1]}"
            last_timestamp = last_row[2]

        cursor.execute('''
            SELECT COUNT(*) FROM messages
            WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
        ''', (other_id, my_id))
        unread = cursor.fetchone()[0]

        conversations.append({
            'id': other_id,
            'name': full_name,
            'avatar': initial,
            'online': False,
            'lastSeen': '',
            'lastMessage': last_message,
            'lastTimestamp': last_timestamp,
            'unread': unread
        })

    conn.close()

    conversations.sort(key=lambda c: c['lastTimestamp'] or '', reverse=True)

    for c in conversations:
        c['lastTimestamp'] = to_iso_utc(c['lastTimestamp'])

    return jsonify(conversations)

# ============ UPLOAD ROUTES ============

@app.route('/api/settings/upload-photo', methods=['POST'])
def upload_profile_photo():
    """Upload/replace the logged-in user's profile photo and persist it."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    if 'photo' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    image_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in image_exts:
        return jsonify({'success': False, 'message': 'Please upload a JPG, PNG, GIF, or WEBP image'}), 400

    user_id = session['user_id']
    user_dir = os.path.join(UPLOAD_FOLDER, 'avatars', str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT avatar_filename FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if row and row[0]:
        old_path = os.path.join(user_dir, row[0])
        if os.path.exists(old_path):
            os.remove(old_path)

    new_filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(user_dir, new_filename))

    cursor.execute('UPDATE users SET avatar_filename = ? WHERE id = ?', (new_filename, user_id))
    conn.commit()
    conn.close()

    avatar_url = f"/static/uploads/avatars/{user_id}/{new_filename}"
    return jsonify({'success': True, 'avatar_url': avatar_url})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('upload.html',
                         firstname=session['firstname'],
                         lastname=session['lastname'],
                         user_id=session['user_id'])

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle single file upload"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'File type not allowed'}), 400
        
        title = request.form.get('title', file.filename)
        description = request.form.get('description', '')
        category = request.form.get('category', 'general')
        resource_type = request.form.get('resourceType', 'document')
        difficulty = request.form.get('difficulty', 'beginner')
        privacy = request.form.get('privacy', 'public')
        
        user_id = session['user_id']
        firstname = session['firstname']
        lastname = session['lastname']
        
        user_dir = os.path.join(UPLOAD_FOLDER, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(user_dir, unique_filename)
        
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        file_category = get_file_category(original_filename)
        thumbnail_url = get_thumbnail_url(file_category, category)
        
        duration = None
        if file_category == 'video':
            duration = '15:30'
        
        pages = 0
        if file_category in ['pdf', 'doc', 'presentation']:
            pages = 15
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO resources 
            (user_id, title, description, category, resource_type, file_name, file_path, 
             file_size, file_category, file_extension, privacy, difficulty, thumbnail_url,
             duration, pages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, title, description, category, resource_type, unique_filename,
            file_path, file_size, file_category, file_extension, privacy, difficulty,
            thumbnail_url, duration, pages
        ))
        
        resource_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute('''
            SELECT r.*, u.firstname, u.lastname 
            FROM resources r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        ''', (resource_id,))
        
        resource_row = cursor.fetchone()
        conn.close()
        
        if resource_row:
            resource = {
                'id': resource_row[0],
                'user_id': resource_row[1],
                'title': resource_row[2],
                'description': resource_row[3],
                'category': resource_row[4],
                'type': resource_row[5],
                'file_name': resource_row[6],
                'file_path': resource_row[7],
                'file_size': resource_row[8],
                'file_category': resource_row[9],
                'file_extension': resource_row[10],
                'privacy': resource_row[11],
                'difficulty': resource_row[12],
                'views': resource_row[13],
                'downloads': resource_row[14],
                'likes': resource_row[15],
                'featured': resource_row[16],
                'duration': resource_row[17],
                'pages': resource_row[18],
                'thumbnail_url': resource_row[19],
                'upload_date': resource_row[20],
                'author': f"{resource_row[21]} {resource_row[22]}" if resource_row[21] and resource_row[22] else 'Anonymous',
                'author_initials': f"{resource_row[21][0]}{resource_row[22][0]}" if resource_row[21] and resource_row[22] else 'AU',
                'file_url': f"/uploads/{user_id}/{resource_row[6]}",
                'is_large_file': file_size > 10 * 1024 * 1024
            }
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'resource': resource
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save resource to database'}), 500
            
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/uploads/<user_id>/<filename>')
def serve_file(user_id, filename):
    """Serve uploaded files"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, user_id, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        file_size = os.path.getsize(file_path)
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        video_exts = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpg', 'mpeg', 'wmv', 'flv']
        audio_exts = ['mp3', 'wav', 'aac', 'flac', 'm4a', 'wma', 'ogg']
        image_exts = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'ico']
        inline_exts = ['pdf', 'txt', 'md', 'json', 'xml', 'csv', 'html', 'css', 'js']
        
        mime_types = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'ogg': 'video/ogg',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'mkv': 'video/x-matroska',
            'wmv': 'video/x-ms-wmv',
            'flv': 'video/x-flv',
            'm4v': 'video/x-m4v',
            'mpg': 'video/mpeg',
            'mpeg': 'video/mpeg',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'flac': 'audio/flac',
            'aac': 'audio/aac',
            'm4a': 'audio/mp4',
            'wma': 'audio/x-ms-wma',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'tiff': 'image/tiff',
            'ico': 'image/x-icon',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'rtf': 'application/rtf',
            'odt': 'application/vnd.oasis.opendocument.text',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'ods': 'application/vnd.oasis.opendocument.spreadsheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'odp': 'application/vnd.oasis.opendocument.presentation',
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed',
            '7z': 'application/x-7z-compressed',
            'tar': 'application/x-tar',
            'gz': 'application/gzip',
            'js': 'application/javascript',
            'html': 'text/html',
            'css': 'text/css',
            'py': 'text/x-python',
            'java': 'text/x-java-source',
            'c': 'text/x-c',
            'cpp': 'text/x-c++',
            'php': 'text/x-php',
            'sql': 'application/sql',
            'json': 'application/json',
            'xml': 'application/xml',
            'yml': 'text/yaml',
            'yaml': 'text/yaml',
            'md': 'text/markdown'
        }
        
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        is_video = file_ext in video_exts
        is_audio = file_ext in audio_exts
        is_image = file_ext in image_exts
        is_media = is_video or is_audio
        
        range_header = request.headers.get('Range')
        
        if is_media and range_header:
            range_header = range_header.strip().replace('bytes=', '')
            byte_ranges = range_header.split('-')
            
            start_byte = 0
            end_byte = file_size - 1
            
            if byte_ranges[0]:
                start_byte = int(byte_ranges[0])
            if byte_ranges[1]:
                end_byte = int(byte_ranges[1])
            else:
                end_byte = file_size - 1
            
            if start_byte >= file_size:
                start_byte = 0
            if end_byte >= file_size:
                end_byte = file_size - 1
            if start_byte > end_byte:
                start_byte, end_byte = end_byte, start_byte
            
            length = end_byte - start_byte + 1
            
            def generate():
                with open(file_path, 'rb') as f:
                    f.seek(start_byte)
                    remaining = length
                    while remaining > 0:
                        chunk_size = min(4096, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                        remaining -= len(chunk)
            
            resp = Response(
                generate(),
                206,
                mimetype=mime_type,
                direct_passthrough=True
            )
            
            resp.headers.add('Content-Range', f'bytes {start_byte}-{end_byte}/{file_size}')
            resp.headers.add('Accept-Ranges', 'bytes')
            resp.headers.add('Content-Length', str(length))
            resp.headers.add('Cache-Control', 'no-cache')
            
            return resp
        
        if is_media:
            response = send_from_directory(
                os.path.join(UPLOAD_FOLDER, user_id),
                filename,
                mimetype=mime_type,
                as_attachment=False
            )
            response.headers.add('Accept-Ranges', 'bytes')
            response.headers.add('Cache-Control', 'public, max-age=31536000')
            return response
        
        if is_image:
            return send_from_directory(
                os.path.join(UPLOAD_FOLDER, user_id),
                filename,
                mimetype=mime_type
            )
        
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT privacy, user_id FROM resources 
            WHERE file_name = ? 
            LIMIT 1
        ''', (filename,))
        
        file_info = cursor.fetchone()
        conn.close()
        
        if file_info:
            privacy, owner_id = file_info
            if privacy == 'public' or str(session['user_id']) == str(owner_id):
                force_download = file_ext not in inline_exts
                return send_from_directory(
                    os.path.join(UPLOAD_FOLDER, user_id),
                    filename,
                    as_attachment=force_download,
                    mimetype=mime_type
                )
        
        return jsonify({'success': False, 'message': 'Access denied'}), 403
        
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Get all resources with filters"""
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        sort_by = request.args.get('sort', 'newest')
        file_type = request.args.get('type', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        query = '''
            SELECT r.*, u.firstname, u.lastname 
            FROM resources r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if category:
            query += ' AND r.category = ?'
            params.append(category)
        
        if file_type:
            if file_type == 'videos':
                query += ' AND r.file_category = "video"'
            elif file_type == 'documents':
                query += ' AND r.file_category IN ("pdf", "doc", "presentation", "spreadsheet", "code")'
            elif file_type == 'images':
                query += ' AND r.file_category = "image"'
            elif file_type == 'audio':
                query += ' AND r.file_category = "audio"'
            elif file_type == 'other':
                query += ' AND r.file_category = "other"'
        
        if search:
            query += ' AND (r.title LIKE ? OR r.description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if sort_by == 'newest':
            query += ' ORDER BY r.upload_date DESC'
        elif sort_by == 'oldest':
            query += ' ORDER BY r.upload_date ASC'
        elif sort_by == 'popular':
            query += ' ORDER BY r.views DESC'
        elif sort_by == 'largest':
            query += ' ORDER BY r.file_size DESC'
        elif sort_by == 'smallest':
            query += ' ORDER BY r.file_size ASC'
        
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        resources_rows = cursor.fetchall()
        
        count_query = '''
            SELECT COUNT(*) FROM resources r WHERE 1=1
        '''
        count_params = []
        
        if category:
            count_query += ' AND r.category = ?'
            count_params.append(category)
        
        if search:
            count_query += ' AND (r.title LIKE ? OR r.description LIKE ?)'
            count_params.extend([f'%{search}%', f'%{search}%'])
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        resources = []
        for row in resources_rows:
            file_url = f"/uploads/{row[1]}/{row[6]}" if row[6] else ''
            
            resource = {
                'id': row[0],
                'user_id': row[1],
                'title': row[2],
                'description': row[3],
                'category': row[4],
                'type': row[5],
                'file_name': row[6],
                'file_path': row[7],
                'file_size': row[8],
                'file_category': row[9],
                'file_extension': row[10],
                'privacy': row[11],
                'difficulty': row[12],
                'views': row[13],
                'downloads': row[14],
                'likes': row[15],
                'featured': row[16],
                'duration': row[17],
                'pages': row[18],
                'thumbnail_url': row[19],
                'upload_date': row[20],
                'author': f"{row[21]} {row[22]}" if row[21] and row[22] else 'Anonymous',
                'author_initials': f"{row[21][0]}{row[22][0]}" if row[21] and row[22] else 'AU',
                'file_url': file_url,
                'is_large_file': row[8] > 10 * 1024 * 1024 if row[8] else False
            }
            resources.append(resource)
        
        return jsonify({
            'success': True,
            'resources': resources,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        print(f"Error getting resources: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    """Get a specific resource by ID"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.firstname, u.lastname 
            FROM resources r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        ''', (resource_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'message': 'Resource not found'}), 404
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE resources SET views = views + 1 WHERE id = ?', (resource_id,))
        conn.commit()
        conn.close()
        
        file_url = f"/uploads/{row[1]}/{row[6]}" if row[6] else ''
        
        resource = {
            'id': row[0],
            'user_id': row[1],
            'title': row[2],
            'description': row[3],
            'category': row[4],
            'type': row[5],
            'file_name': row[6],
            'file_path': row[7],
            'file_size': row[8],
            'file_category': row[9],
            'file_extension': row[10],
            'privacy': row[11],
            'difficulty': row[12],
            'views': row[13] + 1,
            'downloads': row[14],
            'likes': row[15],
            'featured': row[16],
            'duration': row[17],
            'pages': row[18],
            'thumbnail_url': row[19],
            'upload_date': row[20],
            'author': f"{row[21]} {row[22]}" if row[21] and row[22] else 'Anonymous',
            'author_initials': f"{row[21][0]}{row[22][0]}" if row[21] and row[22] else 'AU',
            'file_url': file_url,
            'is_large_file': row[8] > 10 * 1024 * 1024 if row[8] else False
        }
        
        return jsonify({
            'success': True,
            'resource': resource
        })
        
    except Exception as e:
        print(f"Error getting resource: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resources/user/<int:user_id>', methods=['GET'])
def get_user_resources(user_id):
    """Get resources for a specific user"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.firstname, u.lastname 
            FROM resources r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.user_id = ?
            ORDER BY r.upload_date DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        resources = []
        for row in rows:
            file_url = f"/uploads/{row[1]}/{row[6]}" if row[6] else ''
            
            resource = {
                'id': row[0],
                'user_id': row[1],
                'title': row[2],
                'description': row[3],
                'category': row[4],
                'type': row[5],
                'file_name': row[6],
                'file_path': row[7],
                'file_size': row[8],
                'file_category': row[9],
                'file_extension': row[10],
                'privacy': row[11],
                'difficulty': row[12],
                'views': row[13],
                'downloads': row[14],
                'likes': row[15],
                'featured': row[16],
                'duration': row[17],
                'pages': row[18],
                'thumbnail_url': row[19],
                'upload_date': row[20],
                'author': f"{row[21]} {row[22]}" if row[21] and row[22] else 'Anonymous',
                'author_initials': f"{row[21][0]}{row[22][0]}" if row[21] and row[22] else 'AU',
                'file_url': file_url,
                'is_large_file': row[8] > 10 * 1024 * 1024 if row[8] else False
            }
            resources.append(resource)
        
        return jsonify({
            'success': True,
            'resources': resources,
            'total': len(resources)
        })
        
    except Exception as e:
        print(f"Error getting user resources: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resources/<int:resource_id>/download', methods=['GET'])
def download_resource(resource_id):
    """Download a resource file"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.firstname, u.lastname 
            FROM resources r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        ''', (resource_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': 'Resource not found'}), 404
        
        cursor.execute('UPDATE resources SET downloads = downloads + 1 WHERE id = ?', (resource_id,))
        conn.commit()
        
        user_id = row[1]
        file_name = row[6]
        privacy = row[11]
        
        conn.close()
        
        if privacy != 'public' and str(session['user_id']) != str(user_id):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        file_dir = os.path.join(UPLOAD_FOLDER, str(user_id))
        file_path = os.path.join(file_dir, file_name)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found on server'}), 404
        
        return send_from_directory(file_dir, file_name, as_attachment=True)
        
    except Exception as e:
        print(f"Error downloading resource: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resources/<int:resource_id>/like', methods=['POST'])
def like_resource(resource_id):
    """Like a resource"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('UPDATE resources SET likes = likes + 1 WHERE id = ?', (resource_id,))
        conn.commit()
        
        cursor.execute('SELECT likes FROM resources WHERE id = ?', (resource_id,))
        new_likes = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Resource liked',
            'likes': new_likes
        })
        
    except Exception as e:
        print(f"Error liking resource: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/resourses')
def resourses():
    """Render the resourses page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('resourses.html',
                         firstname=session['firstname'],
                         lastname=session['lastname'],
                         user_id=session['user_id'])

def format_file_size(bytes):
    if bytes == 0:
        return "0 Bytes"
    k = 1024
    sizes = ["Bytes", "KB", "MB", "GB"]
    i = int(math.floor(math.log(bytes) / math.log(k)))
    return f"{bytes / math.pow(k, i):.2f} {sizes[i]}"

@app.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, file_name 
            FROM resources 
            WHERE id = ?
        ''', (resource_id,))
        resource = cursor.fetchone()

        if not resource:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Resource not found'
            }), 404

        owner_id, file_name = resource

        if int(owner_id) != int(session['user_id']):
            conn.close()
            return jsonify({
                'success': False,
                'message': 'You are not allowed to delete this resource'
            }), 403

        file_path = os.path.join(
            UPLOAD_FOLDER,
            str(owner_id),
            file_name
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        cursor.execute(
            'DELETE FROM resources WHERE id = ?',
            (resource_id,)
        )
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Resource deleted successfully'
        })

    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({
            'success': False,
            'message': 'Server error while deleting'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)