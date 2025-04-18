import threading
from typing import Union

from sqlalchemy import Column, String, UnicodeText, Integer, func
from . import BASE, SESSION
import json
from datetime import datetime

class Backup(BASE):
    __tablename__ = "backups"
    chat_id = Column(String(14), primary_key=True)
    backup_name = Column(String(100), primary_key=True)
    data = Column(UnicodeText)
    created_at = Column(Integer)

    def __init__(self, chat_id, backup_name, data, created_at):
        self.chat_id = str(chat_id)  # ensure string
        self.backup_name = backup_name
        self.data = data
        self.created_at = created_at

    def __repr__(self):
        return f"<Backup {self.backup_name} for {self.chat_id}>"

BACKUP_LOCK = threading.RLock()

def save_backup(chat_id: Union[str, int], backup_name: str, data: str, created_at: int) -> bool:
    with BACKUP_LOCK:
        try:
            backup = SESSION.query(Backup).get((str(chat_id), backup_name))
            if backup:
                backup.data = data
                backup.created_at = created_at
            else:
                backup = Backup(chat_id, backup_name, data, created_at)
            
            SESSION.add(backup)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_backup(chat_id: Union[str, int], backup_name: str) -> Union[str, None]:
    try:
        backup = SESSION.query(Backup).get((str(chat_id), backup_name))
        return backup.data if backup else None
    finally:
        SESSION.close()

def get_backups(chat_id: Union[str, int]) -> list:
    try:
        return (
            SESSION.query(Backup)
            .filter(Backup.chat_id == str(chat_id))
            .order_by(Backup.created_at.desc())
            .all()
        )
    finally:
        SESSION.close()

def delete_backup(chat_id: Union[str, int], backup_name: str) -> bool:
    with BACKUP_LOCK:
        try:
            backup = SESSION.query(Backup).get((str(chat_id), backup_name))
            if backup:
                SESSION.delete(backup)
                SESSION.commit()
                return True
            return False
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with BACKUP_LOCK:
        chat_backups = (
            SESSION.query(Backup)
            .filter(Backup.chat_id == str(old_chat_id))
            .all()
        )
        for backup in chat_backups:
            backup.chat_id = str(new_chat_id)
        SESSION.commit() 
