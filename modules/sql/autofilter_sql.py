import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText, Boolean

from . import BASE, SESSION

class AutoFilter(BASE):
    __tablename__ = "auto_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True)
    response = Column(UnicodeText)
    is_active = Column(Boolean, default=True)

    def __init__(self, chat_id, keyword, response, is_active=True):
        self.chat_id = str(chat_id)
        self.keyword = keyword
        self.response = response
        self.is_active = is_active

    def __repr__(self):
        return f"<AutoFilter {self.keyword} for {self.chat_id}>"

INSERTION_LOCK = threading.RLock()

def add_filter(chat_id: Union[str, int], keyword: str, response: str) -> bool:
    with INSERTION_LOCK:
        try:
            filter_obj = SESSION.query(AutoFilter).get((str(chat_id), keyword))
            if not filter_obj:
                filter_obj = AutoFilter(chat_id, keyword, response)
            else:
                filter_obj.response = response
                filter_obj.is_active = True

            SESSION.add(filter_obj)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def remove_filter(chat_id: Union[str, int], keyword: str) -> bool:
    with INSERTION_LOCK:
        try:
            filter_obj = SESSION.query(AutoFilter).get((str(chat_id), keyword))
            if filter_obj:
                SESSION.delete(filter_obj)
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_filter(chat_id: Union[str, int], keyword: str) -> str:
    try:
        filter_obj = SESSION.query(AutoFilter).get((str(chat_id), keyword))
        if filter_obj and filter_obj.is_active:
            return filter_obj.response
        return None
    finally:
        SESSION.close()

def get_all_filters(chat_id: Union[str, int]) -> list:
    try:
        return (
            SESSION.query(AutoFilter)
            .filter(AutoFilter.chat_id == str(chat_id), AutoFilter.is_active == True)
            .all()
        )
    finally:
        SESSION.close()

def toggle_filter(chat_id: Union[str, int], keyword: str, active: bool = True) -> bool:
    with INSERTION_LOCK:
        try:
            filter_obj = SESSION.query(AutoFilter).get((str(chat_id), keyword))
            if filter_obj:
                filter_obj.is_active = active
                SESSION.add(filter_obj)
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with INSERTION_LOCK:
        chat_filters = (
            SESSION.query(AutoFilter)
            .filter(AutoFilter.chat_id == str(old_chat_id))
            .all()
        )
        for filter_obj in chat_filters:
            filter_obj.chat_id = str(new_chat_id)
        SESSION.commit() 
