import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText, Boolean, Integer, distinct, func
from . import BASE, SESSION

class Notes(BASE):
    __tablename__ = "notes"
    chat_id = Column(String(14), primary_key=True)
    name = Column(String(512), primary_key=True)
    value = Column(UnicodeText, nullable=False)
    file = Column(UnicodeText)
    is_reply = Column(Boolean, default=False)
    has_buttons = Column(Boolean, default=False)
    msgtype = Column(Integer, default=1)

    def __init__(self, chat_id, name, value, msgtype, file=None, is_reply=False, has_buttons=False):
        self.chat_id = str(chat_id)  # ensure string
        self.name = name
        self.value = value
        self.msgtype = msgtype
        self.file = file
        self.is_reply = is_reply
        self.has_buttons = has_buttons

    def __repr__(self):
        return f"<Note {self.name} for {self.chat_id}>"

NOTES_LOCK = threading.RLock()

def add_note(chat_id: Union[str, int], name: str, value: str, msgtype: int, 
            file: str = None, is_reply: bool = False, has_buttons: bool = False) -> bool:
    with NOTES_LOCK:
        try:
            note = Notes(str(chat_id), name, value, msgtype, file, is_reply, has_buttons)
            SESSION.add(note)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_note(chat_id: Union[str, int], name: str) -> Notes:
    try:
        return SESSION.query(Notes).get((str(chat_id), name))
    finally:
        SESSION.close()

def rm_note(chat_id: Union[str, int], name: str) -> bool:
    with NOTES_LOCK:
        try:
            note = SESSION.query(Notes).get((str(chat_id), name))
            if note:
                SESSION.delete(note)
                SESSION.commit()
                return True
            return False
        except:
            return False
        finally:
            SESSION.close()

def get_all_chat_notes(chat_id: Union[str, int]) -> list:
    try:
        return SESSION.query(Notes).filter(Notes.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()

def num_notes() -> int:
    try:
        return SESSION.query(Notes).count()
    finally:
        SESSION.close()

def num_chats() -> int:
    try:
        return SESSION.query(func.count(distinct(Notes.chat_id))).scalar()
    finally:
        SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]) -> None:
    with NOTES_LOCK:
        chat_notes = SESSION.query(Notes).filter(Notes.chat_id == str(old_chat_id)).all()
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        SESSION.commit() 
