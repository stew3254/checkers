import checkers
from database import db
from models import *

session = db.session

running_ai = {}


def __new_game():
    user = User().create_unique(session)
    checkers.new_game(session, user.id)


class AI:
    def __init__(self, game_id: int):
        self.game_id = game_id
        pass

    def heurisitc(self):
        pass

    def make_move(self):
        # This can be a checkers.make_jump() or checkers.make_move()
        pass

    def evaluate(self):
        pass
