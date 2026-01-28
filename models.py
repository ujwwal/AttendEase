from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # User's full name
    username = db.Column(db.String(80), unique=True, nullable=False)  # ERP number
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Password reset fields
    reset_token = db.Column(db.String(6), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Relationship to attendance records
    attendance_records = db.relationship('Attendance', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate a 6-digit reset token valid for 15 minutes"""
        self.reset_token = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.reset_token_expires = datetime.utcnow() + timedelta(minutes=15)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return self.reset_token == token
    
    def clear_reset_token(self):
        """Clear the reset token after successful password reset"""
        self.reset_token = None
        self.reset_token_expires = None
    
    def get_attendance_stats(self, subject_id=None):
        """Calculate attendance statistics for the user"""
        from sqlalchemy import func
        
        query = db.session.query(
            func.coalesce(func.sum(Attendance.lectures_total), 0).label('total'),
            func.coalesce(func.sum(Attendance.lectures_present), 0).label('present')
        ).filter_by(user_id=self.id)
        
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        result = query.first()
        total = result.total if result else 0
        present = result.present if result else 0
        
        percentage = (present / total * 100) if total > 0 else 0
        return {'total': total, 'present': present, 'percentage': round(percentage, 1)}


class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_lectures = db.Column(db.Integer, default=40)
    
    # Relationship to attendance records
    attendance_records = db.relationship('Attendance', backref='subject', lazy='dynamic')
    
    def get_user_attendance(self, user_id):
        """Get attendance stats for a specific user in this subject"""
        from sqlalchemy import func
        
        # Sum up all lectures present and total for this subject
        result = db.session.query(
            func.coalesce(func.sum(Attendance.lectures_present), 0).label('present'),
            func.coalesce(func.sum(Attendance.lectures_total), 0).label('total')
        ).filter_by(user_id=user_id, subject_id=self.id).first()
        
        present = result.present if result else 0
        total = result.total if result else 0
        percentage = (present / total * 100) if total > 0 else 0
        
        # Calculate projected attendance
        remaining = max(0, self.total_lectures - total)
        
        return {
            'attended': present,
            'total_marked': total,
            'total_lectures': self.total_lectures,
            'remaining': remaining,
            'percentage': round(percentage, 1)
        }


def _get_current_date():
    """Helper function to get current date for database default."""
    return datetime.utcnow().date()


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=_get_current_date)
    # Number of lectures attended (0 to N)
    lectures_present = db.Column(db.Integer, default=1)
    # Total number of lectures that occurred (1 to N)
    lectures_total = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one attendance record per user per subject per date
    __table_args__ = (db.UniqueConstraint('user_id', 'subject_id', 'date', name='unique_attendance'),)
