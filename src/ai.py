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
        moves_heuristic = []
        if moves == []:
            moves_heuristic.append(0)
        elif moves != []:
            for action in moves:
                moves_heuristic.append(5)
        i = 0
        average = 0
        for action in moves_heuristic:
            average = average + action
            i = i + 1
        average = average/i

        return (average, moves_heuristic)
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

        highest = 0
        highest_piece = piece_heuristics[0]
        for piece in piece_heuristics:
            if piece[0] > highest:
                highest = piece[0]
                highest_piece = piece
        highest_move = 0
        for moves in highest_piece[1]:
            for move in moves:
                if move > highest_move:
                    highest_move = move

        #highest piece is the piece the AI needs to Move
        #Highest_move is where the piece moves to
        print("HERE")
        print(highest_piece)
        print(highest_move)

        pass

    def evaluate(self):
        self.make_move()
        pass

