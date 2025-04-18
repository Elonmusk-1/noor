import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText, Integer, Boolean, func, distinct

from . import BASE, SESSION

class Federations(BASE):
    __tablename__ = "feds"
    owner_id = Column(String(14))
    fed_name = Column(UnicodeText)
    fed_id = Column(String(14), primary_key=True)
    fed_rules = Column(UnicodeText)
    fed_log = Column(UnicodeText)
    fed_users = Column(UnicodeText)

    def __init__(self, owner_id, fed_name, fed_id, fed_rules, fed_log, fed_users):
        self.owner_id = owner_id
        self.fed_name = fed_name
        self.fed_id = fed_id
        self.fed_rules = fed_rules
        self.fed_log = fed_log
        self.fed_users = fed_users

class ChatF(BASE):
    __tablename__ = "chat_feds"
    chat_id = Column(String(14), primary_key=True)
    fed_id = Column(String(14))

    def __init__(self, chat_id, fed_id):
        self.chat_id = chat_id
        self.fed_id = fed_id

class BansF(BASE):
    __tablename__ = "bans_feds"
    fed_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    first_name = Column(UnicodeText)
    reason = Column(UnicodeText)

    def __init__(self, fed_id, user_id, first_name, reason):
        self.fed_id = fed_id
        self.user_id = user_id
        self.first_name = first_name
        self.reason = reason

FEDS_LOCK = threading.RLock()
CHAT_FEDS_LOCK = threading.RLock()
FEDS_SETTINGS_LOCK = threading.RLock()

def get_fed_info(fed_id):
    try:
        return SESSION.query(Federations).get(str(fed_id))
    finally:
        SESSION.close()

def get_fed_id(chat_id):
    try:
        chat = SESSION.query(ChatF).get(str(chat_id))
        if chat:
            return chat.fed_id
        return None
    finally:
        SESSION.close()

def new_fed(owner_id, fed_name, fed_id):
    with FEDS_LOCK:
        fed = Federations(
            str(owner_id),
            fed_name,
            str(fed_id),
            'Rules is not set in this federation.',
            None,
            str({owner_id: {'first_name': 'Fed Owner'}}),
        )
        SESSION.add(fed)
        SESSION.commit()

def del_fed(fed_id):
    with FEDS_LOCK:
        fed = SESSION.query(Federations).get(str(fed_id))
        if fed:
            SESSION.delete(fed)
        SESSION.commit()
        return True
    return False

def chat_join_fed(fed_id, chat_id):
    with CHAT_FEDS_LOCK:
        chat_fed = ChatF(str(chat_id), str(fed_id))
        SESSION.add(chat_fed)
        SESSION.commit()

def chat_leave_fed(chat_id):
    with CHAT_FEDS_LOCK:
        chat_fed = SESSION.query(ChatF).get(str(chat_id))
        if chat_fed:
            SESSION.delete(chat_fed)
            SESSION.commit()

def user_join_fed(fed_id, user_id):
    with FEDS_SETTINGS_LOCK:
        fed = SESSION.query(Federations).get(fed_id)
        if fed:
            users = eval(fed.fed_users) if fed.fed_users else {}
            users[user_id] = {'first_name': 'Fed Admin'}
            fed.fed_users = str(users)
            SESSION.add(fed)
            SESSION.commit()
            return True
    return False

def user_demote_fed(fed_id, user_id):
    with FEDS_SETTINGS_LOCK:
        fed = SESSION.query(Federations).get(fed_id)
        if fed:
            users = eval(fed.fed_users)
            if user_id in users:
                del users[user_id]
                fed.fed_users = str(users)
                SESSION.add(fed)
                SESSION.commit()
                return True
    return False

def get_all_fed_chats(fed_id):
    try:
        return SESSION.query(ChatF).filter(ChatF.fed_id == str(fed_id)).all()
    finally:
        SESSION.close()

def get_all_fed_users(fed_id):
    try:
        fed = SESSION.query(Federations).get(fed_id)
        if fed:
            return eval(fed.fed_users)
        return {}
    finally:
        SESSION.close()

def get_all_feds():
    try:
        return SESSION.query(Federations).all()
    finally:
        SESSION.close()

def is_user_fed_admin(fed_id, user_id):
    try:
        fed = SESSION.query(Federations).get(fed_id)
        if fed:
            users = eval(fed.fed_users)
            return str(user_id) in users
        return False
    finally:
        SESSION.close()

def get_fed_ban(fed_id, user_id):
    try:
        return SESSION.query(BansF).get((str(fed_id), str(user_id)))
    finally:
        SESSION.close()

def fed_ban_user(fed_id, user_id, first_name, reason=None):
    with FEDS_LOCK:
        ban = BansF(str(fed_id), str(user_id), first_name, reason)
        SESSION.add(ban)
        try:
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False

def un_fed_ban_user(fed_id, user_id):
    with FEDS_LOCK:
        ban = SESSION.query(BansF).get((str(fed_id), str(user_id)))
        if ban:
            SESSION.delete(ban)
            SESSION.commit()
            return True
    return False

def get_all_fed_bans(fed_id):
    try:
        return SESSION.query(BansF).filter(BansF.fed_id == str(fed_id)).all()
    finally:
        SESSION.close() 
