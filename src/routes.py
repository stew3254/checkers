import datetime
import flask
import json

import checkers
from models import *
from database import db
from lib import create_user_cookie, create_game_id
from ai import running_ai, AI

routes = flask.Blueprint("routes", __name__, )


# Render the page to play the game
@routes.route("/", methods=["GET"])
def play():
    resp = flask.make_response()
    user_id = flask.request.cookies.get("token")
    # If the uid doesn't exist or is invalid, make a new one
    user_id = create_user_cookie(resp, user_id)

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

    # Give the user a cookie
    if flask.request.cookies.get("game_id") != str(game_state.id):
        create_game_id(resp, game_state.id)

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

    running_ai[game_state.id] = AI(game_state.id)
    user = db.session.query(User).where(User.id == user_id).scalar()
    if not user.turn:
        # Have the ai take its turn
        running_ai[game_state.id].evaluate()
        user.turn = True
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


@routes.route("/api/new-game", methods=["POST"])
def new_game():
    data = {}
    if flask.request.data:
        data = json.loads(flask.request.data)
    else:
        # This handles form data posts
        data = flask.request.form.to_dict()
    choice = data.get("player_choice")
    if choice is None:
        return {"type": "error", "message": "You must submit a player_choice"}, 400
    if choice != "first" and choice != "second":
        return {"type": "error", "message": "You must either go first or second"}, 400

    # See if the user exists
    user_id = flask.request.cookies.get("token")
    if user_id is not None:
        user = db.session.query(User).where(User.id == user_id).scalar()
        if user is not None:
            game_state = db.session.query(GameState).where(GameState.user_id == user_id).scalar()
            if game_state is not None:
                board_states = db.session.query(BoardState) \
                    .where(BoardState.game_id == game_state.id).all()
                piece_ids = [i.piece_id for i in board_states]
                pieces = db.session.query(Piece).filter(Piece.id.in_(piece_ids)).all()
                # Delete the board states
                [db.session.delete(i) for i in board_states]
                # Flush so we can delete the rest of the things
                db.session.flush(board_states)
                # Delete the pieces and game
                [db.session.delete(i) for i in pieces]
                db.session.delete(game_state)
                # Make the new game
                checkers.new_game(db.session, user_id)
            if choice == "first":
                user.turn = True
            else:
                user.turn = False
        db.session.commit()
    # If the player's token is invalid just tell them it's okay anyways
    # This is for security reasons
    return {"type": "message", "message": "new game has been started"}


@routes.route("/api/make-move", methods=["POST"])
def make_move():
    data = json.loads(flask.request.data)
    try:
        game_id = int(flask.request.cookies.get("game_id"))
    except ValueError:
        return {"type": "error", "message": "invalid game id"}, 400

    # Create a piece from the json
    try:
        piece = Piece(**data["piece"]).get_from_db(db.session, game_id)
    except InvalidPiece as e:
        db.session.rollback()
        return {"type": "error", "message": str(e)}, 400

    # Get the user
    user_id = flask.request.cookies.get("token")
    user = db.session.query(User).where(User.id == user_id).scalar()
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
            checkers.make_move(db.session, game_id, piece, data.get("position"))
            # Tell the user it's no longer their turn
            user.turn = False
            db.session.commit()
            # Run the ai
            ai = running_ai.get(game_id)
            if ai is None:
                ai = AI(game_id)
                running_ai.update({game_id: ai})
            ai.evaluate()
            # It's the user's turn again
            user.turn = True
        except InvalidPiece as e:
            res = ({"type": "error", "message": str(e)}, 400)
        except InvalidMove as e:
            res = ({"type": "error", "message": str(e)}, 400)
    else:
        res = ({"type": "error", "message": "it is not your turn yet"}, 400)

    db.session.commit()
    return res


@routes.route("/api/make-jump", methods=["POST"])
def make_jump():
    data = json.loads(flask.request.data)
    try:
        game_id = int(flask.request.cookies.get("game_id"))
    except ValueError:
        return {"type": "error", "message": "invalid game id"}, 400

    # Create a piece from the json
    try:
        piece = Piece(**data["piece"]).get_from_db(db.session, game_id)
    except InvalidPiece as e:
        db.session.rollback()
        return {"type": "error", "message": str(e)}, 400

    # Get the user
    user_id = flask.request.cookies.get("token")
    user = db.session.query(User).where(User.id == user_id).scalar()
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
            checkers.make_jump(db.session, game_id, piece, data.get("position"))
            if not user.turn:
                # Run the ai
                db.session.commit()
                ai = running_ai.get(game_id)
                if ai is None:
                    ai = AI(game_id)
                    running_ai[game_id] = ai
                ai.evaluate()
                user.turn = True
        except InvalidPiece as e:
            res = ({"type": "error", "message": str(e)}, 400)
        except InvalidMove as e:
            res = ({"type": "error", "message": str(e)}, 400)
    else:
        res = ({"type": "error", "message": "it is not your turn yet"}, 400)

    db.session.commit()
    return res


@routes.route("/api/available-moves", methods=["GET"])
def get_moves():
    data = flask.request.args
    print(data)
    # Get game id
    try:
        game_id = int(flask.request.cookies.get("game_id"))
    except ValueError:
        return {"type": "error", "message": "invalid game id"}, 400

    try:
        row = int(data.get("row"))
        column = int(data.get("column"))
        piece = Piece(row, column).get_from_db(db.session, game_id)
    except (ValueError, InvalidPiece):
        return {"type": "error", "message": "invalid piece"}, 400

    board = checkers.board_state(db.session, game_id)
    moves = checkers.get_moves(board, piece)
    return {
        "type": "moves",
        "message": "The list of move paths available for this move",
        "response": [[i.as_json() for i in path] for path in moves]
    }
