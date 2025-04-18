import threading
from sqlalchemy import Column, String, Boolean, UnicodeText, BigInteger
from .base import BASE, SESSION
import logging

logger = logging.getLogger(__name__)

class GroupChatSettings(BASE):
    __tablename__ = "groupchat_settings"
    chat_id = Column(BigInteger, primary_key=True)
    is_enabled = Column(Boolean, default=False)
    custom_prompt = Column(UnicodeText, default=None)

    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.is_enabled = False
        self.custom_prompt = None

    def __repr__(self):
        return f"<GroupChat settings for {self.chat_id}>"

GroupChatSettings.__table__.create(checkfirst=True)
CHAT_SETTINGS_LOCK = threading.RLock()

def enable_groupchat(chat_id: int) -> bool:
    with CHAT_SETTINGS_LOCK:
        try:
            chat = SESSION.query(GroupChatSettings).get(chat_id)
            if not chat:
                chat = GroupChatSettings(chat_id)
            chat.is_enabled = True
            SESSION.add(chat)
            SESSION.commit()
            return True
        except Exception as e:
            logger.error(f"Error enabling groupchat: {e}")
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def disable_groupchat(chat_id: int) -> bool:
    with CHAT_SETTINGS_LOCK:
        try:
            chat = SESSION.query(GroupChatSettings).get(chat_id)
            if chat:
                chat.is_enabled = False
                SESSION.commit()
            return True
        except Exception as e:
            logger.error(f"Error disabling groupchat: {e}")
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def is_groupchat_enabled(chat_id: int) -> bool:
    try:
        chat = SESSION.query(GroupChatSettings).get(chat_id)
        return bool(chat and chat.is_enabled)
    except Exception as e:
        logger.error(f"Error checking groupchat status: {e}")
        return False
    finally:
        SESSION.close()

def set_custom_prompt(chat_id: int, prompt: str) -> bool:
    with CHAT_SETTINGS_LOCK:
        try:
            chat = SESSION.query(GroupChatSettings).get(chat_id)
            if not chat:
                chat = GroupChatSettings(chat_id)
            chat.custom_prompt = prompt
            SESSION.add(chat)
            SESSION.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting custom prompt: {e}")
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_custom_prompt(chat_id: int) -> str:
    try:
        chat = SESSION.query(GroupChatSettings).get(chat_id)
        return chat.custom_prompt if chat else None
    except Exception as e:
        logger.error(f"Error getting custom prompt: {e}")
        return None
    finally:
        SESSION.close() 