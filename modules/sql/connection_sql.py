import threading
from typing import Union

from sqlalchemy import Column, String, Boolean, UnicodeText
from . import BASE, SESSION

class Connection(BASE):
    __tablename__ = "connection"
    user_id = Column(String(14), primary_key=True)
    chat_id = Column(String(14))
    
    def __init__(self, user_id, chat_id):
        self.user_id = str(user_id)
        self.chat_id = str(chat_id)

INSERTION_LOCK = threading.RLock()

def add_connection(user_id: Union[str, int], chat_id: Union[str, int]):
    with INSERTION_LOCK:
        try:
            user = SESSION.query(Connection).get(str(user_id))
            if not user:
                user = Connection(str(user_id), str(chat_id))
            else:
                user.chat_id = str(chat_id)

            SESSION.add(user)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_connected_chat(user_id: Union[str, int]) -> str:
    try:
        user = SESSION.query(Connection).get(str(user_id))
        if user:
            return user.chat_id
        return None
    finally:
        SESSION.close()

def remove_connection(user_id: Union[str, int]):
    with INSERTION_LOCK:
        try:
            user = SESSION.query(Connection).get(str(user_id))
            if user:
                SESSION.delete(user)
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def all_connections() -> list:
    try:
        return SESSION.query(Connection).all()
    finally:
        SESSION.close() 
