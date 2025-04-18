from typing import Dict, List

class Vars:
    # Bot Configuration
    BOT_TOKEN = None
    API_ID = None
    API_HASH = None
    OWNER_ID = None
    DATABASE_URL = None
    LOG_CHANNEL = None
    SUPPORT_CHAT = None
    SUDO_USERS = []
    DRAGONS = []
    WOLVES = []
    GEMINI_API_KEY = None
    
    # Database Configuration
    DB_URL: str = None  # Database URL, set in config.py
    
    # Chat Settings
    SUPPORT_ID: int = -1001249136826  # Support chat ID
    
    # Handler Groups
    FLOOD_GROUP = None
    BLACKLIST_GROUP: int = 4
    WELCOME_GROUP: int = 5
    HANDLER_GROUP: int = 7
    SPAM_CHECK_GROUP: int = 15
    
    # Anti-Flood Settings
    FLOOD_LIMIT: int = 5
    FLOOD_TIME: int = 60  # Time in seconds
    
    # Anti-Spam Settings
    SPAM_LIMIT: int = 5  # Max messages in SPAM_INTERVAL
    SPAM_INTERVAL: int = 5  # Time interval in seconds
    SPAM_MUTE_TIME: int = 60  # Mute duration in seconds
    
    # Warn Settings
    WARN_LIMIT: int = 3  # Default number of warnings before ban
    WARN_EXPIRE: int = 604800  # Warn expiry time in seconds (7 days)
    
    # Federation Settings
    FED_NAME_LIMIT: int = 50  # Maximum characters in federation name
    FED_TAG_LIMIT: int = 10   # Maximum characters in federation tag
    
    # Message Settings
    MAX_MESSAGE_LENGTH: int = 4096  # Telegram's max message length
    MEDIA_TYPES: List[str] = ["audio", "document", "photo", "sticker", "video", "voice", "video_note"]
    
    # Permission Groups
    ADMIN_PERMS: Dict[str, str] = {
        "can_change_info": "Change group info",
        "can_delete_messages": "Delete messages",
        "can_invite_users": "Invite users",
        "can_restrict_members": "Ban users",
        "can_pin_messages": "Pin messages",
        "can_promote_members": "Add new admins",
    }
    
    # Localization
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "es", "fr", "de", "it", "ru", "ar"]
    
    # Misc Settings
    BACKUP_PATH: str = "backups"  # Path to store backup files
    TEMP_DOWNLOAD_PATH: str = "downloads"  # Path for temporary downloads
    MAX_FILTERS_PER_CHAT: int = 50
    MAX_NOTES_PER_CHAT: int = 100
    
    @classmethod
    def init(cls, config):
        """Initialize variables from config"""
        # Bot Configuration
        cls.BOT_TOKEN = config.BOT_TOKEN
        cls.API_ID = config.API_ID
        cls.API_HASH = config.API_HASH
        cls.OWNER_ID = config.OWNER_ID
        
        # Database Configuration
        cls.DATABASE_URL = config.DATABASE_URL
        
        # Channel/Group Configuration
        cls.LOG_CHANNEL = config.LOG_CHANNEL
        cls.SUPPORT_CHAT = config.SUPPORT_CHAT
        
        # Admin Lists
        cls.SUDO_USERS = config.SUDO_USERS
        cls.DRAGONS = config.DRAGONS
        cls.WOLVES = config.WOLVES
        
        # AI Configuration
        cls.GEMINI_API_KEY = config.GEMINI_API_KEY
        
        # Add any other config variables that need to be initialized

    @classmethod
    def is_sudo_user(cls, user_id: int) -> bool:
        """Check if a user is sudo user"""
        return user_id in cls.SUDO_USERS or user_id == cls.OWNER_ID

    @classmethod
    def is_owner(cls, user_id: int) -> bool:
        """Check if a user is the bot owner"""
        return user_id == cls.OWNER_ID 
