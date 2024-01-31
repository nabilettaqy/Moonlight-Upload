from flask import Flask, render_template, request, redirect, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import random
import string
from decimal import Decimal

app = Flask(__name__)

# Config
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
os.makedirs(db_path, exist_ok=True)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}/uploads.db'
db = SQLAlchemy(app)

# Options
NOT_ALLOWED_ARCHIVE_EXTENSIONS = {'php',}
MAX_ARCHIVE_SIZE_MB = 10  # 10MB
MAX_ARCHIVE_SIZE_BYTES = MAX_ARCHIVE_SIZE_MB * 1024 * 1024
ALLOWED_PREVIEW_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_PREVIEW_SIZE_MB = 2  # 2MB
MAX_PREVIEW_SIZE_BYTES = MAX_PREVIEW_SIZE_MB * 1024 * 1024

# DB Models
class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folder = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    upload_date = db.Column(db.String(10), nullable=False)
    file_size_mb = db.Column(db.Float, nullable=False)
    key = db.Column(db.String(10), nullable=False, unique=True)
    preview = db.Column(db.String(255))
    download_count = db.Column(db.Integer, default=0, nullable=False) 
    view_count = db.Column(db.Integer, default=0, nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))    

class DownloadLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    download_time = db.Column(db.DateTime, default=datetime.now, nullable=False)     

def allowed_archive_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() not in NOT_ALLOWED_ARCHIVE_EXTENSIONS

def allowed_preview_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PREVIEW_EXTENSIONS

# Generate a random key for the file deletion system
def generate_random_key():
    key_length = 10
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(key_length))

# Delete unused files and empty folders
def cleanup_empty_folders():
    uploads_folder = app.config['UPLOAD_FOLDER']
    for folder_name in os.listdir(uploads_folder):
        folder_path = os.path.join(uploads_folder, folder_name)
        if os.path.isdir(folder_path) and not os.listdir(folder_path):
            os.rmdir(folder_path)

# Main page and upload logic
@app.route('/', methods=['GET', 'POST'])
def index():
    upload = None
    file_size_mb = None
    error = None
    loading = False     

    if request.method == 'POST':
        loading = True
        if 'archive' not in request.files:
            error = "No file part"
        else:
            archive_file = request.files['archive']
            if archive_file.filename == '':
                error = "No selected file"
            elif archive_file and allowed_archive_file(archive_file.filename):
                archive_data = archive_file.read()  
                if len(archive_data) > MAX_ARCHIVE_SIZE_BYTES:
                    error = "File size exceeds 10MB limit"
                else:
                    folder_name = str(uuid.uuid4().hex)
                    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], folder_name))
                    filename = secure_filename(archive_file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename)
                    with open(file_path, 'wb') as file:
                        file.write(archive_data)
                    file_size_bytes = len(archive_data)
                    file_size_mb = file_size_bytes / (1024 * 1024)
                    key = generate_random_key()
                    ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                    up_date=datetime.now().strftime('%d/%m/%Y')
                    upload = Upload(folder=folder_name, filename=filename, ip_address=ip_addr,
                                    upload_date=up_date, file_size_mb=file_size_mb, key=key)
                    db.session.add(upload)
                    db.session.commit()
                    if 'preview' in request.files:
                        preview_file = request.files['preview']
                        if preview_file.filename != '' and allowed_preview_file(preview_file.filename):
                            preview_data = preview_file.read()  

                            if len(preview_data) > MAX_PREVIEW_SIZE_BYTES:
                                error = "Preview image size exceeds 2MB limit"
                            else:
                                preview_filename = secure_filename(preview_file.filename)
                                preview_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name, preview_filename)
                                with open(preview_path, 'wb') as preview:
                                    preview.write(preview_data)
                                upload.preview = f"/uploads/{folder_name}/{preview_filename}"
                                db.session.commit()
                        else:
                            error = "Invalid preview image file type or size or no preview image file selected"
                    else:
                        error = "No preview image file selected"
            else:
                error = "Invalid file type"
        loading = False
    main_page_message = db.session.query(Message).first()
    if main_page_message:
        main_page_message = main_page_message.content
    else:
        main_page_message = ""
    return render_template('base.html', upload=upload, file_size_mb=file_size_mb, error=error, main_page_message=main_page_message, loading=loading)

# Delete page and confirmation logic
@app.route('/delete', methods=['GET', 'POST'])
@app.route('/delete/', methods=['GET', 'POST'])
def delete():
    error = None
    if request.method == 'POST':
        key = request.form['key']
        upload = Upload.query.filter_by(key=key).first()
        if upload:
            return render_template('confirm_delete.html', upload=upload)
        error = "Invalid deletion key"
    return render_template('delete.html', error=error)

@app.route('/confirm_delete', methods=['POST'])
def confirm_delete():
    error = None
    key = request.form['key']
    upload = Upload.query.filter_by(key=key).first()
    if upload:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], upload.folder, upload.filename)
        if os.path.exists(file_path):
            deleted_file_name = upload.filename
            os.remove(file_path)
            if upload.preview:
                preview_path = os.path.join(app.config['UPLOAD_FOLDER'], upload.folder, os.path.basename(upload.preview))
                if os.path.exists(preview_path):
                    os.remove(preview_path)
            db.session.delete(upload)
            db.session.commit()
            cleanup_empty_folders()
            return render_template('delete_success.html', deleted_file=deleted_file_name)
        error = "Deletion failed: File not found"
    else:
        error = "Invalid deletion key"
        error_image = "img/404-2.webp"
    return render_template('error.html', error=error, error_image=error_image)

# Vault page and download logic
@app.route('/vault/<folder>', methods=['GET'])
def vault(folder):
    with app.app_context():
        upload = Upload.query.filter_by(folder=folder).first()
        if upload:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, upload.filename)
            preview_url = url_for('preview', folder=upload.folder, filename=os.path.basename(upload.preview)) if upload.preview else None
            if os.path.exists(file_path):
                upload.view_count += 1
                db.session.commit()
                download_count = upload.download_count if upload else 0
                view_count = upload.view_count if upload else 0
                return render_template('vault.html', upload=upload, preview_url=preview_url, download_count=download_count, view_count=view_count)
        return render_template('error.html', error="Upload not found", error_image="img/404.webp")

@app.route('/download/<folder>/<filename>', methods=['GET'])
def download(folder, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    if os.path.exists(file_path):
        upload = Upload.query.filter_by(folder=folder, filename=filename).first()
        if upload:
            upload.download_count += 1
            db.session.commit()
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            download_log = DownloadLog(upload_id=upload.id, ip_address=ip_address)
            db.session.add(download_log)
            db.session.commit()
            return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path), as_attachment=True)
        else:
            error_image = "img/404-3.webp"
            return render_template('error.html', error="Requested file not found", error_image=error_image)
    else:
        error_image = "img/404-3.webp"
        return render_template('error.html', error="Requested file does not exist", error_image=error_image)

# Media page for video files
@app.route('/media/<folder>/<filename>', methods=['GET'])
def media(folder, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    if os.path.exists(file_path):
        if filename.endswith(('.mp4', '.webm')):
            if filename.endswith('.mp4'):
                media_type = 'video/mp4'
            elif filename.endswith('.webm'):
                media_type = 'video/webm'
            return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path), as_attachment=True, mimetype=media_type)
        else:
            error_image = "img/404-3.webp"
            return render_template('error.html', error="Requested file is not a supported media type", error_image=error_image)
    else:
        error_image = "img/404-3.webp"
        return render_template('error.html', error="Requested file does not exist", error_image=error_image)

# Where the preview image is served from
@app.route('/preview/<folder>/<filename>', methods=['GET'])
def preview(folder, filename):
    preview_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    if os.path.exists(preview_path):
        return send_from_directory(os.path.dirname(preview_path), os.path.basename(preview_path))
    else:
        error_image = "img/404-3.webp"
        return render_template('error.html', error="Preview image not found", error_image=error_image)
    
# Admin page and config update logic
@app.route('/admin', methods=['GET'])
@app.route('/admin/', methods=['GET'])
def admin():
    if request.remote_addr == '127.0.0.1':
        return render_template('admin.html', allowed_extensions=','.join(NOT_ALLOWED_ARCHIVE_EXTENSIONS), max_archive_size=MAX_ARCHIVE_SIZE_MB, max_preview_size=MAX_PREVIEW_SIZE_MB)
    else:
        error_image = "img/403.webp"
        return render_template('error.html', error="403 - Forbidden", error_image=error_image), 403

@app.route('/admin/update', methods=['POST'])
def admin_update():
    if request.remote_addr == '127.0.0.1':
        allowed_extensions = set(request.form.get('allowed_extensions').split(','))
        max_archive_size = int(request.form.get('max_archive_size'))
        max_preview_size = int(request.form.get('max_preview_size'))
        main_page_message = request.form.get('main_page_message')
        global NOT_ALLOWED_ARCHIVE_EXTENSIONS, MAX_ARCHIVE_SIZE_MB, MAX_ARCHIVE_SIZE_BYTES, MAX_PREVIEW_SIZE_MB, MAX_PREVIEW_SIZE_BYTES
        NOT_ALLOWED_ARCHIVE_EXTENSIONS = allowed_extensions
        MAX_ARCHIVE_SIZE_MB = max_archive_size
        MAX_ARCHIVE_SIZE_BYTES = max_archive_size * 1024 * 1024
        MAX_PREVIEW_SIZE_MB = max_preview_size
        MAX_PREVIEW_SIZE_BYTES = max_preview_size * 1024 * 1024
        message = "Configuration updated successfully."
        db.session.query(Message).delete()  
        db.session.add(Message(content=main_page_message))
        db.session.commit()
        return render_template('admin.html', allowed_extensions=','.join(NOT_ALLOWED_ARCHIVE_EXTENSIONS), max_archive_size=MAX_ARCHIVE_SIZE_MB, max_preview_size=MAX_PREVIEW_SIZE_MB, message=message, main_page_message=main_page_message)
    else:
        error_image = "img/403.webp"
        return render_template('error.html', error="403 - Forbidden", error_image=error_image), 403
    
@app.route('/admin/show_entries', methods=['POST'])
def show_entries():
    search_query = request.form.get('file_search')
    if search_query:
        entries = Upload.query.filter(Upload.filename.like(f"%{search_query}%") | (Upload.folder == search_query)).all()
        return render_template('show_entries.html', entries=entries, search_query=search_query)
    else:
        message = "Please enter a search query."
        return render_template('admin.html', allowed_extensions=','.join(NOT_ALLOWED_ARCHIVE_EXTENSIONS), max_archive_size=MAX_ARCHIVE_SIZE_MB, max_preview_size=MAX_PREVIEW_SIZE_MB, message=message, main_page_message=request.form.get('main_page_message', ''))

# Stats page
@app.route('/stats', methods=['GET'])
@app.route('/stats/', methods=['GET'])
def stats():
    num_uploads = db.session.query(Upload).count()
    num_previews = db.session.query(Upload).filter(Upload.preview.isnot(None)).count()
    total_size_bytes = db.session.query(Upload).with_entities(db.func.sum(Upload.file_size_mb)).scalar()
    total_downloads = db.session.query(Upload).with_entities(db.func.sum(Upload.download_count)).scalar()
    total_views = db.session.query(Upload).with_entities(db.func.sum(Upload.view_count)).scalar()
    if total_size_bytes is None:
        total_size_mb = 0
    else:
        total_size_mb = Decimal(total_size_bytes)
        total_size_mb = round(total_size_mb, 2)
    if total_downloads is None:
        total_downloads = 0
    if total_views is None:
        total_views = 0    
    return render_template('stats.html', num_uploads=num_uploads, num_previews=num_previews, total_size_mb=total_size_mb, total_downloads=total_downloads, total_views=total_views,)

# Static pages
@app.route('/about', methods=['GET'])
@app.route('/about/', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/donation', methods=['GET'])
@app.route('/donation/', methods=['GET'])
def advert():
    return render_template('donation.html')

@app.route('/privacy', methods=['GET'])
@app.route('/privacy/', methods=['GET'])
def privacy():
    return render_template('privacy.html')

@app.route('/tos', methods=['GET'])
@app.route('/tos/', methods=['GET'])
def terms():
    return render_template('tos.html')

# Some easter-eggs because why not 
@app.route('/fastandfurious', methods=['GET'])
@app.route('/fastandfurious/', methods=['GET'])
def ff():
    return redirect('https://www.youtube.com/watch?v=3VP_f9eZYpc')

@app.route('/prigozhin', methods=['GET'])
@app.route('/prigozhin/', methods=['GET'])
def prigozhin():
    return redirect('https://www.youtube.com/watch?v=gHv-EuK22SQ')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    error_image = "img/404.webp"
    return render_template('error.html', error="404 - Page not found", error_image=error_image), 404

@app.errorhandler(403)
def forbidden_error(error):
    error_image = "img/403.webp"
    return render_template('error.html', error="403 - Forbidden", error_image=error_image), 403

@app.errorhandler(405)
def not_found_error(error):
    error_image = "img/405.webp"
    return render_template('error.html', error="405 - Method Not Allowed", error_image=error_image), 405

@app.errorhandler(500)
def internal_server_error(error):
    error_image = "img/500.webp"
    return render_template('error.html', error="500 - Internal Server Error", error_image=error_image), 500

# Run the app and pray it works
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)