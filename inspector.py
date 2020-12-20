import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import copy
import math

import protocol

# ways between rooms
# rooms are numbered
# from right to left
# from bottom to top
# 0 ---> 9
passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
# ways for the pink character
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9},
                 {4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5},
                 {7, 8, 4, 6}]

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
set up inspector logging
"""
inspector_logger = logging.getLogger()
inspector_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/inspector.log"):
    os.remove("./logs/inspector.log")
file_handler = RotatingFileHandler('./logs/inspector.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
inspector_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
inspector_logger.addHandler(stream_handler)


class Player():

    SELECT_CHAR = 'select character'
    SELECT_POSITION = 'select position'

    def __init__(self):

        self.end = False
        # self.old_question = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._blocked = []
        self._answers = None

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def getAdjacentPositionsFromCharacter(self, character):
        if character['color'] == "pink":
            active_passages = pink_passages
        else:
            active_passages = passages
        return [room for room in active_passages[character['position']] if set([room, character['position']]) != set(self._blocked)]

    def generateAvailablePosition(self, position):
        newPositions = []
        currentAvailableCharacters = copy.deepcopy(position['available_characters'])
        for availableCharacter in position['available_characters']:
            avalaiblePositions = self.getAdjacentPositionsFromCharacter(availableCharacter)
            availableCharacters = [x for x in currentAvailableCharacters if x != availableCharacter]
            indexCharacter = 0
            for i, character in enumerate(position['characters']):
                if character['color'] == availableCharacter['color']:
                    indexCharacter = i
                    break
            for avalaiblePosition in avalaiblePositions:
                characters = copy.deepcopy(position['characters'])
                actionCharacter = characters[indexCharacter].copy()
                characters[indexCharacter]['position'] = avalaiblePosition
                newPositions.append({
                    'available_characters': availableCharacters,
                    'characters': characters,
                    'action': {
                        'character': actionCharacter,
                        'position' : avalaiblePosition
                    }
                })
        return newPositions
    
    def evaluate(self, position):
        if position is None or position['action'] is None:
            return { 'numberOfNewInnocent': 0, 'action': None }
        numberOfNewInnocent = 0
        for i, character in enumerate(position['characters']):
            if character['suspect'] == True:
                newInnocent = 1
                otherCharacters = [x for j, x in enumerate(position['characters']) if i > j]
                for otherCharacter in otherCharacters:
                    if otherCharacter['position'] == character['position']:
                        newInnocent = 0
                        break
                numberOfNewInnocent += newInnocent
        return { 'numberOfNewInnocent': numberOfNewInnocent, 'action': position['action'] }

    def pruneAlphaBeta(self, currentPosition, positions, depth = 3, alpha = -math.inf, beta = math.inf, maxPlayer = True):
        if depth == 0:
            return self.evaluate(currentPosition)
        action = None
        if maxPlayer:
            maxEval = -math.inf
            for position in positions:
                algoEval = self.pruneAlphaBeta(position, self.generateAvailablePosition(position), depth - 1, alpha, beta, False)
                maxEval = max(maxEval, algoEval['numberOfNewInnocent'])
                if maxEval == algoEval['numberOfNewInnocent']:
                    action = algoEval['action']
                alpha = max(alpha, algoEval['numberOfNewInnocent'])
                if beta <= alpha:
                    break
            return { 'numberOfNewInnocent': maxEval, 'action': action }
        minEval = math.inf
        for position in positions:
            algoEval = self.pruneAlphaBeta(position, self.generateAvailablePosition(position), depth - 1,  alpha, beta, True)
            minEval = min(minEval, algoEval['numberOfNewInnocent'])
            if minEval == algoEval['numberOfNewInnocent']:
                action = algoEval['action']
            beta = min(beta, algoEval['numberOfNewInnocent'])
            if beta <= alpha:
                break
        return { 'numberOfNewInnocent': minEval, 'action': action }

    def answer(self, question):
        # work
        questionType = question['question type']
        data = question["data"]
        game_state = question["game state"]
        response_index = random.randint(0, len(data)-1)

        # If new player has to be selected, run minmax alpha beta prune algo
        if questionType == self.SELECT_CHAR:
            self._blocked = game_state['blocked']
            initialPosition = [{ 'available_characters': question["data"], 'characters': game_state['characters'], 'action': None}]
            self._answers = self.pruneAlphaBeta(None, initialPosition, min(len(question["data"]), 3))

        if self._answers is not None and self._answers['action'] is not None:
            action = self._answers['action']
            questionPower = 'activate {color} power'.format(color = action['character']['color'])
            if questionType == self.SELECT_CHAR:
                for index, availableCharacter in enumerate(question["data"]):
                    if availableCharacter['color'] == action['character']['color']:
                        response_index = index
                        break
            elif questionType == self.SELECT_POSITION:
                if action['position'] in question['data']:
                    response_index =  question['data'].index(action['position'])
            elif questionType == questionPower:
                if action['character']['color'] == 'pink':
                    response_index = 1
                else:
                    response_index = 0
        # log
        inspector_logger.debug("|\n|")
        inspector_logger.debug("inspector answers")
        inspector_logger.debug(f"question type ----- {question['question type']}")
        inspector_logger.debug(f"data -------------- {data}")
        inspector_logger.debug(f"response index ---- {response_index}")
        inspector_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
        # send back to server
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):

        self.connect()

        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True


p = Player()

p.run()
