import threading
from typing import Union

from sqlalchemy import Column, String, Integer, UnicodeText, func
from . import BASE, SESSION

class ChatStats(BASE):
    __tablename__ = "chat_stats"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    message_count = Column(Integer, default=0)
    last_message = Column(UnicodeText)
    last_message_time = Column(Integer)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)
        self.user_id = str(user_id)
        self.message_count = 0
        self.last_message = ""
        self.last_message_time = 0

    def __repr__(self):
        return f"<Chat {self.chat_id} stats for {self.user_id}>"

STATS_LOCK = threading.RLock()

def update_user_stats(chat_id: Union[str, int], user_id: Union[str, int], message: str = None, message_time: int = None):
    with STATS_LOCK:
        try:
            stats = SESSION.query(ChatStats).get((str(chat_id), str(user_id)))
            if not stats:
                stats = ChatStats(chat_id, user_id)

            stats.message_count += 1
            if message:
                stats.last_message = message
            if message_time:
                stats.last_message_time = message_time

            SESSION.add(stats)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_user_stats(chat_id: Union[str, int], user_id: Union[str, int]) -> ChatStats:
    try:
        return SESSION.query(ChatStats).get((str(chat_id), str(user_id)))
    finally:
        SESSION.close()

def get_chat_stats(chat_id: Union[str, int]) -> list:
    try:
        return SESSION.query(ChatStats).filter(ChatStats.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()

def get_top_users(chat_id: Union[str, int], limit: int = 10) -> list:
    try:
        return (
            SESSION.query(ChatStats)
            .filter(ChatStats.chat_id == str(chat_id))
            .order_by(ChatStats.message_count.desc())
            .limit(limit)
            .all()
        )
    finally:
        SESSION.close()

def reset_stats(chat_id: Union[str, int]):
    with STATS_LOCK:
        try:
            stats = SESSION.query(ChatStats).filter(ChatStats.chat_id == str(chat_id)).all()
            for stat in stats:
                SESSION.delete(stat)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with STATS_LOCK:
        try:
            stats = (
                SESSION.query(ChatStats)
                .filter(ChatStats.chat_id == str(old_chat_id))
                .all()
            )
            for stat in stats:
                stat.chat_id = str(new_chat_id)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close() 
