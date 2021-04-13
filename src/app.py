import checkers
import flask
import flask_socketio as ws
import jinja2
import sqlalchemy as sqla
import models
import datetime
from src.errors import *
from sqlalchemy.orm import sessionmaker, scoped_session
from sassutils.wsgi import SassMiddleware
from lib import *

# Create the flask app
app = flask.Flask(__name__)
# Create the websocket
socket = ws.SocketIO(app)
# Allow using pug for templating
app.jinja_loader = jinja2.FileSystemLoader("src/templates/pug")
app.jinja_env.add_extension("pypugjs.ext.jinja.PyPugJSExtension")
# Allow sass to be used instead of css
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'app': {'sass_path': 'static/sass',
            'css_path': 'static/css',
            'strip_extension': True,
            },
})

# Connect to the database
engine = sqla.create_engine("sqlite:///checkers.db?check_same_thread=False")
conn = engine.connect()
# Drop all tables to clean up old things (For debugging purposes uncomment this)
models.Base.metadata.drop_all(engine)
# Create all of the tables for the db if they don't already exist
models.Base.metadata.create_all(engine)
session = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))()


# Render the page to play the game
@app.route("/", methods=["GET"])
def play():
    resp = flask.make_response()
    user_id = flask.request.cookies.get("token")
    # If the uid doesn't exist or is invalid, make a new one
    if user_id is None or not session.query(sqla.exists().where(models.User.id == user_id)).scalar():
        user = models.User().create_unique(session, last_ip=flask.request.remote_addr)
        # Add the user to the database
        session.add(user)
        session.commit()
        # Set cookie to expire 4 weeks from now if not used
        resp.set_cookie(
            "token",
            user.id,
            expires=datetime.datetime.utcnow() + datetime.timedelta(days=28),
            secure=True,
            # This is bad practice, but I didn't want to set up proper authentication
            httponly=False
        )
        # Fix the user id for later
        user_id = user.id

    # Grab the game state
    game_state = session.query(models.GameState) \
        .join(models.User) \
        .filter(models.User.id == user_id) \
        .scalar()
    session.commit()

    # If they don't exist, make a new game
    if game_state is None:
        game_state = models.GameState()
        game_state.game_id = checkers.new_game(session, user_id)

    # Get the board states
    board_states = session.query(models.BoardState) \
        .filter(models.BoardState.game_id == game_state.game_id) \
        .all()
    session.commit()

    # Create a dict of pieces from the board states to give to the template
    pieces = {}

    # Get linear position based on grid
    def get_pos(piece):
        return 8 * piece.row + piece.column

    # Make a dict of pieces where the linear position is the key
    pieces = {get_pos(state.piece): state.piece for state in board_states}

    # Get the score
    score = session.query(models.Score).join(models.User).where(models.User.id == user_id).scalar()
    # If score doesn't exist, make it
    if score is None:
        score = models.Score(user_id=user_id)
        session.add(score)
    session.commit()

    # Hijack the response to fix the template
    resp.response = [flask.render_template(
        "checkers.pug",
        str=str,
        int=int,
        pieces=pieces,
        score=score
    ).encode()]

    return resp


# TODO make this require user authentication
@socket.on(Channel.Move, namespace="/ws")
def place(data):
    # Create a piece from the json
    piece = models.Piece(**data["piece"])

    # Get the user
    user = session.query(models.User).where(models.User.id == data["token"]).scalar()

    # Make sure it's the user's turn before trying to place a move
    if user.turn:
        try:
            # Attempt to place the move
            checkers.place_move(session, data["game_id"], piece, data["position"])
            # Tell the user it's no longer their turn
            user.turn = False
        except InvalidPiece as e:
            socket.emit(Channel.PieceError, e)
        except InvalidMove as e:
            socket.emit(Channel.MoveError, e)
    else:
        socket.emit(Channel.TurnError, "it is not your turn yet")

    session.commit()


if __name__ == "__main__":
    socket.run(app)
    session.close()
