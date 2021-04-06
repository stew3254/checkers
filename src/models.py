import os
from datetime import datetime
import sqlalchemy as sqla
from sqlalchemy.orm import relation, backref, Session
from base64 import b64encode as encode
from sqlalchemy.ext.declarative import declarative_base

# Define the base for everything to derive from
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = sqla.Column("id", sqla.String, primary_key=True)
    last_played = sqla.Column("last_played", sqla.DateTime, default=datetime.utcnow())
    last_ip = sqla.Column("last_ip", sqla.String)

    def __init__(self, user_id=None, last_played=None, last_ip=None):
        self.id = user_id
        self.last_played = last_played
        self.last_ip = last_ip

    def exists(self, session: Session):
        return session.query(sqla.exists().where(User.id == self.id)).scalar()

    def create_unique(self, session: Session, user_id=None, last_played=None, last_ip=None):
        self.last_played = last_played
        self.last_ip = last_ip
        exists = True
        while exists:
            exists = self.exists(session)
            self.id = user_id or encode(os.urandom(32)).decode()
        return self


class Piece(Base):
    __tablename__ = "pieces"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    column = sqla.Column("column", sqla.String(1))
    row = sqla.Column("row", sqla.SmallInteger)
    king = sqla.Column("king", sqla.Boolean)
    owner_id = sqla.Column("owner", sqla.ForeignKey("users.id"), index=True)
    owner = relation(User, backref=backref("pieces", lazy="joined"))


class Score(Base):
    __tablename__ = "scores"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    wins = sqla.Column("wins", sqla.Integer)
    losses = sqla.Column("losses", sqla.Integer)
    ties = sqla.Column("ties", sqla.Integer)
    user_id = sqla.Column("user_id", sqla.ForeignKey("users.id"), index=True)
    user = relation(User, backref=backref("scores", lazy="joined"))


class BoardState(Base):
    __tablename__ = "board_states"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    game_id = sqla.Column("game_id", sqla.Integer)
    piece_id = sqla.Column("game_id", sqla.Integer, sqla.ForeignKey("pieces.id"))
