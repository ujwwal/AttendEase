"""
Flask Application Entry Point
"""
import sys
import os
import threading
import json
import time
from collections import defaultdict

# Get the absolute path to the project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
from config import Config, DEFAULT_SUBJECTS
from models import db, User, Subject, Attendance

# Gemini AI imports
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-genai not installed. AI chat will be disabled.")

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

# Rate limiting for AI chat (20 requests per day per user)
chat_rate_limits = defaultdict(list)
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW = 86400  # 24 hours in seconds

def check_rate_limit(user_id):
    """Check if user has exceeded daily rate limit. Returns (allowed, remaining)."""
    now = time.time()
    # Clean old entries (older than 24 hours)
    chat_rate_limits[user_id] = [t for t in chat_rate_limits[user_id] if now - t < RATE_LIMIT_WINDOW]
    
    if len(chat_rate_limits[user_id]) >= RATE_LIMIT_REQUESTS:
        return False, 0
    
    chat_rate_limits[user_id].append(now)
    return True, RATE_LIMIT_REQUESTS - len(chat_rate_limits[user_id])

# Initialize Gemini AI
def get_gemini_client():
    """Get configured Gemini client instance."""
    if not GEMINI_AVAILABLE:
        return None
    
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        print("Warning: GEMINI_API_KEY not set. AI chat will be disabled.")
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('error_404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()  # Rollback any failed transactions
    return render_template('error_500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other uncaught exceptions."""
    # Pass through HTTP exceptions (like redirects)
    from werkzeug.exceptions import HTTPException
    if isinstance(error, HTTPException):
        return error
    
    # Log the error
    print(f"Unhandled exception: {error}")
    import traceback
    traceback.print_exc()
    
    # Rollback any failed database transactions
    db.session.rollback()
    
    # Return 500 error page
    return render_template('error_500.html'), 500

# Database initialization flag
_db_initialized = False
_db_init_lock = threading.Lock()

def init_database():
    """Initialize database tables and default subjects."""
    global _db_initialized
    if _db_initialized:
        return

    with _db_init_lock:
        if _db_initialized:
            return

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
            else:
                db.session.rollback()
            _db_initialized = True
        except Exception as e:
            db.session.rollback()
            print(f"Database initialization error: {e}")


@app.before_request
def ensure_database_initialized():
    init_database()

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
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database error during registration: {e}")
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
        
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
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Database error generating reset token: {e}")
                flash('An error occurred. Please try again.', 'error')
                return render_template('forgot_password.html')
            
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
            
            try:
                db.session.commit()
                flash('Password reset successful! Please login with your new password.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                print(f"Database error resetting password: {e}")
                flash('An error occurred. Please try again.', 'error')
                return render_template('reset_password.html', email=email, token=token)
        else:
            flash('Invalid or expired reset code. Please try again.', 'error')
            return render_template('reset_password.html', email=email, token=token)
    
    return render_template('reset_password.html', email=email, token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    subjects = Subject.query.all()
    today = date.today()
    
    subject_data = []
    total_attended = 0
    total_classes = 0
    
    for subject in subjects:
        stats = subject.get_user_attendance(current_user.id)
        
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
            'today_present': today_record.lectures_present if today_record else 0,
            'today_total': today_record.lectures_total if today_record else 0
        })
        
        total_attended += stats['attended']
        total_classes += stats['total_marked']
    
    overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
    
    # Get recent history (last 5 distinct dates)
    recent_dates = db.session.query(Attendance.date).filter_by(user_id=current_user.id)\
        .distinct().order_by(Attendance.date.desc()).limit(5).all()
    
    recent_history = {}
    for r_date in recent_dates:
        d = r_date[0]
        date_str = d.isoformat()
        
        # Get stats for this day
        day_records = Attendance.query.filter_by(user_id=current_user.id, date=d).all()
        present_count = sum(1 for r in day_records if r.lectures_present > 0)
        fully_present_count = sum(1 for r in day_records if r.lectures_present == r.lectures_total)
        
        recent_history[date_str] = {
            'date_obj': d,
            'present_count': present_count,
            'fully_present_count': fully_present_count,
            'total_subjects': len(day_records)
        }

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
        
        try:
            db.session.commit()
            flash(f'Attendance saved for {attendance_date.strftime("%B %d, %Y")}!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            print(f"Database error saving attendance: {e}")
            flash('Failed to save attendance. Please try again.', 'error')
            # Re-load the form with the data
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
            
            try:
                db.session.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('settings'))
            except Exception as e:
                db.session.rollback()
                print(f"Database error changing password: {e}")
                flash('Failed to change password. Please try again.', 'error')
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
        
        try:
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            db.session.rollback()
            print(f"Database error updating settings: {e}")
            flash('Failed to update settings. Please try again.', 'error')
            return redirect(url_for('settings'))
    
    return render_template('settings.html', subjects=subjects)

@app.route('/notes')
@login_required
def notes():
    return render_template('notes.html', folder_id=GOOGLE_DRIVE_FOLDER_ID)

# ============================================
# AI Chat Routes
# ============================================

def get_user_context():
    """Build context about user's subjects and attendance for AI."""
    subjects = Subject.query.all()
    today = date.today()
    
    context_lines = []
    context_lines.append(f"Today's date: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})")
    context_lines.append(f"User: {current_user.name}")
    context_lines.append("\nSubjects and current attendance:")
    
    subject_list = []
    for subject in subjects:
        stats = subject.get_user_attendance(current_user.id)
        subject_info = {
            'id': subject.id,
            'name': subject.name,
            'attended': stats['attended'],
            'total': stats['total_marked'],
            'percentage': stats['percentage']
        }
        subject_list.append(subject_info)
        context_lines.append(f"- {subject.name} (ID: {subject.id}): {stats['attended']}/{stats['total_marked']} lectures ({stats['percentage']}%)")
    
    return "\n".join(context_lines), subject_list

def get_ai_system_prompt():
    """Return the restrictive system prompt for the AI."""
    return """You are an attendance assistant for AttendEase, a college attendance tracking app. 

STRICT RULES - YOU MUST FOLLOW THESE:
1. You can ONLY help with:
   - Marking attendance (present or absent) for specific subjects
   - Showing attendance summaries/statistics
   - Answering questions about the user's attendance data

2. You CANNOT and MUST NEVER:
   - Delete any attendance records
   - Modify user account information
   - Access or discuss anything outside attendance management
   - Execute any database operations directly
   - Provide information about other users

3. For marking attendance:
   - ALWAYS show a summary preview BEFORE marking
   - For batch operations (multiple lectures), use TODAY'S DATE unless the user specifies a different date
   - Ask for confirmation before any marking operation
   - Valid statuses are: "present" or "absent"
   - Lectures count should be between 1-3 per subject per day

4. Response format for attendance marking:
   When the user wants to mark attendance, respond with a JSON block in this exact format:
   ```json
   {
     "action": "preview_attendance",
     "message": "Your friendly message explaining the preview",
     "data": [
       {
         "subject_id": <id>,
         "subject_name": "<name>",
         "date": "YYYY-MM-DD",
         "lectures": <number 1-3>,
         "status": "present" or "absent"
       }
     ]
   }
   ```

5. Response format for attendance summary:
   When showing attendance summary, just respond with a friendly message containing the statistics.

6. If user asks for something you cannot do, politely explain that you can only help with attendance marking and viewing summaries.

Remember: BE HELPFUL but STAY WITHIN YOUR BOUNDARIES. Safety first!"""

def parse_ai_response(response_text):
    """Parse AI response to extract any JSON action blocks."""
    try:
        # Look for JSON block in the response
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end > start:
                json_str = response_text[start:end].strip()
                action_data = json.loads(json_str)
                # Extract message text (everything before and after JSON block)
                message_before = response_text[:response_text.find('```json')].strip()
                message_after = response_text[end + 3:].strip()
                clean_message = f"{message_before} {message_after}".strip()
                if not clean_message and 'message' in action_data:
                    clean_message = action_data['message']
                return {
                    'has_action': True,
                    'action': action_data.get('action'),
                    'data': action_data.get('data', []),
                    'message': clean_message or action_data.get('message', '')
                }
    except json.JSONDecodeError:
        pass
    
    # No action found, return as plain message
    return {
        'has_action': False,
        'message': response_text
    }

@app.route('/chat')
@login_required
def chat():
    """Render the AI chat page."""
    # Check if Gemini is available
    if not GEMINI_AVAILABLE or not Config.GEMINI_API_KEY:
        flash('AI Chat is currently unavailable. Please try again later.', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    """Handle chat messages and interact with Gemini AI."""
    # Check rate limit
    allowed, remaining = check_rate_limit(current_user.id)
    if not allowed:
        return jsonify({
            'error': 'Rate limit exceeded. Please wait a moment before sending more messages.',
            'rate_limit_remaining': 0
        }), 429
    
    # Check if Gemini is available
    client = get_gemini_client()
    if not client:
        return jsonify({'error': 'AI service is currently unavailable.'}), 503
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message cannot be empty.'}), 400
    
    if len(user_message) > 500:
        return jsonify({'error': 'Message too long. Please keep it under 500 characters.'}), 400
    
    try:
        # Build context
        user_context, subject_list = get_user_context()
        
        # Build the full prompt
        full_prompt = f"""{get_ai_system_prompt()}

CURRENT USER CONTEXT:
{user_context}

USER MESSAGE: {user_message}

Respond helpfully while following all the rules above."""

        # Get AI response
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=full_prompt
        )
        ai_response = response.text
        
        # Parse the response for any actions
        parsed = parse_ai_response(ai_response)
        
        # If there's a preview action, store it in session for confirmation
        if parsed['has_action'] and parsed['action'] == 'preview_attendance':
            session['pending_attendance'] = {
                'data': parsed['data'],
                'timestamp': time.time()
            }
        
        return jsonify({
            'response': parsed['message'],
            'has_action': parsed['has_action'],
            'action': parsed.get('action'),
            'action_data': parsed.get('data', []),
            'rate_limit_remaining': remaining
        })
        
    except Exception as e:
        print(f"Chat API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An error occurred while processing your message.'}), 500

@app.route('/api/chat/confirm', methods=['POST'])
@login_required
def confirm_attendance():
    """Confirm and execute the pending attendance action."""
    # Check if there's a pending action
    pending = session.get('pending_attendance')
    
    if not pending:
        return jsonify({'error': 'No pending attendance action found. Please try again.'}), 400
    
    # Check if the pending action is still valid (within 5 minutes)
    if time.time() - pending['timestamp'] > 300:
        session.pop('pending_attendance', None)
        return jsonify({'error': 'The attendance preview has expired. Please start over.'}), 400
    
    data = pending['data']
    today = date.today()
    
    try:
        marked_count = 0
        for item in data:
            subject_id = item.get('subject_id')
            date_str = item.get('date')
            lectures = item.get('lectures', 1)
            status = item.get('status', 'present')
            
            # Validate subject exists
            subject = Subject.query.get(subject_id)
            if not subject:
                continue
            
            # Parse and validate date
            try:
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                attendance_date = today
            
            # Prevent future dates
            if attendance_date > today:
                attendance_date = today
            
            # Validate lectures count
            lectures = max(1, min(3, int(lectures)))
            
            # Calculate present/total based on status
            if status == 'present':
                lectures_present = lectures
            else:
                lectures_present = 0
            
            # Upsert attendance record
            existing = Attendance.query.filter_by(
                user_id=current_user.id,
                subject_id=subject_id,
                date=attendance_date
            ).first()
            
            if existing:
                existing.lectures_total = lectures
                existing.lectures_present = lectures_present
            else:
                record = Attendance(
                    user_id=current_user.id,
                    subject_id=subject_id,
                    date=attendance_date,
                    lectures_total=lectures,
                    lectures_present=lectures_present
                )
                db.session.add(record)
            
            marked_count += 1
        
        db.session.commit()
        
        # Clear the pending action
        session.pop('pending_attendance', None)
        
        return jsonify({
            'success': True,
            'message': f'Successfully marked attendance for {marked_count} subject(s)!',
            'marked_count': marked_count
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error confirming attendance: {e}")
        return jsonify({'error': 'Failed to mark attendance. Please try again.'}), 500

@app.route('/api/chat/cancel', methods=['POST'])
@login_required
def cancel_attendance():
    """Cancel the pending attendance action."""
    session.pop('pending_attendance', None)
    return jsonify({'success': True, 'message': 'Attendance marking cancelled.'})

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
