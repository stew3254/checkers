import random
import time
import checkers
import sqlalchemy as sqla
from models import *
from database import db

session = db.session
running_ai = {}
random.seed(time.time())


class GameNode:

    def __init__(self, board: dict, piece: Piece, move_path: list, edges=None):
        if edges is None:
            edges = []
        self.board = board
        self.piece = piece
        self.move_path = move_path
        self.edges = edges

    def add_edge(self, node: GameNode):
        self.edges.append(node)

    def compute_subtree(self, depth, leaves: list):
        new_board = self.board.copy()
        if len(self.move_path) > 1:
            # Definitely a jump
            for i, move in enumerate(self.move_path):
                move_pos = move.as_json()
                # Make the jumps
                if i != len(self.move_path) - 1:
                    new_board = checkers.try_jump(new_board, self.piece, move_pos, False)
                else:
                    new_board = checkers.try_jump(new_board, self.piece, move_pos, True)
        elif len(self.move_path) == 1:
            move = self.move_path[0]
            # Check to see if it's an empty move or a jump
            if move.owner_id is None:
                # Try a regular move
                new_board = checkers.try_move(new_board, self.piece, move.as_json())
            else:
                # Make the single jump
                new_board = checkers.try_jump(new_board, self.piece, move.as_json(), True)

        # Now get all of the opponent's pieces for their moves
        pieces = []
        if self.piece.player_owned():
            pieces = [i for i in new_board if not i.player_owned()]
        else:
            pieces = [i for i in new_board if i.player_owned()]

        for piece in pieces:
            moves = checkers.get_moves(new_board, piece)
            for move_path in moves:
                new_node = GameNode(new_board, piece, move_path)
                if depth > 0:
                    # Recursively compute subtrees up until depth
                    new_node.compute_subtree(depth - 1, leaves)
                else:
                    leaves.append(self)
                self.edges.append(new_node)
        return self


class AI:

    def __init__(self, game_id: int, depth=4):
        self.game_id = game_id
        self.depth = depth
        # Get the board to construct the tree
        board = checkers.board_state(session, game_id)
        # Get user to see if this game exists
        user = session.query(User).join(GameState).where(sqla.and_(
            GameState.id == game_id,
            User.id != encode(b"ai").decode()
        )).scalar()
        if user is None:
            raise InvalidGame("Game does not exist")

        # Get whose turn it is
        if user.turn:
            piece = Piece(owner_id=user.id)
        else:
            piece = Piece(owner_id=encode(b"ai").decode())

        self.leaves = []
        self.game_tree = GameNode(board, piece, []).compute_subtree(depth, self.leaves)

    "This function takes a potential move as its parameter"
    "We then Calculate the heuristic of this position"
    "Returns a value for this potential move"

    def get_move_heuristic(self, piece: Piece, move: list):

        # Will change to Zero when done for now it start random
        move_heuristic = random.randint(0, 9)
        print("MOVE: ", move)
        print("PIECE KING? ", piece.king)
        # print("ROW: ", move[0].row)
        # print("STATUS: ", move[0].owner_id)
        # print("COLUMN: ", move[0].column)
        # print("PIECE STATUS: ", move[0].king)

        # Heuristic for when piece being moves is a King
        if piece.king:
            # When path is Non-Jump
            if move[0].owner_id is None:
                move_heuristic = move_heuristic + 1
            # When path is Jump
            else:
                move_heuristic = move_heuristic + 10
                # When A King Piece can Be Jumped
                if move[0].king:
                    move_heuristic = move_heuristic + 30

        # Heuristic for when Piece being moves is not a King
        elif not piece.king:
            # Heuristic for Calculating if a Piece is Closer to being a King
            move_heuristic = move_heuristic + (7 - move[0].row)

            # When path is Non-Jump
            if move[0].owner_id is None:
                move_heuristic = move_heuristic + 1
            # When path is Jump
            else:
                move_heuristic = move_heuristic + 10
                # When A King Piece can Be Jumped
                if move[0].king:
                    move_heuristic = move_heuristic + 30

            ##[Empty(4, 2, non - king)]
            print("MOVE VALUE: ", move_heuristic)

        return move_heuristic

    "This function takes a single piece as its argument"
    "For this piece it will calculate a heuristic for all possible moves"
    "Returns a tuple who's first element is a list of possible moves for this piece"
    "The second element is the index value in moves which contains best move for this piece"
    "The Third element is the average of all move heuristic values"
    "Avg is the heuristic value for this given piece"

    def get_best_move(self, piece):

        # records which move has highest heuristic for this piece
        highest_move = 0
        move_index = -1
        piece_heuristic = []

        "retrieve the current board"
        board = checkers.board_state(session, self.game_id)

        # contains a list of possible moves for this specific piece
        moves = checkers.get_moves(board, piece)
        # [[Empty(4, 2, non - king)], [Empty(4, 4, king)]]
        print("MOVES for Piece: ", moves)

        # if there are no possible moves the heuristic for best move is 0
        if len(moves) == 0:
            highest_move = 0
            moves = []
            move_index = 0

        # if there are possible moves we must calculate the heuristic for each move available
        elif len(moves) > 0:
            for move in moves:
                print("Move: ", move)
                print("Move Heuristic: ", self.get_move_heuristic(move, piece))
                # returns heuristic for given move
                piece_heuristic.append(self.get_move_heuristic(move, piece))

            for idx, move in enumerate(piece_heuristic):
                if move > highest_move:
                    highest_move = move
                    move_index = idx

        if len(piece_heuristic) != 0:
            avg = sum(piece_heuristic) / len(piece_heuristic)
        elif len(piece_heuristic) == 0:
            avg = sum(piece_heuristic)
        print("Length: ", len(moves))
        print("INDEX: ", move_index)

        return moves, move_index, avg

    def negamax(self, node, depth, alpha, beta, color):
        if depth == 0 or len(node.edges) == 0:
            return color * self.get_move_heuristic(node.piece, node.move_path)
        value = -float("inf")
        for child in node.edges:
            value = max(value, -self.negamax(child, depth - 1, -beta, -alpha, -color))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    "This Function looks at the Game board and calculates heuristics"
    "For each of a players pieces and available moves to that piece"
    "The piece that has the highest heuristic is moved to the position"
    "That has the highest heuristic for the selected piece"

    def evaluate(self):
        print("EVALUATE::: ")
        "list of heuristics for available pieces"
        piece_heuristics = []
        # ( [int,int,int....] , int, flaot )

        "retrieve the current board"
        board = checkers.board_state(session, self.game_id)

        ai_pieces = [i for i in board.values() if not i.player_owned()]

        for piece in ai_pieces:
            "For each piece we calculate the heuristic for each of its"
            "Possible moves in order to determine the pieces heuristic"
            # calls get_best_move to calculate heuristic returns
            # tuple ([X,Y],highest_move, Avg) where X and Y are heuristic
            # for possible moves and Avg is heuristic for this specific piece

            piece_heuristics.append(self.get_best_move(piece))
            print("Pieces Heuristics: ", piece_heuristics)

        # Loop that finds the Piece with the highest heuristic
        highest = 0
        piece_index = -1
        for idx, (moves, move_index, piece_heuristic) in enumerate(piece_heuristics):
            if piece_heuristic > highest:
                highest = piece_heuristic
                piece_index = idx
        print("Piece index: ", piece_index)
        print("PIECE: ", piece_heuristics[piece_index])

        # Generate tuple for piece to move contains list of possible moves
        # index for the best move and heuristic for the piece
        (moves, move_index, piece_heuristic) = piece_heuristics[piece_index]
        print("Piece: ", (moves, move_index, piece_heuristic))

        # position piece needs to move to
        # Path is:  [Empty(4, 2, non-king)]
        path = moves[move_index]
        print("PATH: ", path)

        # See if it's a jump
        if checkers.exists(board, path[0]):
            return checkers.make_jump(session, self.game_id, ai_pieces[piece_index], path[0].as_json(), True)
        else:
            return checkers.make_move(session, self.game_id, ai_pieces[piece_index], path[0].as_json())
