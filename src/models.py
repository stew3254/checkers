import json
import os
from datetime import datetime
import sqlalchemy as sqla
from sqlalchemy.orm import relation, backref, Session
from base64 import b64encode as encode
from sqlalchemy.ext.declarative import declarative_base

# Define the base for everything to derive from
Base = declarative_base()


class ABC:
    # Make it so the tables pretty print the columns and values as json
    def __repr__(self):
        columns = []
        # Get (hopefully) columns names
        for i in dir(self):
            if not i.startswith("_") and not callable(getattr(self, i)) and i not in ["metadata", "registry"]:
                columns.append(i)
        data = {}
        for column in columns:
            data.update({column: getattr(self, column)})
        return json.dumps(data, indent=2, sort_keys=True)


class User(ABC, Base):
    __tablename__ = "users"
    id = sqla.Column("id", sqla.String, primary_key=True)
    last_played = sqla.Column("last_played", sqla.DateTime, nullable=False, default=datetime.utcnow())
    last_ip = sqla.Column("last_ip", sqla.String, nullable=False)

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


class Piece(ABC, Base):
    __tablename__ = "pieces"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    column = sqla.Column("column", sqla.String(1), nullable=False)
    row = sqla.Column("row", sqla.SmallInteger, nullable=False)
    king = sqla.Column("king", sqla.Boolean, nullable=False)
    owner_id = sqla.Column("owner", sqla.ForeignKey("users.id"), index=True, nullable=False)
    owner = relation(User, backref=backref("pieces", lazy="joined"))

    def __init__(self, column=None, row=None, owner_id=encode(b"ai").decode(), king=False):
        self.column = column
        self.row = row
        self.owner_id = owner_id
        self.king = king


class Score(ABC, Base):
    __tablename__ = "scores"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    wins = sqla.Column("wins", sqla.Integer, nullable=False, default=0)
    losses = sqla.Column("losses", sqla.Integer, nullable=False, default=0)
    ties = sqla.Column("ties", sqla.Integer, nullable=False, default=0)
    user_id = sqla.Column("user_id", sqla.ForeignKey("users.id"), nullable=False, default=True)
    user = relation(User, backref=backref("scores", lazy="joined"))

    def __init__(self, wins=0, losses=0, ties=0, user_id=None):
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.user_id = user_id


class BoardState(ABC, Base):
    __tablename__ = "board_states"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    game_id = sqla.Column("game_id", sqla.Integer, nullable=False)
    piece_id = sqla.Column("piece_id", sqla.Integer, sqla.ForeignKey("pieces.id"), nullable=False)

    def __init__(self, game_id=None, piece_id=None):
        self.game_id = game_id
        self.piece_id = piece_id

