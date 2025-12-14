import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Default subjects configuration
DEFAULT_SUBJECTS = [
    {'name': 'Subject 1', 'total_lectures': 40},
    {'name': 'Subject 2', 'total_lectures': 40},
    {'name': 'Subject 3', 'total_lectures': 40},
    {'name': 'Subject 4', 'total_lectures': 40},
    {'name': 'Subject 5', 'total_lectures': 40},
    {'name': 'Subject 6', 'total_lectures': 40},
    {'name': 'Subject 7', 'total_lectures': 40},
    {'name': 'Subject 8', 'total_lectures': 40},
]
