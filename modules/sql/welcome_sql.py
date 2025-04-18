import threading
from typing import Union

from sqlalchemy import Column, String, Boolean, UnicodeText, Integer

from . import BASE, SESSION

class Welcome(BASE):
    __tablename__ = "welcome_settings"
    chat_id = Column(String(14), primary_key=True)
    should_welcome = Column(Boolean, default=True)
    should_goodbye = Column(Boolean, default=True)
    custom_welcome = Column(UnicodeText, default=None)
    custom_goodbye = Column(UnicodeText, default=None)
    welcome_type = Column(Integer, default=0)
    
    def __init__(self, chat_id, should_welcome=True, should_goodbye=True):
        self.chat_id = chat_id
        self.should_welcome = should_welcome
        self.should_goodbye = should_goodbye

    def __repr__(self):
        return f"<Chat {self.chat_id} should Welcome new users: {self.should_welcome}>"

class WelcomeButtons(BASE):
    __tablename__ = "welcome_urls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.name = name
        self.url = url
        self.same_line = same_line

INSERTION_LOCK = threading.RLock()

def get_welcome_settings(chat_id):
    try:
        return SESSION.query(Welcome).get(str(chat_id))
    finally:
        SESSION.close()

def add_welcome_setting(chat_id, should_welcome=True, should_goodbye=True):
    with INSERTION_LOCK:
        chat = SESSION.query(Welcome).get(str(chat_id))
        if not chat:
            chat = Welcome(str(chat_id), should_welcome, should_goodbye)
        else:
            chat.should_welcome = should_welcome
            chat.should_goodbye = should_goodbye

        SESSION.add(chat)
        SESSION.commit()

def set_custom_welcome(chat_id, custom_welcome, welcome_type, buttons=None):
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id))

        if buttons is not None:
            SESSION.query(WelcomeButtons).filter(WelcomeButtons.chat_id == str(chat_id)).delete()
            for btn in buttons:
                new_button = WelcomeButtons(chat_id, btn.name, btn.url, btn.same_line)
                SESSION.add(new_button)

        welcome_settings.custom_welcome = custom_welcome
        welcome_settings.welcome_type = welcome_type

        SESSION.add(welcome_settings)
        SESSION.commit()

def get_custom_welcome(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = ""
    if welcome_settings and welcome_settings.custom_welcome:
        ret = welcome_settings.custom_welcome

    SESSION.close()
    return ret

def set_custom_goodbye(chat_id, custom_goodbye):
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id))

        welcome_settings.custom_goodbye = custom_goodbye
        SESSION.add(welcome_settings)
        SESSION.commit()

def get_custom_goodbye(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = ""
    if welcome_settings and welcome_settings.custom_goodbye:
        ret = welcome_settings.custom_goodbye

    SESSION.close()
    return ret

def get_welcome_buttons(chat_id):
    try:
        return SESSION.query(WelcomeButtons).filter(WelcomeButtons.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Welcome).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)

        SESSION.commit() 
