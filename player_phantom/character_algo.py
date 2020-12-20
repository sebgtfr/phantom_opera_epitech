import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler
from copy import deepcopy
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
original_passages = [[1, 4], [0, 2], [1, 3], [2, 7], [0, 8, 5],
            [4, 6], [5, 7], [9, 3, 6], [9, 4], [8, 7]]

original_pink_passages = [[1, 4], [0, 2, 5, 7], [1, 3, 6], [2, 7], [0, 8, 5, 9],
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
        self.passages = None
        self.pink_passages = None
        self.blocked_passage= None
        self.will_scream = True
        self.in_dark_room = True
        self.answer_data = {}

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def is_suspect(self, character):
        return character["suspect"]

    def is_alone(self, character, characters):
        for c in characters:
            if c is not character:
                if characters["position"] == character["position"]:
                    return False
        return True

    def get_position(self, character):
        return character["position"]

    def get_nb_player_in_room(self, room, characters):
        nb_player_in_room = 0
        for character in characters:
            if room == character["position"]:
                nb_player_in_room += 1
        return nb_player_in_room

    def get_nb_player_in_same_position(self, position, characters):
        nb_same_pos = 0
        for character in characters:
            if position == self.get_position(character):
                nb_same_pos += 1
        return nb_same_pos

    def get_nb_suspect(self, characters):
        nb_suspect = 0
        for character in characters:
            if character["suspect"] is True:
                nb_suspect += 1
        return nb_suspect

    def get_nb_suspect_player_solo(self, characters):
        nb_suspect = 0
        for character in characters:
            if character["suspect"] is True and self.is_alone(character, characters) is True:
                nb_suspect += 1
        return nb_suspect

    def get_nb_player_in_same_situation(self, c, characters):
        nb_player_same_situation = 0
        is_solo = self.is_alone(c, characters)
        for character in characters:
            if is_solo == self.is_alone(character, characters):
                nb_player_same_situation += 1
        return nb_player_same_situation

    def how_many_will_be_exculpate(self, characters):
        nb_exculpate = 0
        if self.will_scream is False:
            return nb_exculpate
        for character in characters:
            if self.is_alone(character, characters) is True:
                nb_exculpate += 1
        return nb_exculpate

    def have_to_scream(self, characters):
        nb_suspect = self.get_nb_suspect(characters)
        nb_exculpate = self.how_many_will_be_exculpate(characters)
        return False if nb_exculpate < nb_suspect / 2 else True

    def in_dark(self, character, rooms, game):
        shadow_room = -1
        for room in rooms in range(10):
            if room is game.shadow:
                shadow_room = room
        return True if character["position"] == shadow_room else False


    def get_room_pos_character_alone(self, characters, room_available):
        room_with_someone = {}
        for character in characters:
            # if character["suspect"] is True and character["position"] in room_available:
            pos = character["position"]
            if pos in room_available:
                if pos not in room_with_someone:
                    room_with_someone[pos] = 1
                else:
                    room_with_someone[pos] += 1
        room_with_one_person = []
        room_with_mutliple_person = []
        for key in room_with_someone:
            if room_with_someone[key] > 1:
                room_with_mutliple_person.append(key)
            else:
                room_with_one_person.append(key)
        if len(room_with_one_person) > 0:
            pos = random.choice(room_with_one_person)
        elif len(room_with_mutliple_person):
            pos = random.choice(room_with_mutliple_person)
        else:
            pos = random.choice(room_available)
        return pos


    def get_available_room_from_pos(self, nbr_person_in_room, initial_pos, characters_passage):
        full_pos_available = characters_passage[initial_pos]
        room_already_check = [initial_pos]
        room_to_check = characters_passage[initial_pos]
        idx = 0
        while (idx < nbr_person_in_room - 1):
            tmp_room_to_check = []
            for pos in room_to_check:
                if pos not in room_already_check:
                    full_pos_available = list(set(full_pos_available + characters_passage[pos]))
                    tmp_room_to_check = tmp_room_to_check + characters_passage[pos]
                    room_already_check.append(pos)
            room_to_check = list(set(tmp_room_to_check))
            idx += 1
        return full_pos_available

    def get_number_person_in_room_and_fantom_pos_and_nbr_sus(self, room_pos, game_state):
        nbr_person_in_room = 0
        fantom_pos = -1
        characters = game_state["characters"]
        fantom = game_state["fantom"]
        suspects = []
        for character in characters:
            if (character["position"] == room_pos):
                nbr_person_in_room += 1
            if character['color'] == fantom:
                fantom_pos = character["position"]
            if character["suspect"] is True:
                suspects.append(character['color'])
        return nbr_person_in_room, fantom_pos, suspects

    def try_to_be_with_fantom(self, character, game_data):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        if character["color"] == "pink":
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.pink_passages)
        else:
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        if fantom_pos in room_available:
            self.answer_data["pos"] = fantom_pos
        else:
            self.answer_data["pos"] = self.get_room_pos_character_alone(game_data["game state"]["characters"], room_available)
        
        # créer une fonction pour savoir combien de personnes se trouve dans la salle.
        # puis en fonction du nombre de personnes dans la salle essayer de voir tous les pass possibles.
        # ensuite voir si dans les paths y'a la position du fantome
        # si y'a pas on va avec un autre suspect 

    def get_pos_empty_and_innocent_room(self, characters, room_available, get_innocent):
        empty_room = deepcopy(room_available)
        room_with_innocent = []
        for character in characters:
            pos = character["position"]
            if pos in empty_room:
                del empty_room[empty_room.index(pos)]
            if pos in room_available and character["suspect"] is False:
                room_with_innocent.append(pos)
        if get_innocent is True:
            pos = random.choice(list(set(empty_room + room_with_innocent)))
        elif len(empty_room) > 0:
            pos = random.choice(empty_room)
        else:
            pos = random.choice(room_available)
        return pos


    def try_to_be_alone(self, character, game_data):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        if character["color"] == "pink":
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.pink_passages)
        else:
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        pos = self.get_pos_empty_and_innocent_room(game_data["game state"]["characters"], room_available, False)
        self.answer_data["pos"] = pos

    def do_suspect_thing(self, character, game_data):
        if self.in_dark_room is True:
            self.try_to_be_with_fantom(character,game_data["game state"])
        else:
            self.try_to_be_alone(character, game_data["game state"])
        
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

    def try_to_be_alone_or_with_innocent(self, character, game_data):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        if character["color"] == "pink":
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.pink_passages)
        else:
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        pos = self.get_pos_empty_and_innocent_room(game_data["game state"]["characters"], room_available, True)
        self.answer_data["pos"] = pos

    def try_to_come_with_suspect(self, character, game_data):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        activate_power = False
        if fantom_pos in room_available and len(suspects) > 0:
            self.answer_data["activate_power"] = 1
            self.answer_data["brown_data"] = random.choice(suspects)
        if activate_power is False:
            self.answer_data["activate_power"] = 0

    def brown_function(self, character, game_data):
        if self.in_dark_room is True:
            self.try_to_come_with_suspect(character, game_data)
        else:
            self.try_to_be_alone_or_with_innocent(character, game_data)

    def do_innocent_thing(self, character, game_data):
        if character["color"] == "brown":
            self.brown_function(character, game_data)
        else:
            self.try_to_be_alone_or_with_innocent(character, game_data)

    def will_scream_function(self, game_data):
        character_to_use = self.get_character_to_use(game_data["data"])
        if character_to_use["suspect"] is True:
            self.do_suspect_thing(character_to_use, game_data)
        else:
            self.do_innocent_thing(character_to_use, game_data)

    def answer(self, question):
        #ne pas oublier de faire une fonction pour choisir cec qu'il faut faire ne fonction de la question type
        # work
        #self.answer_data = {}
        #if self.will_scream is True:
        #    self.will_scream_function(question)
        data = question["data"]
        #game_state = question["game state"]
        #character_to_use = self.get_character_to_use(question["data"])
        #self.try_to_be_with_fantom(character_to_use, question)
        response_index = random.randint(0, len(data)-1)
        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        if question['question type'] == "select character":
            #character = self.get_character_to_use(question["data"])
            character = data[response_index]
            nbr_person_in_room, fantom_pos = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], question["game state"])
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
            pos = self.get_room_pos_character_alone(question["game state"]["characters"], room_available)
            fantom_logger.debug(f"room_available {room_available}")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def define_passages(self, blocked):
        try:
            if self.blocked_passage != blocked:
                self.blocked_passage = blocked
                self.pink_passages = deepcopy(original_pink_passages)
                self.passages = deepcopy(original_passages)
                self.passages[blocked[0]].remove(blocked[1])
                self.passages[blocked[1]].remove(blocked[0])
                self.pink_passages[blocked[0]].remove(blocked[1])
                self.pink_passages[blocked[1]].remove(blocked[0])
        except:
            pass

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
        self.define_passages(data["game state"]["blocked"])
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
