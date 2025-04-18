import threading
from typing import Union

from sqlalchemy import Column, String, Boolean, UnicodeText

from . import BASE, SESSION

class LogChannel(BASE):
    __tablename__ = "log_channels"
    chat_id = Column(String(14), primary_key=True)
    log_channel = Column(String(14))
    log_enabled = Column(Boolean, default=False)
    message_types = Column(UnicodeText)  # JSON string of enabled message types

    def __init__(self, chat_id, log_channel=None):
        self.chat_id = str(chat_id)
        self.log_channel = str(log_channel) if log_channel else None
        self.log_enabled = bool(log_channel)
        self.message_types = "{}"  # Default: all types disabled

    def __repr__(self):
        return f"<Log channel settings for {self.chat_id}>"

# Note: Don't create tables here, they are created in __init__.py
# Remove this line:
# LogChannel.__table__.create(checkfirst=True)

LOGS_INSERTION_LOCK = threading.RLock()

def set_log_channel(chat_id: Union[str, int], log_channel: Union[str, int]) -> bool:
    with LOGS_INSERTION_LOCK:
        try:
            chat = SESSION.query(LogChannel).get(str(chat_id))
            if not chat:
                chat = LogChannel(chat_id, log_channel)
            else:
                chat.log_channel = str(log_channel)
                chat.log_enabled = True

            SESSION.add(chat)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def stop_chat_logging(chat_id: Union[str, int]) -> bool:
    with LOGS_INSERTION_LOCK:
        try:
            chat = SESSION.query(LogChannel).get(str(chat_id))
            if chat:
                chat.log_enabled = False
                SESSION.add(chat)
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_chat_log_channel(chat_id: Union[str, int]) -> str:
    try:
        chat = SESSION.query(LogChannel).get(str(chat_id))
        if chat and chat.log_enabled:
            return chat.log_channel
        return None
    finally:
        SESSION.close()

def set_message_types(chat_id: Union[str, int], message_types: str) -> bool:
    with LOGS_INSERTION_LOCK:
        try:
            chat = SESSION.query(LogChannel).get(str(chat_id))
            if chat:
                chat.message_types = message_types
                SESSION.add(chat)
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_message_types(chat_id: Union[str, int]) -> str:
    try:
        chat = SESSION.query(LogChannel).get(str(chat_id))
        return chat.message_types if chat else "{}"
    finally:
        SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with LOGS_INSERTION_LOCK:
        chat = SESSION.query(LogChannel).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)
            SESSION.commit() 
