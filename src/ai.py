import checkers
from database import db
from models import *
from functools import reduce

session = db.session
running_ai = {}


class AI:
    def __init__(self, game_id: int, depth=3):
        self.game_id = game_id
        self.depth = depth
        pass

    def heuristic(self):
        pass

    def make_move(self):
        # This can be a checkers.make_jump() or checkers.make_move()
        pass

    # Didn't finish this
    # def negamax(self, board, piece, depth, alpha, beta, color):
    #     if depth == self.depth or piece is a terminal node then
    #     return color * self.heuristic()
    #
    #     new_moves = checkers.get_moves()
    #     value = −float("inf")
    #     for move in new_moves:
    #         value = max(value, −negamax(move, depth − 1, −β, −α, −color))
    #         alpha := max(alpha, value)
    #         if alpha >= beta:
    #             break
    #     # (*cut - off *)
    #
    #
    #     return value

    def evaluate(self):
        board = checkers.board_state(session, self.game_id)
        ai_pieces = [i for i in board.values() if not i.player_owned()]
        # See which piece can take a move
        ai_moves = []

        def sort_move(m):
            score = len(m) * 100
            if score == 100:
                if not checkers.exists(board, m[0]):
                    score = 1
            return score

        for piece in ai_pieces:
            moves = checkers.get_moves(board, piece)
            moves.sort(key=sort_move, reverse=True)
            if len(moves) > 0:
                ai_moves.append((piece, moves))

        # Get the very best move out of all possible moves
        ai_moves.sort(key=lambda x: len(x[1][0]), reverse=True)
        # Make the best move
        move = ai_moves[0][1][0][0]
        piece = ai_moves[0][0]
        print(ai_moves)
        # if move.player_owned():
        #     checkers.make_jump(session, self.game_id, piece, {"row": move.row, "column": move.column}, True)
        # else:
        #     checkers.make_move(session, self.game_id, piece, move)
