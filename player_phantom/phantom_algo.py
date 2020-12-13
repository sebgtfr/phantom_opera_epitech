import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

from original_src import protocol

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
set up fantom logging
"""
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)
passages = [[1, 4], [0, 2], [1, 3], [2, 7], [0, 8, 5],
            [4, 6], [5, 7], [9, 3, 6], [9, 4], [8, 7]]

pink_passages = [[1, 4], [0, 2, 5, 7], [1, 3, 6], [2, 7], [0, 8, 5, 9],
                [8, 1, 4, 6], [9, 2, 5, 7], [9, 3, 6, 1],[9, 4, 5],
                [8, 4, 6, 7]]

class Player():

    def __init__(self):
        self.end = False
        self.is_init_once = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tier_list = ["red", "white", "brown", "pink", "purple", "black"]
        self.not_in_tier_list = ["blue", "grey"]
        self.will_scream = True
        self.in_dark_room = True

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def try_to_be_with_phantom(self, character, game_data):
        #créer une fonction pour savoir combien de personnes se trouve dans la salle.
        #puis en fonction du nombre de personnes dans la salle essayer de voir tous les pass possibles.
        #ensuite voir si dans les paths y'a la position du fantome
        #si y'a pas on va avec un autre suspect 
        return None

    def do_suspect_thing(self, character, game_data):
        if self.in_dark_room:
            self.try_to_be_with_phantom(character, game_data["game state"]["characters"])
        #else:
            #self.try_to_be_alone()
        
    def get_character_to_use(self, characters):
        smallest_idx = None
        character_to_use = None
        for character in characters:
            color = character["color"]
            idx = self.tier_list.index(color)
            if (smallest_idx is None or idx < smallest_idx):
                smallest_idx = idx
                character_to_use = character
        return character_to_use

    def will_scream_function(self, game_data):
        character_to_use = self.get_character_to_use(game_data["data"])
        if character_to_use["suspect"] is True:
            self.do_suspect_thing(character_to_use, game_data)
        #else:
            #self.do_innocent_thing


    def answer(self, question):
        # work
        #if self.will_scream is True:
        #    self.will_scream_function(question)
        data = question["data"]
        #game_state = question["game state"]
        response_index = random.randint(0, len(data)-1)
        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def init_passages(self, blocked):
        passages[blocked[0]].remove(blocked[1])
        passages[blocked[1]].remove(blocked[0])

    def init_tier_list(self, data):
        fantom = data["game state"]["fantom"]
        if fantom not in self.tier_list:
            self.tier_list.insert(0, fantom)
            self.not_in_tier_list.remove(fantom)
        else:
            old_index = self.tier_list.index(fantom)
            self.tier_list.insert(0, self.tier_list.pop(old_index))
            random.shuffle(self.not_in_tier_list)
        self.tier_list = self.tier_list + self.not_in_tier_list
        self.is_init_once = False

    def handle_json(self, data):
        data = json.loads(data)
        if self.is_init_once is True:
            self.init_tier_list(data)
            self.init_passages(data["game state"]["blocked"])
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
