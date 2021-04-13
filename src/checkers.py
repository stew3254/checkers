from models import *
import sqlalchemy as sqla

COLUMNS = "abcdefgh"
DIMENSIONS = 8


def new_game(session: Session, user_id: str):
    """
    :param session:
    :param user_id:
    :return: The id of the game created
    """
    pieces = []
    i = 0
    uid = user_id

    # Add all of the pieces to the game
    while i < DIMENSIONS ** 2:
        if DIMENSIONS * 3 <= i < DIMENSIONS * (DIMENSIONS - 3):
            i = DIMENSIONS * 5 + 1
            uid = encode(b"ai").decode()
            continue
        pieces.append(Piece(i // DIMENSIONS, i % DIMENSIONS, uid))
        # Need to skip an extra one to find the next black
        if (i // DIMENSIONS) % 2 == 0 and i % DIMENSIONS == DIMENSIONS - 2:
            i += 3
        # Don't skip at all, just go to the next black
        elif (i // DIMENSIONS) % 2 == 1 and i % DIMENSIONS == DIMENSIONS - 1:
            i += 1
        # Normal rules when in a row
        else:
            i += 2

    # Add all of the pieces to the table
    session.add_all(pieces)
    # Get the ids of the pieces that have been committed
    session.flush(pieces)

    # Now get the next game id
    new_game_id = session.query(
        # Make sure it returns 0 instead of none
        sqla.func.coalesce(
            # Get the max board state
            sqla.func.max(GameState.game_id),
            0
        )
    ).scalar() + 1

    # Add players to the game and create them
    game_states = [GameState(new_game_id, user_id), GameState(new_game_id, uid)]
    session.add_all(game_states)

    # Add all of the board states for this game
    session.add_all(BoardState(new_game_id, piece.id) for piece in pieces)
    # Commit the transaction
    session.commit()
    return new_game_id


def place_move(session: Session, game_id: int, piece: Piece, position: dict, is_jump=False):
    # Get the piece from the database if it exists
    # If it doesn't, don't handle the exception
    piece = piece.get_from_db(session, game_id)

    # Make sure the move type is not a jump
    if not is_jump:
        # Make sure move is within bounds of the board
        if not (0 <= position["row"] <= DIMENSIONS and 0 <= position["column"] <= DIMENSIONS):
            raise InvalidMove("Cannot place move off of the board")

        # Get correct movement direction
        direction = 1
        if piece.owner_id == encode(b"ai").decode():
            direction = -1

        # Get tiles moves
        row_diff = direction * (position["row"] - piece.row)
        col_diff = position["column"] - piece.column
        if abs(row_diff) != 1 or abs(col_diff) != 1:
            raise InvalidMove("Tried to move too many spaces")
        elif row_diff != 1 and not piece.king:
            raise InvalidMove("Cannot move non-king pieces backwards")

        # See if a piece is already there or not
        if Piece(**position).exists(session, game_id):
            raise InvalidMove("Another piece is already here")

    # Update the new position of the piece
    piece.row, piece.column = position["row"], position["column"]

    session.commit()
