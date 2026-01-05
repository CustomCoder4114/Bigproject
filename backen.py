from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash, Response
import sqlite3
import os
import uuid
import json
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

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'temp'), exist_ok=True)

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
            SELECT id, firstname, lastname, email 
            FROM users 
            WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            # Save user info in s
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

@app.context_processor
def inject_user():
    return dict(
        firstname=session.get('firstname'),
        lastname=session.get('lastname'),
        user_id=session.get('user_id')
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

@app.route('/assignment')
def assignment():
    return render_template('assignment.html')

@app.route('/progres')
def progres():
    return render_template('progres.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# ============ UPLOAD ROUTES ============

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
    """Handle single file upload - FIXED: Store same filename in DB and disk"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        # Check if file exists
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'File type not allowed'}), 400
        
        # Get form data
        title = request.form.get('title', file.filename)
        description = request.form.get('description', '')
        category = request.form.get('category', 'general')
        resource_type = request.form.get('resourceType', 'document')
        difficulty = request.form.get('difficulty', 'beginner')
        privacy = request.form.get('privacy', 'public')
        
        # Get user info from session
        user_id = session['user_id']
        firstname = session['firstname']
        lastname = session['lastname']
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(UPLOAD_FOLDER, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # FIX 1: Generate unique filename and use SAME name for disk and DB
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_category = get_file_category(original_filename)
        thumbnail_url = get_thumbnail_url(file_category, category)
        
        # Calculate duration for videos
        duration = None
        if file_category == 'video':
            duration = '15:30'
        
        # Calculate pages for documents
        pages = 0
        if file_category in ['pdf', 'doc', 'presentation']:
            pages = 15
        
        # Save to database - FIXED: Store unique_filename in file_name field
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO resources 
            (user_id, title, description, category, resource_type, file_name, file_path, 
             file_size, file_category, file_extension, privacy, difficulty, thumbnail_url,
             duration, pages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, title, description, category, resource_type, unique_filename,  # FIX: Store unique_filename
            file_path, file_size, file_category, file_extension, privacy, difficulty,
            thumbnail_url, duration, pages
        ))
        
        resource_id = cursor.lastrowid
        conn.commit()
        
        # Get the inserted resource
        cursor.execute('''
            SELECT r.*, u.firstname, u.lastname 
            FROM resources r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        ''', (resource_id,))
        
        resource_row = cursor.fetchone()
        conn.close()
        
        # Convert row to dict
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
                'file_url': f"/uploads/{user_id}/{resource_row[6]}",  # FIX: Use file_name from DB
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
    """Serve uploaded files - UPDATED: Support HTTP Range requests for video streaming"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, user_id, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # Get file size and extension
        file_size = os.path.getsize(file_path)
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Define media file extensions
        video_exts = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpg', 'mpeg', 'wmv', 'flv']
        audio_exts = ['mp3', 'wav', 'aac', 'flac', 'm4a', 'wma', 'ogg']
        image_exts = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'ico']
        
        # Determine MIME type
        mime_types = {
            # Video
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
            # Audio
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac',
            'aac': 'audio/aac',
            'm4a': 'audio/mp4',
            'wma': 'audio/x-ms-wma',
            # Images
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'tiff': 'image/tiff',
            'ico': 'image/x-icon',
            # Documents
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'rtf': 'application/rtf',
            'odt': 'application/vnd.oasis.opendocument.text',
            # Spreadsheets
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'ods': 'application/vnd.oasis.opendocument.spreadsheet',
            # Presentations
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'odp': 'application/vnd.oasis.opendocument.presentation',
            # Archives
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed',
            '7z': 'application/x-7z-compressed',
            'tar': 'application/x-tar',
            'gz': 'application/gzip',
            # Code
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
        
        # === VIDEO STREAMING FIX: Handle HTTP Range requests ===
        range_header = request.headers.get('Range')
        
        if is_media and range_header:
            # Parse range header
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
            
            # Ensure valid range
            if start_byte >= file_size:
                start_byte = 0
            if end_byte >= file_size:
                end_byte = file_size - 1
            if start_byte > end_byte:
                start_byte, end_byte = end_byte, start_byte
            
            length = end_byte - start_byte + 1
            
            # Read the specified byte range
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
            
            # Create 206 Partial Content response
            resp = Response(
                generate(),
                206,  # Partial Content
                mimetype=mime_type,
                direct_passthrough=True
            )
            
            resp.headers.add('Content-Range', f'bytes {start_byte}-{end_byte}/{file_size}')
            resp.headers.add('Accept-Ranges', 'bytes')
            resp.headers.add('Content-Length', str(length))
            resp.headers.add('Cache-Control', 'no-cache')
            
            return resp
        
        # For non-range requests:
        # Media files (videos/audio) - serve without attachment for inline playback
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
        
        # Image files - serve directly without authentication
        if is_image:
            return send_from_directory(
                os.path.join(UPLOAD_FOLDER, user_id),
                filename,
                mimetype=mime_type
            )
        
        # For other files, require login and check permissions
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        # Check permissions for non-media files
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
                return send_from_directory(
                    os.path.join(UPLOAD_FOLDER, user_id),
                    filename,
                    as_attachment=True,
                    mimetype=mime_type
                )
        
        return jsonify({'success': False, 'message': 'Access denied'}), 403
        
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Get all resources with filters - FIXED: Generate correct URLs"""
    try:
        # Get query parameters
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        sort_by = request.args.get('sort', 'newest')
        file_type = request.args.get('type', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT r.*, u.firstname, u.lastname 
            FROM resources r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        # Add filters
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
        
        # Add sorting
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
        
        # Add pagination
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        resources_rows = cursor.fetchall()
        
        # Get total count
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
        
        # Convert rows to dicts
        resources = []
        for row in resources_rows:
            # FIX: Generate correct URL using file_name from DB
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
                'file_url': file_url,  # FIXED: Correct URL format
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
    """Get a specific resource by ID - FIXED: Generate correct URLs"""
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
        
        # Update view count
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE resources SET views = views + 1 WHERE id = ?', (resource_id,))
        conn.commit()
        conn.close()
        
        # FIX: Generate correct URL
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
            'file_url': file_url,  # FIXED: Correct URL format
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
    """Get resources for a specific user - FIXED: Generate correct URLs"""
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
            # FIX: Generate correct URL
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
                'file_url': file_url,  # FIXED: Correct URL format
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
        
        # Update download count
        cursor.execute('UPDATE resources SET downloads = downloads + 1 WHERE id = ?', (resource_id,))
        conn.commit()
        
        user_id = row[1]
        file_name = row[6]  # Use file_name from DB
        privacy = row[11]
        
        conn.close()
        
        # Check permissions
        if privacy != 'public' and str(session['user_id']) != str(user_id):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Serve the file
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
    """Render the resources page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('resourses.html',
                         firstname=session['firstname'],
                         lastname=session['lastname'],
                         user_id=session['user_id'])

# Helper function to format file size
def format_file_size(bytes):
    if bytes == 0:
        return "0 Bytes"
    k = 1024
    sizes = ["Bytes", "KB", "MB", "GB"]
    i = int(math.floor(math.log(bytes) / math.log(k)))
    return f"{bytes / math.pow(k, i):.2f} {sizes[i]}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)