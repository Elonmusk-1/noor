import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText

from . import BASE, SESSION

class BlackListFilters(BASE):
    __tablename__ = "blacklist"
    chat_id = Column(String(14), primary_key=True)
    trigger = Column(UnicodeText, primary_key=True)

    def __init__(self, chat_id, trigger):
        self.chat_id = str(chat_id)  # ensure string
        self.trigger = trigger

    def __repr__(self):
        return f"<Blacklist filter '{self.trigger}' for {self.chat_id}>"

BLACKLIST_LOCK = threading.RLock()

def add_to_blacklist(chat_id: Union[str, int], trigger: str) -> bool:
    with BLACKLIST_LOCK:
        try:
            blacklist_filter = BlackListFilters(str(chat_id), trigger)
            SESSION.merge(blacklist_filter)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def rm_from_blacklist(chat_id: Union[str, int], trigger: str) -> bool:
    with BLACKLIST_LOCK:
        try:
            blacklist_filter = SESSION.query(BlackListFilters).get((str(chat_id), trigger))
            if blacklist_filter:
                SESSION.delete(blacklist_filter)
                SESSION.commit()
                return True
            return False
        except:
            return False
        finally:
            SESSION.close()

def get_chat_blacklist(chat_id: Union[str, int]) -> list:
    try:
        return [x.trigger for x in SESSION.query(BlackListFilters).filter(BlackListFilters.chat_id == str(chat_id)).all()]
    finally:
        SESSION.close()

def num_blacklist_filters() -> int:
    try:
        return SESSION.query(BlackListFilters).count()
    finally:
        SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]) -> None:
    with BLACKLIST_LOCK:
        chat_filters = SESSION.query(BlackListFilters).filter(BlackListFilters.chat_id == str(old_chat_id)).all()
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit() 
