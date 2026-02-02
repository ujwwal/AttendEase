import os
from urllib.parse import urlparse

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-2.0-flash'  # Using Gemini 2.0 Flash model
    
    # Support multiple database providers:
    # - Neon: DATABASE_URL
    # - Vercel Postgres: POSTGRES_URL / POSTGRES_URL_NON_POOLING
    # - Other providers: DATABASE_URL
    database_url = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('POSTGRES_URL_NON_POOLING')
        or os.environ.get('POSTGRES_URL')
    )
    
    # Handle postgres:// -> postgresql:// (required by SQLAlchemy)
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Add sslmode for hosted Postgres in Vercel if not already present
    if database_url and os.environ.get('VERCEL') and 'sslmode' not in database_url:
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
            # Detect pooled connections that don't support statement_timeout in connect_args
            # Common patterns: Neon pooled URLs contain "-pooler." in hostname (e.g., ep-xxx-pooler.region.neon.tech)
            # or use port 6543 (common pooled connection port instead of standard 5432)
            parsed_url = urlparse(SQLALCHEMY_DATABASE_URI)
            hostname = parsed_url.hostname or ''
            port = parsed_url.port or 5432
            
            is_pooled_connection = (
                '-pooler.' in hostname or   # Neon pooled: ep-xxx-pooler.region.neon.tech
                hostname.endswith('-pooler') or  # Edge case: hostname ends with -pooler (no domain)
                port == 6543                # Pooled connection port
            )
            
            connect_args = {
                'connect_timeout': 10,  # 10 second connection timeout
            }
            
            # Only add statement_timeout for non-pooled (direct) connections
            # Pooled connections reject this option causing 500 errors during login
            if not is_pooled_connection:
                connect_args['options'] = '-c statement_timeout=30000'  # 30 second query timeout
            
            SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = connect_args
    else:
        # Use a writable path for SQLite (e.g., Vercel serverless)
        sqlite_path = os.environ.get(
            'SQLITE_PATH',
            os.path.join('/tmp' if os.environ.get('VERCEL') else os.path.dirname(__file__), 'attendance.db')
        )
        sqlite_dir = os.path.dirname(sqlite_path)
        if sqlite_dir:
            os.makedirs(sqlite_dir, exist_ok=True)
        # Normalize path for SQLite URI (handles Windows paths too)
        sqlite_uri_path = sqlite_path.replace('\\', '/')
        if ':' in sqlite_uri_path and not sqlite_uri_path.startswith('/'):
            sqlite_uri_path = f"/{sqlite_uri_path}"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_uri_path}"
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
