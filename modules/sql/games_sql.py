import threading
from typing import Union

from sqlalchemy import Column, String, Integer, UnicodeText, func, distinct

from . import BASE, SESSION

class GameScore(BASE):
    __tablename__ = "game_scores"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(String(14), primary_key=True)
    game_name = Column(String(64), primary_key=True)
    score = Column(Integer, default=0)
    last_played = Column(Integer)

    def __init__(self, chat_id, user_id, game_name, score=0, last_played=0):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = str(user_id)
        self.game_name = game_name
        self.score = score
        self.last_played = last_played

    def __repr__(self):
        return f"<Game {self.game_name} score for {self.user_id} in {self.chat_id}: {self.score}>"

INSERTION_LOCK = threading.RLock()

def update_score(chat_id: Union[str, int], user_id: Union[str, int], game_name: str, score: int, last_played: int) -> bool:
    with INSERTION_LOCK:
        try:
            game_score = SESSION.query(GameScore).get((str(chat_id), str(user_id), game_name))
            if not game_score:
                game_score = GameScore(chat_id, user_id, game_name)

            game_score.score = score
            game_score.last_played = last_played

            SESSION.add(game_score)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def get_score(chat_id: Union[str, int], user_id: Union[str, int], game_name: str) -> tuple[int, int]:
    try:
        game_score = SESSION.query(GameScore).get((str(chat_id), str(user_id), game_name))
        if game_score:
            return game_score.score, game_score.last_played
        return 0, 0
    finally:
        SESSION.close()

def get_game_scores(chat_id: Union[str, int], game_name: str) -> list:
    try:
        return (
            SESSION.query(GameScore)
            .filter(
                GameScore.chat_id == str(chat_id),
                GameScore.game_name == game_name
            )
            .order_by(GameScore.score.desc())
            .all()
        )
    finally:
        SESSION.close()

def reset_score(chat_id: Union[str, int], user_id: Union[str, int], game_name: str = None):
    with INSERTION_LOCK:
        try:
            if game_name:
                game_score = SESSION.query(GameScore).get((str(chat_id), str(user_id), game_name))
                if game_score:
                    SESSION.delete(game_score)
            else:
                game_scores = (
                    SESSION.query(GameScore)
                    .filter(
                        GameScore.chat_id == str(chat_id),
                        GameScore.user_id == str(user_id)
                    )
                    .all()
                )
                for score in game_scores:
                    SESSION.delete(score)
            SESSION.commit()
            return True
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def migrate_chat(old_chat_id: Union[str, int], new_chat_id: Union[str, int]):
    with INSERTION_LOCK:
        chat_scores = (
            SESSION.query(GameScore)
            .filter(GameScore.chat_id == str(old_chat_id))
            .all()
        )
        for score in chat_scores:
            score.chat_id = str(new_chat_id)
        SESSION.commit() 
