import threading
import logging
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import Column, Integer, String
from . import BASE, SESSION

DEF_COUNT = 0
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)

logger = logging.getLogger(__name__)

class FloodControl(BASE):
    __tablename__ = "antiflood"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(Integer)
    count = Column(Integer, default=0)
    limit = Column(Integer, default=0)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return f"<flood control for {self.chat_id}>"

INSERTION_LOCK = threading.RLock()

def check_flood(chat_id, user_id):
    if not SESSION:
        logger.error("No database session available")
        return None
        
    try:
        flood = SESSION.query(FloodControl).get(str(chat_id))
        if not flood:
            flood = FloodControl(str(chat_id))

        flood.user_id = user_id
        flood.count += 1
        SESSION.add(flood)
        SESSION.commit()
        return flood
    except SQLAlchemyError as e:
        logger.error(f"Database error in check_flood: {e}")
        SESSION.rollback()
        return None
    finally:
        SESSION.close()

def get_flood_limit(chat_id):
    try:
        return SESSION.query(FloodControl).get(str(chat_id))
    finally:
        SESSION.close()

def set_flood(chat_id, amount):
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(chat_id))
        if not flood:
            flood = FloodControl(str(chat_id))

        flood.user_id = None
        flood.limit = amount

        SESSION.add(flood)
        SESSION.commit()

def update_flood(chat_id: str, user_id: int) -> bool:
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(chat_id))
        if not flood:
            return False

        flood.user_id = user_id
        flood.count += 1

        if flood.count > flood.limit:
            SESSION.delete(flood)
            SESSION.commit()
            return True

        SESSION.add(flood)
        SESSION.commit()
        return False

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        flood = SESSION.query(FloodControl).get(str(old_chat_id))
        if flood:
            flood.chat_id = str(new_chat_id)
            SESSION.add(flood)

        SESSION.commit() 
