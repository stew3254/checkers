import checkers
from database import db

session = db.session

running_ai = {}


class AI:
    def __init__(self, game_id: int):
        self.game_id = game_id
        pass

    def get_heurisitc(self):
        heuristic = 0

        return heuristic
        #pass

    def make_move(self):
        # This can be a checkers.make_jump() or checkers.make_move()
        session_state = checkers.check_game_state(session, id)
        pieces = checkers.board_state(session_state)
        for piece in pieces:
            moves = checkers.get_moves(session_state, piece)


        pass

    def evaluate(self):
        pass
