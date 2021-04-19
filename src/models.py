import os
from datetime import datetime
import sqlalchemy as sqla
from sqlalchemy.orm import relation, backref, Session
from base64 import b64encode as encode
from errors import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import MultipleResultsFound

# Define the base for everything to derive from
Base = declarative_base()


class ABC:
    # Make it so the tables pretty print the columns and values as json
    # TODO: fix this or remove it
    # def __repr__(self):
    #     columns = []
    #     # Get (hopefully) columns names
    #     for i in dir(self):
    #         if not i.startswith("_") and not callable(getattr(self, i)) and i not in ["metadata", "registry"]:
    #             columns.append(i)
    #     data = {}
    #     for column in columns:
    #         data.update({column: getattr(self, column)})
    #     return json.dumps(data, indent=2, sort_keys=True)
    pass


class User(ABC, Base):
    __tablename__ = "users"
    id = sqla.Column("id", sqla.String, primary_key=True)
    last_played = sqla.Column("last_played", sqla.DateTime, nullable=False, default=datetime.utcnow())
    last_ip = sqla.Column("last_ip", sqla.String, nullable=False)
    turn = sqla.Column("turn", sqla.Boolean, nullable=False, default=True)

    def __init__(self, user_id=None, last_played=None, last_ip=None):
        self.id = user_id
        self.last_played = last_played
        self.last_ip = last_ip

    def exists(self, session: Session):
        return session.query(sqla.exists().where(User.id == self.id)).scalar()

    def create_unique(self, session: Session, user_id=None, last_played=None, last_ip=None, game_id=None):
        self.last_played = last_played
        self.last_ip = last_ip
        exists = True
        # Find a valid id that doesn't exist
        while exists:
            exists = self.exists(session)
            self.id = user_id or encode(os.urandom(32)).decode()
        return self

    def is_player(self):
        return self.id != encode(b"ai").decode()


class Piece(ABC, Base):
    __tablename__ = "pieces"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    row = sqla.Column("row", sqla.SmallInteger, nullable=False)
    column = sqla.Column("column", sqla.Integer, nullable=False)
    king = sqla.Column("king", sqla.Boolean, nullable=False)
    owner_id = sqla.Column("owner", sqla.ForeignKey("users.id"), index=True, nullable=False)
    owner = relation(User, backref=backref("pieces", lazy="joined"))

    def __init__(self, row=None, column=None, owner_id=encode(b"ai").decode(), king=False, id=None):
        self.row = row
        self.column = column
        self.owner_id = owner_id
        self.king = king
        self.id = id

    def player_owned(self):
        return self.owner_id != encode(b"ai").decode()

    def get_from_db(self, session: Session, game_id: int):
        # Check to see if the piece exists
        try:
            res = session.query(Piece).join(BoardState).where(sqla.and_(
                Piece.row == self.row,
                Piece.column == self.column,
                BoardState.game_id == game_id
            )).scalar()
        # Got back too many pieces
        except MultipleResultsFound:
            raise InvalidPiece("Too many pieces found, couldn't tell which to refer to")
        # Raise an exception if it doesn't exist
        if res is None:
            raise InvalidPiece("Piece does not exist")
        session.commit()
        return res

    def exists(self, session: Session, game_id=0):
        if self.id != 0 and self.id is not None:
            res = session.query(sqla.exists().where(Piece.id == self.id)).scalar()
        else:
            res = session.query(sqla.exists().where(sqla.and_(
                Piece.row == self.row,
                Piece.column == self.column,
                BoardState.game_id == game_id
            ))).scalar()
        session.commit()
        return res


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


class GameState(ABC, Base):
    __tablename__ = "game_states"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    game_id = sqla.Column("game_id", sqla.Integer, nullable=False)
    user_id = sqla.Column("user_id", sqla.String, sqla.ForeignKey("users.id"), nullable=False)
    user = relation(User, backref=backref("users", lazy="joined"))
    __table_args__ = (sqla.UniqueConstraint("game_id", "user_id", name="_game_user_uc"),)

    def __init__(self, game_id=None, user_id=None):
        self.game_id = game_id
        self.user_id = user_id


class BoardState(ABC, Base):
    __tablename__ = "board_states"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    game_id = sqla.Column("game_id", sqla.Integer, sqla.ForeignKey("game_states.game_id"), nullable=False)
    piece_id = sqla.Column("piece_id", sqla.Integer, sqla.ForeignKey("pieces.id"), nullable=False)
    piece = relation(Piece, backref=backref("board_states", lazy="joined"))

    def __init__(self, game_id=None, piece_id=None):
        self.game_id = game_id
        self.piece_id = piece_id

