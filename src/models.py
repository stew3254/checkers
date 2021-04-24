import os
import datetime
from base64 import b64encode as encode
from errors import *
from sqlalchemy.exc import MultipleResultsFound
from database import db

Session = db.Session


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


class User(ABC, db.Model):
    __tablename__ = "users"
    id = db.Column("id", db.String, primary_key=True)
    last_played = db.Column("last_played", db.DateTime, nullable=False, default=datetime.datetime.utcnow())
    last_ip = db.Column("last_ip", db.String, nullable=False)
    turn = db.Column("turn", db.Boolean, nullable=False, default=True)

    def __init__(self, user_id=None, last_played=None, last_ip=None):
        self.id = user_id
        self.last_played = last_played
        self.last_ip = last_ip

    def __repr__(self):
        return self.id

    def exists(self, session: Session):
        return session.query(db.exists().where(User.id == self.id)).scalar()

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


class Piece(ABC, db.Model):
    __tablename__ = "pieces"
    id = db.Column("id", db.Integer, primary_key=True)
    row = db.Column("row", db.SmallInteger, nullable=False)
    column = db.Column("column", db.Integer, nullable=False)
    king = db.Column("king", db.Boolean, nullable=False)
    owner_id = db.Column("owner", db.ForeignKey("users.id"), index=True, nullable=False)
    owner = db.relation(User, backref=db.backref("pieces", lazy="joined"))

    def __init__(self, row=None, column=None, owner_id=encode(b"ai").decode(), king=False, id=None):
        self.row = row
        self.column = column
        self.owner_id = owner_id
        self.king = king
        self.id = id

    def __repr__(self):
        return f"{'Player' if self.player_owned() else 'AI'}" \
               f"({self.row}, {self.column}, {'king' if self.king else 'normal'})"

    def player_owned(self):
        return self.owner_id != encode(b"ai").decode()

    def get_from_db(self, session: Session, game_id: int):
        # Check to see if the piece exists
        try:
            res = session.query(Piece).join(BoardState).where(db.and_(
                Piece.row == self.row,
                Piece.column == self.column,
                BoardState.game_id == game_id
            )).scalar()
            session.commit()
        # Got back too many pieces
        except MultipleResultsFound:
            session.rollback()
            raise InvalidPiece("Too many pieces found, couldn't tell which to refer to")
        # Raise an exception if it doesn't exist
        if res is None:
            session.rollback()
            raise InvalidPiece("Piece does not exist")
        return res

    def exists(self, session: Session, game_id=0):
        if self.id != 0 and self.id is not None:
            res = session.query(db.exists().where(Piece.id == self.id)).scalar()
        else:
            res = session.query(db.exists().where(db.and_(
                Piece.row == self.row,
                Piece.column == self.column,
                BoardState.game_id == game_id
            ))).scalar()
        session.commit()
        return res

    def as_json(self):
        return {"row": self.row, "column": self.column}


class Score(ABC, db.Model):
    __tablename__ = "scores"
    id = db.Column("id", db.Integer, primary_key=True)
    wins = db.Column("wins", db.Integer, nullable=False, default=0)
    losses = db.Column("losses", db.Integer, nullable=False, default=0)
    ties = db.Column("ties", db.Integer, nullable=False, default=0)
    user_id = db.Column("user_id", db.ForeignKey("users.id"), nullable=False, default=True)
    user = db.relation(User, backref=db.backref("scores", lazy="joined"))

    def __init__(self, wins=0, losses=0, ties=0, user_id=None):
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.user_id = user_id


class GameState(ABC, db.Model):
    __tablename__ = "game_states"
    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column("user_id", db.String, db.ForeignKey("users.id"), nullable=False)
    user = db.relation(User, backref=db.backref("users", lazy="joined"))
    __table_args__ = (db.UniqueConstraint("user_id", name="_game_user_uc"),)

    def __init__(self, game_id=None, user_id=None):
        self.id = game_id
        self.user_id = user_id


class BoardState(ABC, db.Model):
    __tablename__ = "board_states"
    id = db.Column("id", db.Integer, primary_key=True)
    game_id = db.Column("game_id", db.Integer, db.ForeignKey("game_states.id"), nullable=False)
    piece_id = db.Column("piece_id", db.Integer, db.ForeignKey("pieces.id"), nullable=False)
    piece = db.relation(Piece, backref=db.backref("board_states", lazy="joined"))

    def __init__(self, game_id=None, piece_id=None):
        self.game_id = game_id
        self.piece_id = piece_id
