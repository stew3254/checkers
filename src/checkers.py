from models import *


def new_game(session: Session, user_id: str):
    """
    :param session:
    :param user_id:
    :return: The id of the game created
    """
    pieces = []
    offset = 1
    uid = user_id
    # Loop through both side
    for side in range(2):
        if side == 1:
            offset = 6
            uid = encode(b"ai").decode()
        # Rows on each side
        for i in range(3):
            row = i + offset
            # Go through columns
            for column, letter in enumerate("abcdefgh"):
                # Make sure to add pieces to black squares only
                if row % 2 == 0:
                    if column % 2 == 1:
                        pieces.append(Piece(letter, row, uid))
                else:
                    if column % 2 == 0:
                        pieces.append(Piece(letter, row, uid))

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
