import threading
from typing import Union

from sqlalchemy import Column, String, Boolean
from . import BASE, SESSION

class CleanServiceSettings(BASE):
    __tablename__ = "clean_service"
    chat_id = Column(String(14), primary_key=True)
    clean_service = Column(Boolean, default=True)
    clean_commands = Column(Boolean, default=False)
    
    def __init__(self, chat_id):
        self.chat_id = str(chat_id)
        self.clean_service = True
        self.clean_commands = False

    def __repr__(self):
        return f"<Clean service settings for {self.chat_id}>"

CLEAN_SERVICE_LOCK = threading.RLock()

def get_clean_service(chat_id: Union[str, int]) -> bool:
    try:
        chat_setting = SESSION.query(CleanServiceSettings).get(str(chat_id))
        if chat_setting:
            return chat_setting.clean_service
        return True  # Default: True
    finally:
        SESSION.close()

def set_clean_service(chat_id: Union[str, int], setting: bool) -> bool:
    with CLEAN_SERVICE_LOCK:
        try:
            chat_setting = SESSION.query(CleanServiceSettings).get(str(chat_id))
            if not chat_setting:
                chat_setting = CleanServiceSettings(chat_id)

            chat_setting.clean_service = setting
            SESSION.add(chat_setting)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with CLEAN_SERVICE_LOCK:
        chat_settings = SESSION.query(CleanServiceSettings).get(str(old_chat_id))
        if chat_settings:
            chat_settings.chat_id = str(new_chat_id)
            SESSION.add(chat_settings)
            SESSION.commit()

def toggle_clean_commands(chat_id: str, setting: bool) -> bool:
    with SESSION() as session:
        chat = session.query(CleanServiceSettings).get(str(chat_id))
        if not chat:
            chat = CleanServiceSettings(chat_id)
            
        chat.clean_commands = setting
        session.add(chat)
        session.commit()
        return setting

def get_clean_settings(chat_id: str) -> tuple:
    with SESSION() as session:
        chat = session.query(CleanServiceSettings).get(str(chat_id))
        if chat:
            return chat.clean_service, chat.clean_commands
        return False, False 
