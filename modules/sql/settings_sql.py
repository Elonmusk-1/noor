import threading

from sqlalchemy import Column, String, Boolean, UnicodeText, Integer
from . import BASE, SESSION

class GroupSettings(BASE):
    __tablename__ = "group_settings"
    chat_id = Column(String(14), primary_key=True)
    setting = Column(String(50))
    value = Column(UnicodeText, default="")

    def __init__(self, chat_id, setting, value):
        self.chat_id = str(chat_id)
        self.setting = setting
        self.value = value

    def __repr__(self):
        return f"<{self.chat_id} setting {self.setting}>"

INSERTION_LOCK = threading.RLock()

def set_setting(chat_id, setting, value):
    with INSERTION_LOCK:
        curr_setting = SESSION.query(GroupSettings).get((str(chat_id), setting))
        if not curr_setting:
            curr_setting = GroupSettings(chat_id, setting, value)

        curr_setting.value = value
        SESSION.add(curr_setting)
        SESSION.commit()

def get_setting(chat_id, setting):
    try:
        setting = SESSION.query(GroupSettings).get((str(chat_id), setting))
        if setting:
            return setting.value
        return None
    finally:
        SESSION.close()

def get_settings(chat_id):
    try:
        return SESSION.query(GroupSettings).filter(
            GroupSettings.chat_id == str(chat_id)
        ).all()
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat_settings = (
            SESSION.query(GroupSettings)
            .filter(GroupSettings.chat_id == str(old_chat_id))
            .all()
        )
        for setting in chat_settings:
            setting.chat_id = str(new_chat_id)
        SESSION.commit() 
