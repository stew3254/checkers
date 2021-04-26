import checkers
from database import db

session = db.session

running_ai = {}


class AI:
    def __init__(self, game_id: int):
        self.game_id = game_id
        pass

    def get_heurisitc(moves):
        heuristic = 0
        if moves == []:
            return heuristic
        else:

        return heuristic
        #pass

    def make_move(self):
        # This can be a checkers.make_jump() or checkers.make_move()
        session_state = checkers.check_game_state(session, self.game_id)
        pieces = checkers.board_state(session_state, self.game_id)
        for piece in pieces:
            moves = checkers.get_moves(session, self.game_id, piece)
            self.get_heuristic(moves)
            print(moves)
        pass

    def evaluate(self):
        pass

