import checkers
from database import db
from models import *
import random
import time
import checkers
from database import db
from models import *
from functools import reduce
from random import randint

session = db.session
running_ai = {}
random.seed(time.time())

# function negamax(node, depth, α, β, color) is
#     if depth = 0 or node is a terminal node then
#         return color × the heuristic value of node
#
#     childNodes := generateMoves(node)
#     childNodes := orderMoves(childNodes)
#     value := −∞
#     foreach child in childNodes do
#         value := max(value, −negamax(child, depth − 1, −β, −α, −color))
#         α := max(α, value)
#         if α ≥ β then
#             break (* cut-off *)
#     return value


class AI:
    def __init__(self, game_id: int, depth=3):
        self.game_id = game_id
        self.depth = depth
        pass

    "This function takes a potential move as its parameter"
    "We then Calculate the heuristic of this position"
    "Returns a value for this potential move"

    def get_move_heuristic(self, move):
        move_heuristic = random.randint(0, 9)
        print("MOVE VALUE: ", move_heuristic)

        return move_heuristic

    "This function takes a single piece as its argument"
    "For this piece it will calculate a heuristic for all possible moves"
    "Returns a tuple who's first element is a list of possible moves for this piece"
    "The second element is the heuristic value for the best move for this piece"
    "The Third element is the average of all move heuristic values"
    "Avg is the heuristic value for this given piece"

    def get_best_move(self, piece):

        # records which move has highest heuristic for this piece
        highest_move = 0
        move_index = 0
        piece_heuristic = []

        "retrieve the current board"
        board = checkers.board_state(session, self.game_id)

        # contains a list of possible moves for this specific piece
        moves = checkers.get_moves(board, piece)
        print("MOVES for Piece: ", moves)

        # if there are no possible moves the heuristic for best move is 0
        if len(moves) == 0:
            highest_move = 0
            moves = []

        # if there are possible moves we must calculate the heuristic for each move available
        elif len(moves) > 0:
            for move in moves:
                print("Move: ", move)
                print("Move Heuristic: ", self.get_move_heuristic(move))
                # returns heuristic for given move
                piece_heuristic.append(self.get_move_heuristic(move))

            for idx, move in piece_heuristic:
                if move > highest_move:
                    highest_move = move

        if len(piece_heuristic) != 0:
            avg = sum(piece_heuristic) / len(piece_heuristic)
        elif len(piece_heuristic) == 0:
            avg = sum(piece_heuristic)

        return (moves, highest_move, avg)

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
        highest_idx = -1
        for idx, moves, move_heuristic, piece_heuristic in enumerate(piece_heuristics):
            if piece_heuristic > highest:
                highest = piece_heuristic
                highest_idx = idx

        # Loop that looks at the piece we need to move and moves it to the best move av
        moves, move_heuristic, piece_heuristic = piece_heuristics[highest_idx]
        # Grab the first path and first move
        # TODO these needs to be changed to fir the algorithm correctly
        path = moves[0]
        move = path[0]

        # See if it's a jump
        if checkers.exists(board, move):
            checkers.make_jump(session, self.game_id, piece, move.as_json(), True)
            return
        else:
            checkers.make_move(session, self.game_id, piece, move.as_json())
            return
