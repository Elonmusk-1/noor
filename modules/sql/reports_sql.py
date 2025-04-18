import threading
from typing import Union

from sqlalchemy import Column, String, Boolean

from . import BASE, SESSION

class ReportingSettings(BASE):
    __tablename__ = "chat_reporting"
    chat_id = Column(String(14), primary_key=True)
    should_report = Column(Boolean, default=True)

    def __init__(self, chat_id: Union[str, int], should_report: bool):
        self.chat_id = str(chat_id)
        self.should_report = should_report

    def __repr__(self):
        return f"<Chat report settings ({self.chat_id}) is {self.should_report}>"

CHAT_LOCK = threading.RLock()

def chat_should_report(chat_id: Union[str, int]) -> bool:
    try:
        chat_setting = SESSION.query(ReportingSettings).get(str(chat_id))
        if chat_setting:
            return chat_setting.should_report
        return True  # Default: True
    finally:
        SESSION.close()

def set_chat_setting(chat_id: Union[str, int], setting: bool) -> bool:
    with CHAT_LOCK:
        try:
            chat_setting = SESSION.query(ReportingSettings).get(str(chat_id))
            if not chat_setting:
                chat_setting = ReportingSettings(chat_id, setting)
            else:
                chat_setting.should_report = setting

            SESSION.add(chat_setting)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with CHAT_LOCK:
        chat_settings = SESSION.query(ReportingSettings).get(str(old_chat_id))
        if chat_settings:
            chat_settings.chat_id = str(new_chat_id)
            SESSION.add(chat_settings)
            SESSION.commit() 
