import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText, Boolean, Integer, distinct, func
from . import BASE, SESSION

class Filters(BASE):
    __tablename__ = "filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True)
    reply = Column(UnicodeText)
    is_sticker = Column(Boolean, default=False)
    is_document = Column(Boolean, default=False)
    is_image = Column(Boolean, default=False)
    is_video = Column(Boolean, default=False)
    is_audio = Column(Boolean, default=False)
    is_voice = Column(Boolean, default=False)
    is_video_note = Column(Boolean, default=False)

    has_buttons = Column(Boolean, default=False)
    # NOTE: Here for legacy purposes, to ensure older filters don't mess up.
    has_markdown = Column(Boolean, default=False)

    def __init__(self, chat_id, keyword, reply, is_sticker=False, is_document=False, is_image=False, is_video=False, 
                 is_audio=False, is_voice=False, is_video_note=False, has_buttons=False):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply
        self.is_sticker = is_sticker
        self.is_document = is_document
        self.is_image = is_image
        self.is_video = is_video
        self.is_audio = is_audio
        self.is_voice = is_voice
        self.is_video_note = is_video_note
        self.has_buttons = has_buttons
        self.has_markdown = True

    def __repr__(self):
        return f"<Filter for {self.chat_id} - {self.keyword}>"

class FilterButtons(BASE):
    __tablename__ = "filter_urls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, keyword, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.keyword = keyword
        self.name = name
        self.url = url
        self.same_line = same_line

# Note: Don't create tables here, they are created in __init__.py
# Remove these lines:
# Filters.__table__.create(checkfirst=True)
# FilterButtons.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()

def get_all_filters(chat_id):
    try:
        return SESSION.query(Filters).filter(Filters.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()

def add_filter(
    chat_id,
    keyword,
    reply,
    is_sticker=False,
    is_document=False,
    is_image=False,
    is_audio=False,
    is_voice=False,
    is_video=False,
    buttons=None,
):
    with INSERTION_LOCK:
        prev = SESSION.query(Filters).get((str(chat_id), keyword))
        if prev:
            with INSERTION_LOCK:
                SESSION.delete(prev)
                SESSION.commit()

        filt = Filters(
            str(chat_id),
            keyword,
            reply,
            is_sticker,
            is_document,
            is_image,
            is_audio,
            is_voice,
            is_video,
            bool(buttons),
        )

        SESSION.add(filt)
        SESSION.commit()

def remove_filter(chat_id, keyword):
    with INSERTION_LOCK:
        filt = SESSION.query(Filters).get((str(chat_id), keyword))
        if filt:
            SESSION.delete(filt)
            SESSION.commit()
            return True
        SESSION.close()
        return False

def get_filter(chat_id, keyword):
    try:
        return SESSION.query(Filters).get((str(chat_id), keyword))
    finally:
        SESSION.close()

def get_filter_buttons(chat_id, keyword):
    try:
        return (
            SESSION.query(FilterButtons)
            .filter(
                FilterButtons.chat_id == str(chat_id),
                FilterButtons.keyword == keyword,
            )
            .order_by(FilterButtons.id)
            .all()
        )
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat_filters = (
            SESSION.query(Filters)
            .filter(Filters.chat_id == str(old_chat_id))
            .all()
        )
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit() 
