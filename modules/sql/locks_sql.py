import threading

from sqlalchemy import Column, String, Boolean, UnicodeText

from . import BASE, SESSION

class Locks(BASE):
    __tablename__ = "locks"
    chat_id = Column(String(14), primary_key=True)
    # Booleans are for "is this locked", _NOT_ "is this allowed"
    sticker = Column(Boolean, default=False)
    audio = Column(Boolean, default=False)
    voice = Column(Boolean, default=False)
    document = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    video_note = Column(Boolean, default=False)
    contact = Column(Boolean, default=False)
    photo = Column(Boolean, default=False)
    gif = Column(Boolean, default=False)
    url = Column(Boolean, default=False)
    bots = Column(Boolean, default=False)
    forward = Column(Boolean, default=False)
    game = Column(Boolean, default=False)
    location = Column(Boolean, default=False)
    rtl = Column(Boolean, default=False)
    button = Column(Boolean, default=False)
    egame = Column(Boolean, default=False)
    inline = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.sticker = False
        self.audio = False
        self.voice = False
        self.document = False
        self.video = False
        self.video_note = False
        self.contact = False
        self.photo = False
        self.gif = False
        self.url = False
        self.bots = False
        self.forward = False
        self.game = False
        self.location = False
        self.rtl = False
        self.button = False
        self.egame = False
        self.inline = False

    def __repr__(self):
        return f"<Chat {self.chat_id} locks>"

# Note: Don't create tables here, they are created in __init__.py
# Remove this line:
# Locks.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()

def init_locks(chat_id, reset=False):
    curr_restr = SESSION.query(Locks).get(str(chat_id))
    if reset:
        SESSION.delete(curr_restr)
        SESSION.flush()
    restr = Locks(str(chat_id))
    SESSION.add(restr)
    SESSION.commit()
    return restr

def update_lock(chat_id, lock_type, locked):
    with INSERTION_LOCK:
        curr_perm = SESSION.query(Locks).get(str(chat_id))
        if not curr_perm:
            curr_perm = init_locks(chat_id)

        if lock_type == "sticker":
            curr_perm.sticker = locked
        elif lock_type == "audio":
            curr_perm.audio = locked
        elif lock_type == "voice":
            curr_perm.voice = locked
        elif lock_type == "document":
            curr_perm.document = locked
        elif lock_type == "video":
            curr_perm.video = locked
        elif lock_type == "video_note":
            curr_perm.video_note = locked
        elif lock_type == "contact":
            curr_perm.contact = locked
        elif lock_type == "photo":
            curr_perm.photo = locked
        elif lock_type == "gif":
            curr_perm.gif = locked
        elif lock_type == "url":
            curr_perm.url = locked
        elif lock_type == "bots":
            curr_perm.bots = locked
        elif lock_type == "forward":
            curr_perm.forward = locked
        elif lock_type == "game":
            curr_perm.game = locked
        elif lock_type == "location":
            curr_perm.location = locked
        elif lock_type == "rtl":
            curr_perm.rtl = locked
        elif lock_type == "button":
            curr_perm.button = locked
        elif lock_type == "egame":
            curr_perm.egame = locked
        elif lock_type == "inline":
            curr_perm.inline = locked

        SESSION.add(curr_perm)
        SESSION.commit()

def get_locks(chat_id):
    try:
        return SESSION.query(Locks).get(str(chat_id))
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat_locks = SESSION.query(Locks).get(str(old_chat_id))
        if chat_locks:
            chat_locks.chat_id = str(new_chat_id)
        SESSION.commit() 
