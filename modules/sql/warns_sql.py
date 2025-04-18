import threading
from typing import Union

from sqlalchemy import Column, String, Integer, UnicodeText, Boolean, func, distinct

from . import BASE, SESSION

class Warns(BASE):
    __tablename__ = "warns"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(Integer, primary_key=True)
    num_warns = Column(Integer, default=0)
    reasons = Column(UnicodeText)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = user_id
        self.num_warns = 0
        self.reasons = ""

    def __repr__(self):
        return f"<{self.chat_id} warns for {self.user_id}: {self.num_warns}>"

class WarnSettings(BASE):
    __tablename__ = "warn_settings"
    chat_id = Column(String(14), primary_key=True)
    warn_limit = Column(Integer, default=3)
    soft_warn = Column(Boolean, default=False)

    def __init__(self, chat_id, warn_limit=3, soft_warn=False):
        self.chat_id = str(chat_id)
        self.warn_limit = warn_limit
        self.soft_warn = soft_warn

    def __repr__(self):
        return f"<{self.chat_id} has {self.warn_limit} possible warns>"

# Note: Don't create tables here, they are created in __init__.py
# Remove these lines:
# Warns.__table__.create(checkfirst=True)
# WarnSettings.__table__.create(checkfirst=True)

WARN_INSERTION_LOCK = threading.RLock()
SETTINGS_INSERTION_LOCK = threading.RLock()

def warn_user(chat_id: Union[str, int], user_id: int, reason: str = "") -> int:
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((str(chat_id), user_id))
        if not warned_user:
            warned_user = Warns(str(chat_id), user_id)

        warned_user.num_warns += 1
        if reason:
            warned_user.reasons = (
                f"{warned_user.reasons}\n{warned_user.num_warns}: {reason}"
            ).strip()

        SESSION.add(warned_user)
        SESSION.commit()

        return warned_user.num_warns

def remove_warn(chat_id: Union[str, int], user_id: int) -> bool:
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((str(chat_id), user_id))
        if not warned_user or warned_user.num_warns == 0:
            return False

        warned_user.num_warns -= 1
        SESSION.add(warned_user)
        SESSION.commit()

        return True

def reset_warns(chat_id: Union[str, int], user_id: int) -> bool:
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((str(chat_id), user_id))
        if not warned_user:
            return False

        warned_user.num_warns = 0
        warned_user.reasons = ""

        SESSION.add(warned_user)
        SESSION.commit()

        return True

def get_warns(chat_id: Union[str, int], user_id: int) -> tuple[int, str]:
    warned_user = SESSION.query(Warns).get((str(chat_id), user_id))
    if not warned_user:
        return 0, ""

    return warned_user.num_warns, warned_user.reasons

def set_warn_limit(chat_id: Union[str, int], warn_limit: int) -> bool:
    with SETTINGS_INSERTION_LOCK:
        settings = SESSION.query(WarnSettings).get(str(chat_id))
        if not settings:
            settings = WarnSettings(chat_id, warn_limit=warn_limit)

        settings.warn_limit = warn_limit
        SESSION.add(settings)
        SESSION.commit()

        return True

def set_warn_mode(chat_id: Union[str, int], soft_warn: bool) -> bool:
    with SETTINGS_INSERTION_LOCK:
        settings = SESSION.query(WarnSettings).get(str(chat_id))
        if not settings:
            settings = WarnSettings(chat_id, soft_warn=soft_warn)

        settings.soft_warn = soft_warn
        SESSION.add(settings)
        SESSION.commit()

        return True

def get_warn_settings(chat_id: Union[str, int]) -> tuple[int, bool]:
    settings = SESSION.query(WarnSettings).get(str(chat_id))
    if not settings:
        return 3, False  # Default values

    return settings.warn_limit, settings.soft_warn

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with WARN_INSERTION_LOCK:
        chat_notes = (
            SESSION.query(Warns).filter(Warns.chat_id == str(old_chat_id)).all()
        )
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        SESSION.commit()

    with SETTINGS_INSERTION_LOCK:
        chat_settings = (
            SESSION.query(WarnSettings)
            .filter(WarnSettings.chat_id == str(old_chat_id))
            .first()
        )
        if chat_settings:
            chat_settings.chat_id = str(new_chat_id)
            SESSION.commit() 
