import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText, Integer, Boolean

from . import BASE, SESSION

class SpamCheck(BASE):
    __tablename__ = "spamcheck"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    message_count = Column(Integer, default=0)
    last_check = Column(Integer)
    is_spammer = Column(Boolean, default=False)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)
        self.user_id = str(user_id)
        self.message_count = 0
        self.last_check = 0
        self.is_spammer = False

    def __repr__(self):
        return f"<Spam check for {self.user_id} in {self.chat_id}>"

INSERTION_LOCK = threading.RLock()

def check_user(chat_id: Union[str, int], user_id: Union[str, int], time: int) -> tuple[int, bool]:
    with INSERTION_LOCK:
        user = SESSION.query(SpamCheck).get((str(chat_id), str(user_id)))
        if not user:
            user = SpamCheck(str(chat_id), str(user_id))
            SESSION.add(user)

        # Reset count if more than 3 seconds passed
        if time - user.last_check >= 3:
            user.message_count = 0
            user.is_spammer = False
        
        user.message_count += 1
        user.last_check = time
        
        # Mark as spammer if more than 10 messages in 3 seconds
        if user.message_count >= 10:
            user.is_spammer = True
        
        SESSION.commit()
        return user.message_count, user.is_spammer

def is_spammer(chat_id: Union[str, int], user_id: Union[str, int]) -> bool:
    try:
        user = SESSION.query(SpamCheck).get((str(chat_id), str(user_id)))
        return bool(user and user.is_spammer)
    finally:
        SESSION.close()

def reset_spammer(chat_id: Union[str, int], user_id: Union[str, int]):
    with INSERTION_LOCK:
        user = SESSION.query(SpamCheck).get((str(chat_id), str(user_id)))
        if user:
            user.message_count = 0
            user.is_spammer = False
            SESSION.commit()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with INSERTION_LOCK:
        chat_filters = (
            SESSION.query(SpamCheck)
            .filter(SpamCheck.chat_id == str(old_chat_id))
            .all()
        )
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit() 
