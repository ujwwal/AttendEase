"""
Vercel Serverless Function Entry Point
This file serves as the entry point for Vercel's serverless Python runtime.
"""
import sys
import os

# Add parent directory to path so we can import our app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date
from config import Config, DEFAULT_SUBJECTS
from models import db, User, Subject, Attendance

# Create Flask app
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    """Initialize database with default subjects"""
    with app.app_context():
        db.create_all()
        # Add default subjects if none exist
        if Subject.query.count() == 0:
            for subj in DEFAULT_SUBJECTS:
                subject = Subject(name=subj['name'], total_lectures=subj['total_lectures'])
                db.session.add(subject)
            db.session.commit()

# Initialize database on startup
with app.app_context():
    try:
        db.create_all()
        if Subject.query.count() == 0:
            for subj in DEFAULT_SUBJECTS:
                subject = Subject(name=subj['name'], total_lectures=subj['total_lectures'])
                db.session.add(subject)
            db.session.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    subjects = Subject.query.all()
    today = date.today()
    
    # Get attendance data for each subject
    subject_data = []
    total_attended = 0
    total_classes = 0
    
    for subject in subjects:
        stats = subject.get_user_attendance(current_user.id)
        
        # Check if already marked today
        today_record = Attendance.query.filter_by(
            user_id=current_user.id,
            subject_id=subject.id,
            date=today
        ).first()
        
        subject_data.append({
            'id': subject.id,
            'name': subject.name,
            'stats': stats,
            'marked_today': today_record is not None,
            'present_today': today_record.is_present if today_record else None
        })
        
        total_attended += stats['attended']
        total_classes += stats['total_marked']
    
    overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
    
    return render_template('dashboard.html', 
                         subjects=subject_data, 
                         overall_percentage=round(overall_percentage, 1),
                         total_attended=total_attended,
                         total_classes=total_classes,
                         today=today)

@app.route('/mark-attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    subjects = Subject.query.all()
    today = date.today()
    
    if request.method == 'POST':
        attendance_date = request.form.get('date', today.isoformat())
        try:
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except ValueError:
            attendance_date = today
        
        marked_count = 0
        for subject in subjects:
            field_name = f'subject_{subject.id}'
            status = request.form.get(field_name, 'none')  # none, absent, or present
            
            # Check if record exists for this date
            existing = Attendance.query.filter_by(
                user_id=current_user.id,
                subject_id=subject.id,
                date=attendance_date
            ).first()
            
            if status == 'none':
                # No lecture - remove any existing record for this date
                if existing:
                    db.session.delete(existing)
            else:
                # There was a lecture - create or update record
                is_present = (status == 'present')
                if existing:
                    existing.is_present = is_present
                else:
                    record = Attendance(
                        user_id=current_user.id,
                        subject_id=subject.id,
                        date=attendance_date,
                        is_present=is_present
                    )
                    db.session.add(record)
                marked_count += 1
        
        db.session.commit()
        flash(f'Attendance marked for {attendance_date.strftime("%B %d, %Y")}!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get today's attendance status for each subject
    subject_status = []
    for subject in subjects:
        today_record = Attendance.query.filter_by(
            user_id=current_user.id,
            subject_id=subject.id,
            date=today
        ).first()
        
        # Determine status: none, absent, or present
        if today_record is None:
            status = 'none'
            status_text = 'No Lecture'
        elif today_record.is_present:
            status = 'present'
            status_text = 'Present'
        else:
            status = 'absent'
            status_text = 'Absent'
        
        subject_status.append({
            'id': subject.id,
            'name': subject.name,
            'status': status,
            'status_text': status_text,
            'already_marked': today_record is not None
        })
    
    return render_template('mark_attendance.html', subjects=subject_status, today=today)

@app.route('/subject/<int:subject_id>')
@login_required
def subject_detail(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    stats = subject.get_user_attendance(current_user.id)
    
    # Get all attendance records for this subject
    records = Attendance.query.filter_by(
        user_id=current_user.id,
        subject_id=subject_id
    ).order_by(Attendance.date.desc()).all()
    
    return render_template('subject_detail.html', subject=subject, stats=stats, records=records)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        for subject in subjects:
            new_name = request.form.get(f'name_{subject.id}', subject.name).strip()
            new_lectures = request.form.get(f'lectures_{subject.id}', subject.total_lectures)
            
            try:
                new_lectures = int(new_lectures)
                if new_lectures < 1:
                    new_lectures = 40
            except ValueError:
                new_lectures = 40
            
            subject.name = new_name
            subject.total_lectures = new_lectures
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', subjects=subjects)

@app.route('/api/toggle-attendance', methods=['POST'])
@login_required
def toggle_attendance():
    """API endpoint for quick attendance toggle"""
    data = request.get_json()
    subject_id = data.get('subject_id')
    attendance_date = data.get('date', date.today().isoformat())
    is_present = data.get('is_present', True)
    
    try:
        attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
    except ValueError:
        attendance_date = date.today()
    
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404
    
    # Find or create attendance record
    record = Attendance.query.filter_by(
        user_id=current_user.id,
        subject_id=subject_id,
        date=attendance_date
    ).first()
    
    if record:
        record.is_present = is_present
    else:
        record = Attendance(
            user_id=current_user.id,
            subject_id=subject_id,
            date=attendance_date,
            is_present=is_present
        )
        db.session.add(record)
    
    db.session.commit()
    
    # Get updated stats
    stats = subject.get_user_attendance(current_user.id)
    
    return jsonify({
        'success': True,
        'stats': stats,
        'is_present': is_present
    })

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
