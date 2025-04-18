import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import BASE, SESSION, init_db, engine
from config import Config

# Import all SQL modules
from .karma_sql import update_karma, get_karma, get_karma_leaderboard
from .notes_sql import *
from .filters_sql import *
from .welcome_sql import *
from .rules_sql import *
from .blacklist_sql import *
from .antispam_sql import *
from .antiflood_sql import *
from .locks_sql import *
from .feds_sql import *
from .reports_sql import *
from .logging_sql import *
from .cleanservice_sql import *
from .backup_sql import *
from .group_ai_sql import *
from .groupchat_sql import *

logger = logging.getLogger(__name__)

# Create the database engine
engine = create_engine(Config.DATABASE_URL)  # Ensure DATABASE_URL is set correctly in your config

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a session instance
SESSION = Session()

def init() -> bool:
    """Initialize the SQL database"""
    try:
        if not Config.DATABASE_URL:
            logger.error("No database URL configured!")
            return False
            
        if not engine:
            logger.error("No database engine available!")
            return False
            
        # Create all tables
        BASE.metadata.create_all(engine)
        logger.info("Database tables created successfully")
            
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

__all__ = [
    'BASE', 'SESSION', 'engine', 'init',
    # Karma
    'update_karma', 'get_karma', 'get_karma_leaderboard',
    # Add other functions as needed...
]


