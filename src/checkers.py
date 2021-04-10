from errors import *
from models import *
from sqlalchemy.exc import MultipleResultsFound
import sqlalchemy as sqla

COLUMNS="abcdefgh"


def new_game(session: Session, user_id: str):
    """
    :param session:
    :param user_id:
    :return: The id of the game created
    """
    letters = "abcdefgh"
    pieces = []
    i = 0
    dim = 8
    uid = user_id

    # Add all of the pieces to the game
    while i < dim ** 2:
        if dim * 3 <= i < dim * (dim - 3):
            i = dim * 5 + 1
            uid = encode(b"ai").decode()
            continue
        pieces.append(Piece(letters[i % dim], i // dim, uid))
        # Need to skip an extra one to find the next black
        if (i // dim) % 2 == 0 and i % dim == dim - 2:
            i += 3
        # Don't skip at all, just go to the next black
        elif (i // dim) % 2 == 1 and i % dim == dim - 1:
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


def place_move(session: Session, game_id: int, piece: Piece, position: str):
    # Check to see if the piece exists
    try:
        res = session.query(Piece).join(BoardState).where(sqla.and_(
            Piece.row == piece.row,
            Piece.column == piece.column,
            Piece.owner_id == piece.owner_id,
            BoardState.game_id == game_id
        )).scalar()
    # Got back too many pieces
    except MultipleResultsFound:
        raise InvalidPiece("error: too many pieces found, couldn't tell which to refer to")
    # Raise an exception if it doesn't exist
    if res is None:
        raise InvalidPiece("error: piece does not exist")
    piece = res

    # See if a position is valid to move to


    session.commit()
