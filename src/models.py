import sqlalchemy as sqla
from sqlalchemy.orm import relation, backref


class User:
    __table_name__ = "users"
    token = sqla.Column("token", sqla.Integer)
    last_played = sqla.Column("last_played", sqla.Time)
    last_ip = sqla.Column("last_ip", sqla.String)


class Piece:
    __table_name__ = "pieces"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    column = sqla.Column("column", sqla.String(1))
    row = sqla.Column("row", sqla.SmallInteger)
    king = sqla.Column("king", sqla.Boolean)
    owner_id = sqla.Column("owner", sqla.ForeignKey("users.id"))
    owner = relation(User, backref=backref("user", lazy="joined"))


class Score:
    __table_name__ = "scores"
    id = sqla.Column("id", sqla.Integer, primary_key=True)
    user_id = sqla.Column("user_id", sqla.ForeignKey("users.id"))
    wins = sqla.Column("wins", sqla.Integer)
    losses = sqla.Column("losses", sqla.Integer)
    ties = sqla.Column("ties", sqla.Integer)

    user = relation(User, backref=backref("user", lazy="joined"))


class BoardState:
    __table_name__ = "board_states"
    game_id = sqla.Column("game_id", sqla.Integer)
    piece_id = sqla.Column("game_id", sqla.Integer, sqla.ForeignKey("pieces.id"))
