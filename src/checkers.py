from models import *
import sqlalchemy as sqla

COLUMNS = "abcdefgh"
import enum

DIMENSIONS = 8


class State(enum.Enum):
    Win = 0
    Loss = 1
    Draw = 2
    Playing = 2


# Determines if you can jump an already existing piece. If it can, it returns a piece location
# Otherwise, it returns none
def show_jump(session: Session, game_id: int, piece: Piece, pos: Piece):
    pos = pos.get_from_db(session, game_id)
    # See if it's an enemy piece
    if piece.owner_id != pos.owner_id:
        # Get the new position
        new_row, new_column = 0, 0
        # Make sure it's valid
        if piece.row > pos.row:
            new_row = piece.row - 2
        else:
            new_row = piece.row + 2
        if piece.column > pos.column:
            new_column = piece.column - 2
        else:
            new_column = piece.column + 2

        # Make sure it's still in the bounds
        if (0 < new_row < DIMENSIONS) and (0 < new_column < DIMENSIONS):
            new_pos = Piece(new_row, new_column, piece.owner_id)
            # See once again if this exists
            if not new_pos.exists(session, game_id):
                return new_pos


# Returns a list of jumps it can make, otherwise returns none
def try_jump(session: Session, game_id: int, piece: Piece, pos: Piece):
    # Jump scenario
    jumps = []
    if pos.exists(session, game_id):
        new_pos = show_jump(session, game_id, piece, pos)
        if new_pos is not None:
            # Recursively see if these can jump
            for i in [-1, 1]:
                # Either moving up the board or down the board
                direction = 1
                if piece.row > pos.row:
                    direction = -1
                jumps += try_jump(
                    session,
                    game_id,
                    new_pos,
                    Piece(new_pos.row + direction, new_pos.column + i)
                )
            # Add any future jumps
            for path in jumps:
                # Add the jump that got us here first
                path.insert(0, new_pos)
            # Add the single jump as a path regardless
            jumps.append([new_pos])

    return jumps


def get_moves(session: Session, game_id: int, piece: Piece):
    # Check the bounds
    potential_moves = []
    direction = 1
    # Check if it's the AI
    if not piece.player_owned():
        direction = -1

    # Get all possible piece moves without jumps
    if piece.row < DIMENSIONS - 1:
        # Correct direction for player movement or backwards movement for ai
        if piece.player_owned() or piece.king:
            if piece.column > 0:
                potential_moves.append([(Piece((piece.row + 1) * direction, piece.column - 1), False)])
            if piece.column < DIMENSIONS - 1:
                potential_moves.append([(Piece((piece.row + 1) * direction, piece.column + 1), False)])
    if piece.row > 0:
        # Correct direction for ai movement or backwards movement for player
        if not piece.player_owned() or piece.king:
            if piece.column > 0:
                potential_moves.append([(Piece((piece.row - 1) * direction, piece.column - 1), False)])
            if piece.column < DIMENSIONS - 1:
                potential_moves.append([(Piece((piece.row - 1) * direction, piece.column + 1), False)])

    # See if pieces already exist in those positions
    moves = []
    for move_paths in potential_moves.copy():
        m = move_paths[0][0]
        # Check Jump scenario
        if m.exists(session, game_id):
            current_jumps = try_jump(session, game_id, piece, m)
            # Jumps exist so add them
            if len(current_jumps) > 0:
                moves += current_jumps
        else:
            # Add the single move
            moves.append([m])

    session.commit()
    return moves


def new_game(session: Session, user_id: str, turn=True):
    """
    :param turn:
    :param session:
    :param user_id:
    :return: The id of the game created
    """
    pieces = []
    i = 0
    uid = user_id
    user = session.query(User).where(User.id == user_id).scalar()
    if user is not None:
        user.turn = turn

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

    print(pieces)
    # Add all of the pieces to the table
    session.add_all(pieces)
    # Get the ids of the pieces that have been committed
    session.flush(pieces)

    # Now get the next game id
    new_game_id = session.query(
        # Make sure it returns 0 instead of none
        sqla.func.coalesce(
            # Get the max board state
            sqla.func.max(GameState.id),
            0
        )
    ).scalar() + 1

    # Add players to the game and create them
    game_states = [GameState(new_game_id, user_id)]
    session.add_all(game_states)
    session.flush(game_states)

    # Add all of the board states for this game
    session.add_all(BoardState(new_game_id, piece.id) for piece in pieces)
    # Commit the transaction
    session.commit()
    return new_game_id


def try_king(session: Session, piece: Piece):
    if not piece.king:
        return
    if ((piece.player_owned() and piece.row == DIMENSIONS - 1) or
            (not piece.player_owned() and piece.row == 0)):
        # King the piece
        piece.king = True
        session.commit()


def make_move(session: Session, game_id: int, piece: Piece, position: dict):
    # Get the piece from the database if it exists
    # If it doesn't, don't handle the exception
    piece = piece.get_from_db(session, game_id)
    user = session.query(User).where(User.id == piece.owner_id).scalar()
    session.commit()

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

    # Commit to the db
    session.commit()

    # See if the piece is now a king
    try_king(session, piece)


def make_jump(session: Session, game_id: int, piece: Piece, position: dict, end_turn):
    # Make sure to get a valid piece
    piece = piece.get_from_db(session, game_id)
    pos = Piece(**position).get_from_db(session, game_id)

    # Try to see if we can jump
    new_piece = show_jump(session, game_id, piece, pos)
    print(new_piece)

    # If we can't jump say we can't
    if new_piece is None:
        raise InvalidMove("cannot jump piece")
    if end_turn:
        user = session.query(User).where(User.id == piece.owner_id)
        user.turn = False
        session.commit()
    else:
        moves = get_moves(session, game_id, new_piece)
        can_jump = False
        if len(moves) != 0:
            direction = pos.row - piece.row

            for path in moves:
                for move in path:
                    if (new_piece.row + 2) * direction == move.row:
                        can_jump = True
                        break
                else:
                    continue
                break
        if not can_jump:
            user = session.query(User).where(User.id == piece.owner_id)
            user.turn = False
            session.commit()

    # Update the piece position
    piece.row, piece.column = new_piece.row, new_piece.column
    # Get the board state for the jumped piece
    state = session.query(BoardState).join(Piece).filter(BoardState.piece_id == pos.id).scalar()
    # Delete the spot on the board and tell the db it's deleted
    session.delete(state)
    session.flush([state])
    # Remove the piece from the db
    session.query(Piece).filter(Piece.id == pos.id).delete(synchronize_session="fetch")

    session.commit()


def check_game_state(session: Session, game_id: int) -> State:
    return State.Playing


def board_state(session: Session, game_id: int) -> list:
    board_states = session.query(BoardState).where(BoardState.game_id == game_id).all()
    session.commit()
    pieces = [state.piece for state in board_states]
    return pieces
