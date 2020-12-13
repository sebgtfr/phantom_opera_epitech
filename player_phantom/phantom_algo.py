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


class Player():

    def __init__(self):
        self.end = False
        self.is_tier_list_init = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tier_list = ["red", "white", "brown", "pink", "purple", "black"]
        self.not_in_tier_list = ["blue", "grey"]
        self.will_scream = True

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        response_index = random.randint(0, len(data)-1)
        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

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
        self.is_tier_list_init = False

    def handle_json(self, data):
        data = json.loads(data)
        if self.is_tier_list_init is True:
            self.init_tier_list(data)
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
