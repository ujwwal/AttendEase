"""
Flask Application Entry Point
"""
import sys
import os

# Get the absolute path to the project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
from config import Config, DEFAULT_SUBJECTS
from models import db, User, Subject, Attendance

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(ROOT_DIR, 'templates'),
            static_folder=os.path.join(ROOT_DIR, 'static'),
            static_url_path='/static')
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Google Drive folder configuration
GOOGLE_DRIVE_FOLDER_ID = '1aBHLl0Wp8fcApVb4d-ZBUcfOQdsh02KU'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database on startup
with app.app_context():
    try:
        db.create_all()
        # Check and add missing default subjects
        existing_subjects = {s.name for s in Subject.query.all()}
        added_new = False
        for subj in DEFAULT_SUBJECTS:
            if subj['name'] not in existing_subjects:
                subject = Subject(name=subj['name'], total_lectures=subj['total_lectures'])
                db.session.add(subject)
                added_new = True
                print(f"Added new subject: {subj['name']}")
        
        if added_new:
            db.session.commit()
            print("Default subjects updated!")
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
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not name or not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('ERP number already registered!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        user = User(name=name, username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        try:
            from email_utils import send_welcome_email
            send_welcome_email(email, name, username, password)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        flash('Registration successful! Check your email for account details.', 'success')
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
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid ERP number or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Password Reset Routes
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            
            try:
                from email_utils import send_password_reset_email
                reset_url = url_for('reset_password', token=token, email=email, _external=True)
                result = send_password_reset_email(user.email, user.name, token, reset_url)
                print(f"Reset email result for {email}: {result}, token: {token}")
            except Exception as e:
                import traceback
                print(f"Failed to send reset email: {e}")
                traceback.print_exc()
        
        flash('If an account exists with that email, you will receive a password reset code.', 'success')
        return redirect(url_for('reset_password', email=email))
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    email = request.args.get('email', '')
    token = request.args.get('token', '')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        token = request.form.get('token', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not email or not token or not new_password:
            flash('All fields are required.', 'error')
            return render_template('reset_password.html', email=email, token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', email=email, token=token)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html', email=email, token=token)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.verify_reset_token(token):
            user.set_password(new_password)
            user.clear_reset_token()
            db.session.commit()
            flash('Password reset successful! Please login with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired reset code. Please try again.', 'error')
            return render_template('reset_password.html', email=email, token=token)
    
    return render_template('reset_password.html', email=email, token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    subjects = Subject.query.all()
    today = date.today()
    
    # OPTIMIZATION: Fetch ALL attendance records for this user in ONE query
    all_records = Attendance.query.filter_by(user_id=current_user.id).all()
    
    # Group records by subject_id for fast lookup
    records_by_subject = {}
    for r in all_records:
        if r.subject_id not in records_by_subject:
            records_by_subject[r.subject_id] = []
        records_by_subject[r.subject_id].append(r)
    
    subject_data = []
    total_attended = 0
    total_classes = 0
    
    for subject in subjects:
        # Get records from memory instead of DB
        subj_records = records_by_subject.get(subject.id, [])
        
        # Calculate stats in Python
        attended = sum(r.lectures_present for r in subj_records)
        total_marked = sum(r.lectures_total for r in subj_records)
        stats = {
            'attended': attended,
            'total_marked': total_marked
        }
        
        # Find today's record in memory
        today_record = next((r for r in subj_records if r.date == today), None)
        
        subject_data.append({
            'id': subject.id,
            'name': subject.name,
            'stats': stats,
            'marked_today': today_record is not None,
            'today_present': today_record.lectures_present if today_record else 0,
            'today_total': today_record.lectures_total if today_record else 0
        })
        
        total_attended += attended
        total_classes += total_marked
    
    overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
    
    # Build recent history from the same pre-fetched records
    history_map = {}
    for r in all_records:
        d_str = r.date.isoformat()
        if d_str not in history_map:
            history_map[d_str] = {
                'date_obj': r.date,
                'present_count': 0,
                'fully_present_count': 0,
                'total_subjects': 0
            }
        history_map[d_str]['total_subjects'] += 1
        if r.lectures_present > 0:
            history_map[d_str]['present_count'] += 1
        if r.lectures_present == r.lectures_total and r.lectures_total > 0:
            history_map[d_str]['fully_present_count'] += 1
    
    # Sort by date descending and take top 5
    sorted_dates = sorted(history_map.keys(), reverse=True)[:5]
    recent_history = {d: history_map[d] for d in sorted_dates}

    return render_template('dashboard.html', 
                         subjects=subject_data, 
                         overall_percentage=round(overall_percentage, 1),
                         total_attended=total_attended,
                         total_classes=total_classes,
                         today=today,
                         recent_history=recent_history)

@app.route('/mark-attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    subjects = Subject.query.all()
    today = date.today()
    
    # Check if a specific date is requested for editing
    requested_date_str = request.args.get('date') or request.form.get('date')
    if requested_date_str:
        try:
            target_date = datetime.strptime(requested_date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = today
    else:
        target_date = today

    # Prevent marking attendance for future dates
    if target_date > today:
        target_date = today
        flash('Cannot mark attendance for future dates.', 'warning')
    
    if request.method == 'POST':
        # Processing POST request with target_date
        attendance_date = target_date # Logic already handles safe date parsing from form if needed, but we essentially sync them
        
        for subject in subjects:
            # New simplified form: lectures_X (count) and status_X (present/absent)
            lectures_field = f'lectures_{subject.id}'
            status_field = f'status_{subject.id}'
            
            lectures_total = request.form.get(lectures_field, '0')
            status = request.form.get(status_field, 'present')
            
            try:
                lectures_total = int(lectures_total)
            except ValueError:
                lectures_total = 0
            
            # Calculate lectures_present based on status
            if status == 'present':
                lectures_present = lectures_total
            else:
                lectures_present = 0
            
            existing = Attendance.query.filter_by(
                user_id=current_user.id,
                subject_id=subject.id,
                date=attendance_date
            ).first()
            
            if lectures_total == 0:
                # No lecture - delete existing record if any
                if existing:
                    db.session.delete(existing)
            else:
                if existing:
                    existing.lectures_total = lectures_total
                    existing.lectures_present = lectures_present
                else:
                    record = Attendance(
                        user_id=current_user.id,
                        subject_id=subject.id,
                        date=attendance_date,
                        lectures_total=lectures_total,
                        lectures_present=lectures_present
                    )
                    db.session.add(record)
        
        db.session.commit()
        flash(f'Attendance saved for {attendance_date.strftime("%B %d, %Y")}!', 'success')
        return redirect(url_for('dashboard'))
    
    # GET request - load data for target_date
    subject_status = []
    for subject in subjects:
        record = Attendance.query.filter_by(
            user_id=current_user.id,
            subject_id=subject.id,
            date=target_date
        ).first()
        
        if record is None:
            lectures_total = 0
            lectures_present = 0
        else:
            lectures_total = record.lectures_total
            lectures_present = record.lectures_present
        
        subject_status.append({
            'id': subject.id,
            'name': subject.name,
            'lectures_total': lectures_total,
            'lectures_present': lectures_present,
            'already_marked': record is not None
        })
    
    return render_template('mark_attendance.html', subjects=subject_status, today=today, target_date=target_date)

@app.route('/subject/<int:subject_id>')
@login_required
def subject_detail(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    stats = subject.get_user_attendance(current_user.id)
    
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
        if 'current_password' in request.form:
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_new_password', '')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('settings'))
            
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('settings'))
            
            if len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'error')
                return redirect(url_for('settings'))
            
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('settings'))
        
        for subject in subjects:
            new_lectures = request.form.get(f'lectures_{subject.id}', subject.total_lectures)
            try:
                new_lectures = int(new_lectures)
                if new_lectures < 1:
                    new_lectures = 40
            except ValueError:
                new_lectures = 40
            subject.total_lectures = new_lectures
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', subjects=subjects)

@app.route('/notes')
@login_required
def notes():
    return render_template('notes.html', folder_id=GOOGLE_DRIVE_FOLDER_ID)

@app.route('/api/cron/weekly-report')
def cron_weekly_report():
    """
    Cron job to send weekly attendance reports.
    Allowed only via manual trigger or Vercel Cron (secured by CRON_SECRET if needed, 
    but for now open as per simple requirements).
    """
    try:
        from email_utils import send_weekly_report_email
        
        # Calculate date range for the past week (Monday to Sunday)
        today = date.today()
        # If today is Sunday, we want last Monday to today (inclusive or exclusive?)
        # Let's say report covers last 7 days including today if run in evening, 
        # or previous week if run in morning.
        # Assuming run on Sunday morning: cover previous Sunday to Saturday
        end_date = today - timedelta(days=1) # Yesterday (Saturday)
        start_date = end_date - timedelta(days=6) # Previous Sunday
        
        users = User.query.all()
        sent_count = 0
        
        for user in users:
            # 1. Get weekly stats
            weekly_records = Attendance.query.filter(
                Attendance.user_id == user.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).all()
            
            weekly_present = 0
            weekly_total = 0
            subjects_map = {} # subject_id -> {name, attended, total}
            
            # Initialize map with all subjects to show 0/0 for subjects not attended
            all_subjects = Subject.query.all()
            for sub in all_subjects:
                subjects_map[sub.id] = {
                    'name': sub.name, 
                    'attended': 0, 
                    'total': 0
                }
            
            for record in weekly_records:
                if record.subject_id in subjects_map:
                    subjects_map[record.subject_id]['attended'] += record.lectures_present
                    subjects_map[record.subject_id]['total'] += record.lectures_total
                    weekly_present += record.lectures_present
                    weekly_total += record.lectures_total
            
            # Convert map to list
            subjects_data = list(subjects_map.values())
            
            # Only send if there was at least minimal activity or if user is active
            # (Optional: send even if 0 activity to remind them?) -> Let's send to all.
            
            weekly_percentage = int((weekly_present / weekly_total * 100)) if weekly_total > 0 else 0
            
            # 2. Get overall stats
            overall_stats = user.get_attendance_stats()
            overall_percentage = overall_stats['percentage']
            
            # 3. Send email
            if user.email:
                send_weekly_report_email(
                    user.email, 
                    user.name, 
                    start_date, 
                    end_date, 
                    subjects_data, 
                    weekly_percentage, 
                    overall_percentage
                )
                sent_count += 1
                
        return jsonify({
            'status': 'success', 
            'message': f'Weekly reports sent to {sent_count} users.',
            'period': f'{start_date} to {end_date}'
        })
        
    except Exception as e:
        print(f"Cron job failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
