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

        for piece in ai_pieces:
            moves = checkers.get_moves(board, piece)
            # Find the first piece that can take a move and just take the first move
            if len(moves) > 0:
                move = moves[0][0]
                # See if it's a jump
                if checkers.exists(board, move):
                    checkers.make_jump(session, self.game_id, piece, move.as_json(), True)
                    return
                else:
                    checkers.make_move(session, self.game_id, piece, move.as_json())
                    return
