import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config

logger = logging.getLogger(__name__)

# Create the declarative base
BASE = declarative_base()

def create_db_engine():
    try:
        # Create database URL with SSL mode
        db_url = (
            f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@"
            f"{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
            "?sslmode=require"
        )
        
        # Create engine with specific settings for Supabase
        engine = create_engine(
            db_url,
            client_encoding='utf8',
            connect_args={
                "sslmode": "require",
                "application_name": "group_manager_bot"
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            logger.info("Database connection test successful")
            
        return engine
    except Exception as e:
        logger.error(f"Error creating database engine: {str(e)}")
        return None

# Create initial engine
engine = create_db_engine()
if engine:
    # Create session factory
    SESSION = scoped_session(sessionmaker(bind=engine, autoflush=False))
    # Bind the engine to the metadata of the Base class
    BASE.metadata.bind = engine
    logger.info("Database engine and session created successfully")
else:
    SESSION = None
    logger.error("Failed to create database engine")

def init_db(url):
    """Initialize database connection"""
    try:
        global engine, SESSION
        
        # Create engine with specific settings
        engine = create_engine(
            url,
            client_encoding='utf8',
            connect_args={
                "sslmode": "require",
                "application_name": "group_manager_bot"
            }
        )
        
        if SESSION:
            SESSION.remove()
            
        SESSION = scoped_session(sessionmaker(bind=engine, autoflush=False))
        BASE.metadata.bind = engine
        
        # Import all models to ensure they're registered with BASE
        from . import ai_sql, notes_sql, blacklist_sql
        
        # Create all tables
        BASE.metadata.create_all(engine)
        
        logger.info("Database connection successful")
        return SESSION
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def get_session():
    """Get the current session or create a new one"""
    global SESSION
    if not SESSION:
        logger.error("Database session not initialized!")
        return None
    return SESSION 
