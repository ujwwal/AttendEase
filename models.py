from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to attendance records
    attendance_records = db.relationship('Attendance', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_attendance_stats(self, subject_id=None):
        """Calculate attendance statistics for the user"""
        from sqlalchemy import func
        
        if subject_id:
            total = Attendance.query.filter_by(user_id=self.id, subject_id=subject_id).count()
            present = Attendance.query.filter_by(user_id=self.id, subject_id=subject_id, is_present=True).count()
        else:
            total = Attendance.query.filter_by(user_id=self.id).count()
            present = Attendance.query.filter_by(user_id=self.id, is_present=True).count()
        
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
        total = Attendance.query.filter_by(user_id=user_id, subject_id=self.id).count()
        present = Attendance.query.filter_by(user_id=user_id, subject_id=self.id, is_present=True).count()
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


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    is_present = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one attendance record per user per subject per date
    __table_args__ = (db.UniqueConstraint('user_id', 'subject_id', 'date', name='unique_attendance'),)
