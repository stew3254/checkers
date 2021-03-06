from models import *
from database import db
import datetime
import flask


def create_user_cookie(resp, user_id):
    # If the uid doesn't exist or is invalid, make a new one
    if user_id is None or not db.session.query(db.exists().where(User.id == user_id)).scalar():
        db.session.commit()
        user = User().create_unique(db.session, last_ip=flask.request.remote_addr)
        # Add the user to the database
        db.session.add(user)
        db.session.commit()
        # Set cookie to expire 4 weeks from now if not used
        resp.set_cookie(
            "token",
            user.id,
            expires=datetime.datetime.utcnow() + datetime.timedelta(days=28),
            secure=True,
            # This is bad practice, but I didn't want to set up proper authentication
            httponly=False
        )

        # return the real user id
        user_id = user.id
    return user_id


def create_game_id(resp, game_id):
    print(game_id)
    # If the uid doesn't exist or is invalid, make a new one
    if game_id is not None and db.session.query(db.exists().where(GameState.id == game_id)).scalar():
        # Set cookie to expire 4 weeks from now if not used
        resp.set_cookie(
            "game_id",
            str(game_id),
            expires=datetime.datetime.utcnow() + datetime.timedelta(days=28),
            secure=True,
            httponly=True
        )
    db.session.commit()


def as_dict(pos: tuple):
    return {
        "row": pos[0],
        "column": pos[1]
    }
