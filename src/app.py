import datetime
import json
import dotenv
import flask
import jinja2
import flask_sqlalchemy as sqla
from sassutils.wsgi import SassMiddleware
from base64 import b64encode as encode
from sqlalchemy.exc import IntegrityError

import checkers
from models import *

dotenv.load_dotenv()
# Create the flask app
app = flask.Flask(__name__)
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

app.config['SQLALCHEMY_DATABASE_URI'] = "".join(f"""
postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}
@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}
""".splitlines())

db = sqla.SQLAlchemy(app)


# Render the page to play the game
@app.route("/", methods=["GET"])
def play():
    resp = flask.make_response()
    user_id = flask.request.cookies.get("token")
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
        # Fix the user id for later
        user_id = user.id

    # Grab the game state
    game_state = db.session.query(GameState) \
        .join(User) \
        .filter(User.id == user_id) \
        .scalar()
    db.session.commit()

    # If they don't exist, make a new game
    if game_state is None:
        game_state = GameState()
        game_state.id = checkers.new_game(db.session, user_id)

    # Get the board states
    board_states = db.session.query(BoardState) \
        .filter(BoardState.game_id == game_state.id) \
        .all()
    db.session.commit()

    # Create a dict of pieces from the board states to give to the template
    pieces = {}

    # Get linear position based on grid
    def get_pos(piece):
        return 8 * piece.row + piece.column

    # Make a dict of pieces where the linear position is the key
    pieces = {get_pos(state.piece): state.piece for state in board_states}

    # Get the score
    score = db.session.query(Score).join(User).where(User.id == user_id).scalar()
    # If score doesn't exist, make it
    if score is None:
        score = Score(user_id=user_id)
        db.session.add(score)
    db.session.commit()

    # Hijack the response to fix the template
    resp.response = [flask.render_template(
        "checkers.pug",
        str=str,
        int=int,
        pieces=pieces,
        score=score
    ).encode()]

    return resp


@app.route("/api/make-move", methods=["POST"])
def make_move():
    data = json.loads(flask.request.data)
    # Create a piece from the json
    try:
        piece = Piece(**data["piece"]).get_from_db(db.session, data.get("game_id"))
    except InvalidPiece as e:
        db.session.rollback()
        return {"type": "error", "message": str(e)}, 400

    # Get the user
    user = db.session.query(User).where(User.id == data.get("token")).scalar()
    db.session.commit()
    if user is None:
        db.session.commit()
        return {"type": "error", "message": "invalid user token"}, 400

    res = {}

    # Make sure it's the user's turn before trying to place a move
    if user.turn:
        try:
            # Attempt to place the move
            db.session.commit()
            checkers.make_move(db.session, data.get("game_id"), piece, data.get("position"))
            # Tell the user it's no longer their turn
            user.turn = False
            # TODO call AI here
        except InvalidPiece as e:
            res = ({"type": "error", "message": str(e)}, 400)
        except InvalidMove as e:
            res = ({"type": "error", "message": str(e)}, 400)
    else:
        res = ({"type": "error", "message": "it is not your turn yet"}, 400)

    db.session.commit()
    return res


@app.route("/api/make-jump", methods=["POST"])
def make_jump():
    data = json.loads(flask.request.data)
    # Create a piece from the json
    try:
        piece = Piece(**data["piece"]).get_from_db(db.session, data.get("game_id"))
    except InvalidPiece as e:
        db.session.rollback()
        return {"type": "error", "message": str(e)}, 400

    # Get the user
    token = data.get("token")
    user = db.session.query(User).where(User.id == data.get("token")).scalar()
    db.session.commit()
    if user is None:
        db.session.commit()
        return {"type": "error", "message": "invalid user token"}, 400

    res = {}

    # Make sure it's the user's turn before trying to place a move
    if user.turn:
        try:
            # Attempt to place the move
            db.session.commit()
            checkers.make_jump(db.session, data.get("game_id"), piece, data.get("position"), data.get("end_turn"))
            # Tell the user it's no longer their turn
            # TODO call AI here
        except InvalidPiece as e:
            res = ({"type": "error", "message": str(e)}, 400)
        except InvalidMove as e:
            res = ({"type": "error", "message": str(e)}, 400)
    else:
        res = ({"type": "error", "message": "it is not your turn yet"}, 400)

    db.session.commit()
    return res


@app.route("/api/available-moves", methods=["GET"])
def get_moves():
    moves = checkers.get_moves(db.session, 1, Piece(3, 1))
    return {
        "type": "moves",
        "message": "The list of move paths available for this move",
        "response": [[i.as_json() for i in path] for path in moves]
    }


if __name__ == "__main__":
    # Drop all tables for debugging
    # db.drop_all()
    # Make all tables
    db.create_all()

    app.run()
    db.session.close()
