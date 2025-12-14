import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Support multiple database providers:
    # - Neon: DATABASE_URL
    # - Vercel Postgres: POSTGRES_URL
    # - Other providers: DATABASE_URL
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    
    # Handle postgres:// -> postgresql:// (required by SQLAlchemy)
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Add sslmode for Neon if not already present (Neon requires SSL)
    if database_url and 'neon' in database_url and 'sslmode' not in database_url:
        separator = '&' if '?' in database_url else '?'
        database_url = f"{database_url}{separator}sslmode=require"
    
    # Use PostgreSQL in production, SQLite for local development
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Engine options for PostgreSQL connection pooling (works with Neon serverless)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 10,
    }

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
