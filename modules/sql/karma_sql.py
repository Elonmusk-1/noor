import threading
from typing import Union, List, Tuple, Optional
import logging
from sqlalchemy import Column, String, Integer, UnicodeText, func

from .base import BASE, SESSION, engine  # Import from base instead of __init__

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Karma(BASE):
    __tablename__ = "karma"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    karma_count = Column(Integer, default=0)
    reason = Column(UnicodeText)

    def __init__(self, chat_id, user_id, karma_count=0, reason=""):
        self.chat_id = str(chat_id)
        self.user_id = str(user_id)
        self.karma_count = karma_count
        self.reason = reason

    def __repr__(self):
        return f"<Karma for {self.user_id} in {self.chat_id}: {self.karma_count}>"

KARMA_LOCK = threading.RLock()

def update_karma(chat_id: Union[str, int], user_id: Union[str, int], karma_diff: int = 1) -> Optional[Tuple[int, int]]:
    """Update a user's karma count. Returns (old_karma, new_karma) or None on error"""
    with KARMA_LOCK:
        try:
            chat_id, user_id = str(chat_id), str(user_id)
            karma = SESSION.query(Karma).get((chat_id, user_id))
            
            if not karma:
                karma = Karma(chat_id=chat_id, user_id=user_id)
                SESSION.add(karma)
            
            old_karma = karma.karma_count
            karma.karma_count += karma_diff
            
            SESSION.commit()
            return old_karma, karma.karma_count
            
        except Exception as e:
            logger.error(f"Error updating karma: {str(e)}")
            SESSION.rollback()
            return None
        finally:
            SESSION.close()

def get_karma(chat_id: Union[str, int], user_id: Union[str, int]) -> int:
    """Get a user's current karma count"""
    try:
        karma = SESSION.query(Karma).get((str(chat_id), str(user_id)))
        return karma.karma_count if karma else 0
    finally:
        SESSION.close()

def get_chat_karma(chat_id: Union[str, int]) -> list:
    try:
        return (
            SESSION.query(Karma)
            .filter(Karma.chat_id == str(chat_id))
            .order_by(Karma.karma_count.desc())
            .all()
        )
    finally:
        SESSION.close()

def reset_karma(chat_id: Union[str, int], user_id: Union[str, int]) -> bool:
    """Reset a user's karma to 0"""
    with KARMA_LOCK:
        try:
            karma = SESSION.query(Karma).get((str(chat_id), str(user_id)))
            if karma:
                karma.karma_count = 0
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]) -> None:
    """Migrate karma data when chat ID changes"""
    with KARMA_LOCK:
        karma_items = (
            SESSION.query(Karma)
            .filter(Karma.chat_id == str(old_chat_id))
            .all()
        )
        for item in karma_items:
            item.chat_id = str(new_chat_id)
        SESSION.commit()

def ensure_tables_exist():
    """Ensure all required tables exist"""
    try:
        if not engine:
            logger.error("No database engine available")
            return False
        BASE.metadata.create_all(engine)
        return True
    except Exception as e:
        logger.error(f"Error creating karma tables: {e}")
        return False

def get_chat_karma_list(chat_id: Union[str, int], limit: int = 10) -> list:
    """Get the karma leaderboard for a chat"""
    try:
        return (
            SESSION.query(Karma)
            .filter(Karma.chat_id == str(chat_id))
            .order_by(Karma.karma_count.desc())
            .limit(limit)
            .all()
        )
    finally:
        SESSION.close()

def get_karma_leaderboard(chat_id: int, limit: int = 10) -> List[Tuple[int, int]]:
    """Get top karma users for a chat"""
    try:
        query = SESSION.query(Karma.user_id, Karma.karma_count)\
            .filter(Karma.chat_id == str(chat_id))\
            .order_by(Karma.karma_count.desc())\
            .limit(limit)
        return [(int(uid), count) for uid, count in query.all()]
    except Exception as e:
        logger.error(f"Error getting karma leaderboard: {e}")
        return []
    finally:
        SESSION.close()

# Call this when module is loaded
ensure_tables_exist() 

