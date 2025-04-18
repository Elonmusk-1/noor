import threading
from sqlalchemy import Column, String, Boolean, UnicodeText, BigInteger
from .base import BASE, SESSION, engine
import logging

logger = logging.getLogger(__name__)

class GroupAISettings(BASE):
    __tablename__ = "group_ai_settings"
    chat_id = Column(String(255), primary_key=True)
    ai_enabled = Column(Boolean, default=False)
    custom_prompt = Column(UnicodeText, default=None)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)
        self.ai_enabled = False
        self.custom_prompt = None

    def __repr__(self):
        return f"<AI settings for chat {self.chat_id}>"

# Drop and recreate table
if engine:
    try:
        GroupAISettings.__table__.drop(engine, checkfirst=True)
        GroupAISettings.__table__.create(engine, checkfirst=True)
        logger.info("AI settings table recreated successfully")
    except Exception as e:
        logger.error(f"Error recreating AI settings table: {str(e)}")
else:
    logger.error("Cannot create AI settings table - no database engine")

GROUPAI_LOCK = threading.RLock()

def toggle_group_ai(chat_id: int, enabled: bool = True) -> bool:
    with GROUPAI_LOCK:
        try:
            chat_id = str(chat_id)
            logger.info(f"Attempting to {'enable' if enabled else 'disable'} AI for chat {chat_id}")
            
            # Get or create settings
            settings = SESSION.query(GroupAISettings).get(chat_id)
            if not settings:
                settings = GroupAISettings(chat_id)
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

def get_group_ai_settings(chat_id: int) -> tuple:
    try:
        chat_id = str(chat_id)
        logger.info(f"Getting AI settings for chat {chat_id}")
        
        settings = SESSION.query(GroupAISettings).get(chat_id)
        if settings:
            return settings.ai_enabled, settings.custom_prompt
        logger.info(f"No AI settings found for chat {chat_id}, returning defaults")
        return False, None
    except Exception as e:
        logger.error(f"Error getting AI settings: {str(e)}")
        return False, None
    finally:
        SESSION.close()

def set_group_custom_prompt(group_id: int, prompt: str) -> bool:
    with GROUPAI_LOCK:
        try:
            logger.info(f"Setting custom prompt for group {group_id}")
            
            settings = SESSION.query(GroupAISettings).get(group_id)
            if not settings:
                settings = GroupAISettings(group_id)
            
            settings.custom_prompt = prompt
            SESSION.add(settings)
            SESSION.commit()
            logger.info(f"Successfully set custom prompt for group {group_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting group custom prompt: {str(e)}")
            SESSION.rollback()
            return False
        finally:
            SESSION.close()
