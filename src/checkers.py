from models import *


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
        if dim*3 < i < dim * 6:
            i = dim * 6
            continue
        elif i // dim == 0:
            pieces.append(Piece(letters[i // dim], i % dim, uid))
        else:
            pieces.append(Piece(letters[i // dim], i % dim + 1, uid))
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
            sqla.func.max(BoardState.game_id),
            0
        )
    ).scalar() + 1

    # Add all of the board states for this game
    session.add_all(BoardState(new_game_id, piece.id) for piece in pieces)
    # Commit the transaction
    session.commit()
    return new_game_id
