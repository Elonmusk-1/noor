import threading
from typing import Union
from datetime import datetime

from sqlalchemy import Column, String, Integer, UnicodeText, func, distinct

from . import BASE, SESSION

class MessageStats(BASE):
    __tablename__ = "message_stats"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    message_type = Column(String(20), primary_key=True)
    count = Column(Integer, default=0)
    last_update = Column(Integer)

    def __init__(self, chat_id, user_id, message_type):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = str(user_id)
        self.message_type = message_type
        self.count = 0
        self.last_update = int(datetime.now().timestamp())

    def __repr__(self):
        return f"<MessageStats {self.message_type} from {self.user_id} in {self.chat_id}>"

class WordStats(BASE):
    __tablename__ = "word_stats"
    chat_id = Column(String(14), primary_key=True)
    word = Column(String(50), primary_key=True)
    count = Column(Integer, default=0)
    
    def __init__(self, chat_id, word):
        self.chat_id = str(chat_id)
        self.word = word
        self.count = 0

    def __repr__(self):
        return f"<WordStats {self.word} in {self.chat_id}: {self.count}>"

STATS_LOCK = threading.RLock()

def increment_message_stats(chat_id: Union[str, int], user_id: Union[str, int], message_type: str) -> int:
    with STATS_LOCK:
        try:
            stats = SESSION.query(MessageStats).get((str(chat_id), str(user_id), message_type))
            if not stats:
                stats = MessageStats(chat_id, user_id, message_type)

            stats.count += 1
            stats.last_update = int(datetime.now().timestamp())

            SESSION.add(stats)
            SESSION.commit()
            return stats.count
        except:
            SESSION.rollback()
            return 0
        finally:
            SESSION.close()

def get_user_stats(chat_id: Union[str, int], user_id: Union[str, int]) -> list:
    try:
        return (
            SESSION.query(MessageStats)
            .filter(
                MessageStats.chat_id == str(chat_id),
                MessageStats.user_id == str(user_id)
            )
            .all()
        )
    finally:
        SESSION.close()

def get_chat_stats(chat_id: Union[str, int]) -> list:
    try:
        return (
            SESSION.query(MessageStats)
            .filter(MessageStats.chat_id == str(chat_id))
            .all()
        )
    finally:
        SESSION.close()

def get_overall_stats() -> dict:
    try:
        total_messages = SESSION.query(func.sum(MessageStats.count)).scalar() or 0
        total_users = SESSION.query(func.count(distinct(MessageStats.user_id))).scalar() or 0
        total_chats = SESSION.query(func.count(distinct(MessageStats.chat_id))).scalar() or 0
        
        return {
            "messages": total_messages,
            "users": total_users,
            "chats": total_chats
        }
    finally:
        SESSION.close()

def reset_stats(chat_id: Union[str, int] = None, user_id: Union[str, int] = None):
    with STATS_LOCK:
        try:
            if chat_id and user_id:
                stats = (
                    SESSION.query(MessageStats)
                    .filter(
                        MessageStats.chat_id == str(chat_id),
                        MessageStats.user_id == str(user_id)
                    )
                    .all()
                )
            elif chat_id:
                stats = (
                    SESSION.query(MessageStats)
                    .filter(MessageStats.chat_id == str(chat_id))
                    .all()
                )
            else:
                stats = SESSION.query(MessageStats).all()

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
        chat_stats = (
            SESSION.query(MessageStats)
            .filter(MessageStats.chat_id == str(old_chat_id))
            .all()
        )
        for stat in chat_stats:
            stat.chat_id = str(new_chat_id)
        SESSION.commit()

def update_message_stats(chat_id: str, user_id: int, date: str):
    with SESSION() as session:
        stat = session.query(MessageStats).get((str(chat_id), user_id, date))
        if not stat:
            stat = MessageStats(chat_id, user_id, date)
            
        stat.message_count += 1
        session.add(stat)
        session.commit()

def update_word_stats(chat_id: str, words: list):
    with SESSION() as session:
        for word in words:
            if len(word) > 50:  # Skip very long words
                continue
                
            stat = session.query(WordStats).get((str(chat_id), word))
            if not stat:
                stat = WordStats(chat_id, word)
                
            stat.count += 1
            session.add(stat)
        session.commit()

def get_chat_stats(chat_id: str, days: int = 7) -> dict:
    with SESSION() as session:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Get daily message counts
        daily_stats = session.query(
            MessageStats.date,
            func.sum(MessageStats.message_count).label('total')
        ).filter(
            MessageStats.chat_id == str(chat_id),
            MessageStats.date >= start_date
        ).group_by(MessageStats.date).all()
        
        # Get top users
        top_users = session.query(
            MessageStats.user_id,
            func.sum(MessageStats.message_count).label('total')
        ).filter(
            MessageStats.chat_id == str(chat_id),
            MessageStats.date >= start_date
        ).group_by(MessageStats.user_id).order_by(
            func.sum(MessageStats.message_count).desc()
        ).limit(10).all()
        
        return {
            'daily_stats': daily_stats,
            'top_users': top_users
        }

def get_word_cloud_data(chat_id: str, limit: int = 100) -> list:
    with SESSION() as session:
        return session.query(WordStats).filter(
            WordStats.chat_id == str(chat_id)
        ).order_by(WordStats.count.desc()).limit(limit).all() 
