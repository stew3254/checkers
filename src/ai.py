import checkers
from database import db

session = db.session


class AI:
    def __init__(self, game_id: int):
        self.game_id = game_id
        pass

    def heurisitc(self):
        pass

    def make_move(self):
        # This can be a checkers.make_jump() or checkers.make_move()
        pass