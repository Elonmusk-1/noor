import threading
from sqlalchemy import Column, String, Boolean, UnicodeText
from .base import BASE, SESSION, engine
import logging

logger = logging.getLogger(__name__)

class AISettings(BASE):
    __tablename__ = "ai_settings"
    chat_id = Column(String(14), primary_key=True)
    ai_enabled = Column(Boolean, default=False)
    custom_prompt = Column(UnicodeText, default=None)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # Convert to string for consistency
        self.ai_enabled = False
        self.custom_prompt = None

    def __repr__(self):
        return f"<AI settings for {self.chat_id}>"

# Drop existing table if it exists and create new one
if engine:
    try:
        AISettings.__table__.drop(engine, checkfirst=True)
        AISettings.__table__.create(engine, checkfirst=True)
        logger.info("AI settings table recreated successfully")
    except Exception as e:
        logger.error(f"Error recreating AI settings table: {str(e)}")
else:
    logger.error("Cannot create AI settings table - no database engine")

AISETTINGS_LOCK = threading.RLock()

def toggle_ai(chat_id: int, enabled: bool = True) -> bool:
    with AISETTINGS_LOCK:
        try:
            chat_id = str(chat_id)  # Convert to string
            logger.info(f"Attempting to {'enable' if enabled else 'disable'} AI for chat {chat_id}")
            
            # Get or create settings
            settings = SESSION.query(AISettings).get(chat_id)
            if not settings:
                settings = AISettings(chat_id)
                SESSION.add(settings)
                logger.info(f"Created new AI settings for chat {chat_id}")
            
            # Update settings
            settings.ai_enabled = enabled
            SESSION.commit()
            logger.info(f"Successfully {'enabled' if enabled else 'disabled'} AI for chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error toggling AI: {str(e)}")
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_ai_settings(chat_id: int) -> tuple:
    try:
        chat_id = str(chat_id)  # Convert to string
        logger.info(f"Getting AI settings for chat {chat_id}")
        
        settings = SESSION.query(AISettings).get(chat_id)
        if settings:
            return settings.ai_enabled, settings.custom_prompt
        logger.info(f"No AI settings found for chat {chat_id}, returning defaults")
        return False, None
    except Exception as e:
        logger.error(f"Error getting AI settings: {str(e)}")
        return False, None
    finally:
        SESSION.close()

def set_custom_prompt(chat_id: int, prompt: str) -> bool:
    with AISETTINGS_LOCK:
        try:
            chat_id = str(chat_id)  # Convert to string
            logger.info(f"Setting custom prompt for chat {chat_id}")
            
            settings = SESSION.query(AISettings).get(chat_id)
            if not settings:
                settings = AISettings(chat_id)
            
            settings.custom_prompt = prompt
            SESSION.add(settings)
            SESSION.commit()
            logger.info(f"Successfully set custom prompt for chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting custom prompt: {str(e)}")
            SESSION.rollback()
            return False
        finally:
            SESSION.close()
