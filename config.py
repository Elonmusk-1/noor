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
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/group_manager")
    
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
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI is not set in environment variables")
        if not cls.LOG_CHANNEL:
            raise ValueError("LOG_CHANNEL is not set in environment variables")
        if not cls.OWNER_ID:
            raise ValueError("OWNER_ID is not set in environment variables")
        
        logger.info(f"Bot initialized with Owner ID: {cls.OWNER_ID}")
        logger.info(f"Super users (DRAGONS): {cls.DRAGONS}")

        # Any initialization if needed
        pass 
