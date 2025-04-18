import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText, Integer, Boolean
from . import BASE, SESSION
from datetime import datetime, timedelta

class Reminder(BASE):
    __tablename__ = "reminders"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    reminder_time = Column(Integer)
    reminder_message = Column(UnicodeText)
    has_alert = Column(Boolean, default=True)

    def __init__(self, chat_id, user_id, reminder_time, reminder_message, has_alert=True):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = str(user_id)
        self.reminder_time = reminder_time
        self.reminder_message = reminder_message
        self.has_alert = has_alert

    def __repr__(self):
        return f"<Reminder {self.reminder_message} at {self.reminder_time}>"

REMINDER_LOCK = threading.RLock()

def add_reminder(chat_id: Union[str, int], user_id: Union[str, int], 
                reminder_time: int, reminder_message: str, has_alert: bool = True) -> bool:
    with REMINDER_LOCK:
        try:
            reminder = Reminder(chat_id, user_id, reminder_time, reminder_message, has_alert)
            SESSION.add(reminder)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_reminder(chat_id: Union[str, int], user_id: Union[str, int]) -> Reminder:
    try:
        return SESSION.query(Reminder).get((str(chat_id), str(user_id)))
    finally:
        SESSION.close()

def get_all_reminders() -> list:
    try:
        return SESSION.query(Reminder).all()
    finally:
        SESSION.close()

def remove_reminder(chat_id: Union[str, int], user_id: Union[str, int]) -> bool:
    with REMINDER_LOCK:
        try:
            reminder = SESSION.query(Reminder).get((str(chat_id), str(user_id)))
            if reminder:
                SESSION.delete(reminder)
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_user_reminders(user_id: int) -> list:
    with SESSION() as session:
        return session.query(Reminder).filter(
            Reminder.user_id == str(user_id)
        ).all()

def get_chat_reminders(chat_id: str) -> list:
    with SESSION() as session:
        return session.query(Reminder).filter(
            Reminder.chat_id == str(chat_id)
        ).all()

def get_due_reminders(current_time: int) -> list:
    with SESSION() as session:
        return session.query(Reminder).filter(
            Reminder.reminder_time <= current_time
        ).all()

def update_reminder_time(reminder_id: int, new_time: int):
    with SESSION() as session:
        reminder = session.query(Reminder).get(reminder_id)
        if reminder:
            reminder.reminder_time = new_time
            session.add(reminder)
            session.commit() 
