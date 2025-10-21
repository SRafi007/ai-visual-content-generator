# config\database.py
"""
Database configuration and session management.
Configured to work with Supabase PostgreSQL database.
"""
from sqlalchemy import create_engine, pool, event
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import get_settings

settings = get_settings()

# Create engine with Supabase-compatible settings
# Use QueuePool with connection recycling for better performance
is_supabase = "supabase.co" in settings.DATABASE_URL

if is_supabase:
    # Use QueuePool with aggressive connection recycling for Supabase
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=pool.QueuePool,
        pool_size=5,  # Small pool for Supabase
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=300,  # Recycle connections every 5 minutes
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "application_name": "arbor_ai_studio"
        }
    )
else:
    # Regular pooling for non-Supabase databases
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle every hour
        echo=settings.DEBUG,
        connect_args={
            "connect_timeout": 10,
            "application_name": "arbor_ai_studio"
        }
    )

# Add connection pool event listeners for debugging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new connections."""
    connection_record.info['pid'] = dbapi_conn.get_backend_pid()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Verify connection is alive on checkout."""
    # Connection verification is handled by pool_pre_ping
    # This listener is here for future debugging if needed
    _ = (dbapi_conn, connection_record, connection_proxy)  # Mark as intentionally unused

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
