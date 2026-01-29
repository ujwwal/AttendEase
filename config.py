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
    
    # Use PostgreSQL in production, SQLite for local development/serverless fallback
    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url
        # Engine options optimized for PostgreSQL (Neon/Vercel)
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,      # Check connection health before use
            'pool_recycle': 300,        # Recycle connections after 5 minutes
            'pool_size': 1,             # Minimal pool for serverless (each function is isolated)
            'max_overflow': 2,          # Allow only 2 extra connections
        }
        if SQLALCHEMY_DATABASE_URI.startswith('postgresql://') or SQLALCHEMY_DATABASE_URI.startswith('postgresql+'):
            SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
                'connect_timeout': 10,  # 10 second connection timeout
                'options': '-c statement_timeout=30000'  # 30 second query timeout
            }
    else:
        # Use a writable path for SQLite (e.g., Vercel serverless)
        sqlite_path = os.environ.get(
            'SQLITE_PATH',
            os.path.join('/tmp' if os.environ.get('VERCEL') else os.path.dirname(__file__), 'attendance.db')
        )
        sqlite_dir = os.path.dirname(sqlite_path)
        if sqlite_dir:
            os.makedirs(sqlite_dir, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Default subjects configuration (Fixed - cannot be edited by users)
DEFAULT_SUBJECTS = [
    {'name': 'Data Warehousing and Data Mining', 'total_lectures': 40},
    {'name': 'Web Programming (PHP)', 'total_lectures': 40},
    {'name': 'Software Project Management', 'total_lectures': 40},
    {'name': 'Elective', 'total_lectures': 40},
    {'name': 'Lab on Web Programming with Project', 'total_lectures': 40},
    {'name': 'Lab on Data Visualization', 'total_lectures': 40},
    {'name': 'Digital Marketing', 'total_lectures': 40},
    {'name': 'Indian Culture', 'total_lectures': 40},
    {'name': 'Professional Competency Development', 'total_lectures': 40},
]
