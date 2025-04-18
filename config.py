import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    OWNER_ID = int(os.getenv("OWNER_ID"))
    SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split())) if os.getenv("SUDO_USERS") else []
    
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Construct Database URL with SSL mode
    DATABASE_URL = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?sslmode=require"
    )
    
    # Channel/Group Configuration
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "")
    
    # Other Configuration
    WEBHOOK = bool(os.getenv("WEBHOOK", False))
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    CERT_PATH = os.getenv("CERT_PATH", "")
    PORT = int(os.getenv("PORT", 8443))
    
    # AI Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Admin Lists
    DRAGONS = {2036109591}  # Add your ID here
    WOLVES = list(map(int, os.getenv("WOLVES", "").split(","))) if os.getenv("WOLVES") else []
    
    # Handler Groups
    FLOOD_GROUP = 1
    HANDLER_GROUP = 2
    SPAM_CHECK_GROUP = 3
    
    # Other Configuration
    ALLOW_EXCL = True
    DEL_CMDS = True
    STRICT_GBAN = True
    VERSION = "1.0.0"

    @classmethod
    def init(cls):
        """Initialize the configuration"""
        # Validate required settings
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in environment variables")
        if not cls.DATABASE_URL:
            raise ValueError("Database URL could not be constructed. Check database settings.")
        if not cls.LOG_CHANNEL:
            raise ValueError("LOG_CHANNEL is not set in environment variables")
        if not cls.OWNER_ID:
            raise ValueError("OWNER_ID is not set in environment variables")
        
        logger.info(f"Bot initialized with Owner ID: {cls.OWNER_ID}")
        logger.info(f"Super users (DRAGONS): {cls.DRAGONS}")

        # Any initialization if needed
        pass 
