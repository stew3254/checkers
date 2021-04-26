import checkers
from database import db
from models import *

session = db.session

running_ai = {}

class AI:
    def __init__(self, game_id: int):
        self.game_id = game_id
        pass

    def get_heurisitc(moves):
        move_heuristic = []
        if moves == []:
            move_heuristic.append(0)
        elif moves != []:
            for move in moves:
                #possible move heuristics
                #can be jumped by opponent lower heuristic
                #closer to becoming a king higher heuristic
                #cant be jumped by opponent higher hearistic
                move_heuristic.append(5)

        return move_heuristic
        #pass

    def make_move(self):
        # This can be a checkers.make_jump() or checkers.make_move()
        piece_heuristics = []
        session_state = checkers.check_game_state(session, self.game_id)
        pieces = checkers.board_state(session_state, self.game_id)
        for piece in pieces:
            moves = checkers.get_moves(session, self.game_id, piece)
            piece_heuristics.append(self.get_heuristic(moves))
            print(moves)
            print(piece_heuristics)
        pass

    def evaluate(self):
        pass

