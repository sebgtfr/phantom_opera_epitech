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
        self.top_tier_list = ["grey", "red"]
        self.tier_list = ["white", "brown", "pink", "purple", "black", "blue"]
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

    def is_alone(self, character, characters):
        for c in characters:
            if c is not character:
                if c["position"] == character["position"]:
                    return False
        return True


    def get_nb_suspect(self, characters):
        nb_suspect = 0
        for character in characters:
            if character["suspect"] is True:
                nb_suspect += 1
        return nb_suspect


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

    def get_room_pos_character_alone(self, characters, room_available):
        room_with_someone = {}
        for character in characters:
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
        elif len(room_with_mutliple_person) > 0:
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
            self.try_to_be_alone(character, game_data)

    def get_pos_empty_and_innocent_room_and_shadow_room(self, characters, room_available, shadow_room, get_innocent):
        empty_room = deepcopy(room_available)
        room_with_innocent = []
        for character in characters:
            pos = character["position"]
            if pos in empty_room and pos != shadow_room:
                del empty_room[empty_room.index(pos)]
            if pos in room_available and character["suspect"] is False:
                room_with_innocent.append(pos)
        if get_innocent is True:
            final_room = list(set(empty_room + room_with_innocent))
            if len(final_room) > 0:
                pos = random.choice(list(set(empty_room + room_with_innocent)))
            else:
                if shadow_room in room_available:
                    del room_available[room_available.index(shadow_room)]
                pos = random.choice(room_available)
        else:
            if shadow_room in room_available:
                empty_room.append(shadow_room)
            if len(empty_room) > 0:
                pos = random.choice(list(set(empty_room)))
            else:
                pos = random.choice(room_available)
        return pos


    def try_to_be_alone(self, character, game_data):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        if character["color"] == "pink":
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.pink_passages)
        else:
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        pos = self.get_pos_empty_and_innocent_room_and_shadow_room(game_data["game state"]["characters"], room_available, game_data["game state"]['shadow'], False)
        self.answer_data["pos"] = pos

    def do_suspect_thing(self, character, game_data):
        if self.in_dark_room is True:
            self.try_to_be_with_fantom(character, game_data)
        else:
            self.try_to_be_alone(character, game_data)
        
    def get_character_to_use(self, characters):
        smallest_idx = None
        character_to_use = None
        character_idx = 0
        for character in characters:
            color = character["color"]
            idx = self.tier_list.index(color)
            if (smallest_idx is None or idx < smallest_idx):
                smallest_idx = idx
                character_to_use = character
                self.answer_data["character_idx"] = character_idx
            character_idx += 1
        return character_to_use

    def try_to_be_alone_or_with_innocent(self, character, game_data):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        if character["color"] == "pink":
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.pink_passages)
        else:
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        pos = self.get_pos_empty_and_innocent_room_and_shadow_room(game_data["game state"]["characters"], room_available, game_data["game state"]['shadow'], True)
        self.answer_data["pos"] = pos

    def try_to_come_with_suspect(self, character, game_data):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        activate_power = False
        if fantom_pos in room_available and len(suspects) > 0:
            self.answer_data["activate_power"] = 1
            self.answer_data["brown_data"] = random.choice(suspects)
            self.answer_data["pos"] = fantom_pos
        if activate_power is False:
            self.answer_data["activate_power"] = 0
            self.try_to_be_alone_or_with_innocent(character, game_data)

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


    def will_scream_function(self, game_data, character):
        if character["suspect"] is True:
            self.do_suspect_thing(character, game_data)
        else:
            self.do_innocent_thing(character, game_data)

    def fantom_is_alone_and_get_room(self, game_state):
        fantom_color = game_state['fantom']
        characters = game_state["characters"]
        positions = [0,0,0,0,0,0,0,0,0,0]
        suspects_room = [0,0,0,0,0,0,0,0,0,0]
        empty_room = [0,0,0,0,0,0,0,0,0,0]
        innocents_room = [0,0,0,0,0,0,0,0,0,0]
        fantom = None
        for character in characters:
            positions[character["position"]] += 1
            if character["color"] == fantom_color:
                fantom = character
            if character["suspect"] is True:
                suspects_room[character["position"]] += 1
            elif character["suspect"] is False:
                innocents_room[character["position"]] += 1
            empty_room[character["position"]] += 1
        if positions[fantom["position"]] == 1:
            suspects_room[game_state['shadow']] = -1
            max_suspects = max(suspects_room)
            max_suspects_room = [i for i, j in enumerate(suspects_room) if j == max_suspects]
            return True, max_suspects_room
        final_empty_room = [i for i, j in enumerate(empty_room) if j == 0]
        final_innocents_room = []
        for i in range(len(innocents_room)):
            if innocents_room[i] >= 1 and suspects_room[i] == 0:
                final_innocents_room.append(i)
        
        return False, final_innocents_room + final_empty_room


    def get_rooms_for_dark(self, game_state, get_max):
        characters = game_state["characters"]
        suspects_room = [0,0,0,0,0,0,0,0,0,0]
        empty_room = [0,0,0,0,0,0,0,0,0,0]
        innocents_room = [0,0,0,0,0,0,0,0,0,0]
        for character in characters:
            if character["suspect"] is True:
                suspects_room[character["position"]] += 1
            elif character["suspect"] is False:
                innocents_room[character["position"]] += 1
            empty_room[character["position"]] += 1
        if get_max is True:
            suspects_room[game_state['shadow']] = -1
            max_suspects = max(suspects_room)
            max_suspects_room = [i for i, j in enumerate(suspects_room) if j == max_suspects]
            return max_suspects_room
        final_empty_room = [i for i, j in enumerate(empty_room) if j == 0]
        final_innocents_room = []
        for i in range(innocents_room):
            if innocents_room[i] >= 1 and suspects_room[i] == 0:
                final_innocents_room.append(i)
        
        return final_innocents_room + final_empty_room


    def set_dark_room(self, game_state):
        response_index = 0
        rooms = []
        if self.in_dark_room is True:
            self.in_dark_room = False
            is_alone, rooms = self.fantom_is_alone_and_get_room(game_state)
            if is_alone is False:
                self.will_scream = False
            response_index = random.choice(rooms)
        elif self.in_dark_room is False and self.will_scream is True:
            rooms = self.get_rooms_for_dark(game_state, True)
        elif self.in_dark_room is False and self.will_scream is False:
            rooms = self.get_rooms_for_dark(game_state, True)
        response_index = random.choice(rooms)
        return response_index




    def character_power(self, game_data):
        question_type = game_data['question type']
        response_data = game_data['data']
        response_index = 0
        if "blue" in question_type:
            response_index = random.choice(response_data)
            response_index = response_data.index(response_index)
        if "grey" in question_type:
            response_index = response_data.index(self.set_dark_room(game_data["game state"]))
        if "brown" in question_type:
            response_index = response_data.index(answer_data["brown_data"])
        return response_index

    def try_to_stay_suspect(self, game_state, room_available):
        characters = game_state["characters"]
        room_with_someone = {}
        for character in characters:
            pos = character["position"]
            if pos in room_available and pos != game_state['shadow']:
                room_with_someone[pos] = True
        if len(room_with_someone.keys()) > 0:
            self.answer_data["pos"] = random.choice(list(room_with_someone))
        else:
            if game_state['shadow'] in room_available:
                del room_available[room_available.index(game_state['shadow'])]
            self.answer_data["pos"] = random.choice(room_available)

    def will_not_scream_function(self, game_data, character):
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        if character["color"] == "pink":
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.pink_passages)
        else:
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        if character["suspect"] is True:
            self.try_to_stay_suspect(game_data["game state"], room_available)
        else:
            pos = random.choice(room_available)
            self.answer_data["pos"] = pos

    def set_fantom_pos(self, game_data, character):
        should_scream = self.have_to_scream(game_data["game state"]["characters"])
        nbr_person_in_room, fantom_pos, suspects = self.get_number_person_in_room_and_fantom_pos_and_nbr_sus(character["position"], game_data["game state"])
        if character["color"] == "pink":
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.pink_passages)
        else:
            room_available = self.get_available_room_from_pos(nbr_person_in_room, character["position"], self.passages)
        if should_scream is True:
            self.answer_data["pos"] = self.get_pos_empty_and_innocent_room_and_shadow_room(game_data["game state"]["characters"], room_available, game_data['game state']['shadow'], False)
        else:
            self.try_to_stay_suspect(game_data["game state"], room_available)

    def in_dark(self, character, rooms, game_state):
        shadow_room = -1
        for room in rooms:
            if room is game_state["shadow"]:
                shadow_room = room
        return True if character["position"] == shadow_room else False

    def can_actually_scream(self, character, characters, rooms, game_state):
        return True if (self.is_alone(character, characters) is True or self.in_dark(character, rooms, game_state) is True) else False            

    def set_dark_and_scream(self, game_data, character):
        fantom_color = game_data["game state"]["fantom"]
        all_rooms = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        characters = game_data["game state"]["characters"]
        for character in characters:
            if character["color"] == fantom_color:
                fantom = character
                break
        self.in_dark_room = self.in_dark(fantom, all_rooms, game_data["game state"])
        self.will_scream = self.can_actually_scream(fantom, game_data["game state"]["characters"], all_rooms, game_data["game state"])

    def answer(self, question):
        data = question["data"]
        if question['question type'] == "select character":
            self.answer_data = {}
            self.answer_data["activate_power"] = 0
            character_to_use = self.get_character_to_use(data)
            self.set_dark_and_scream(question, character_to_use)
            if character_to_use['color'] == question["game state"]["fantom"]:
                self.set_fantom_pos(question, character_to_use)
            else:
                if self.will_scream is True:
                    self.will_scream_function(question, character_to_use)
                else:
                    self.will_not_scream_function(question, character_to_use)
            response_index = self.answer_data["character_idx"]
        elif question['question type'] == "select position":
            response_index = data.index(self.answer_data["pos"])
        elif "activate" in question['question type']:
            response_index = self.answer_data["activate_power"]
        elif "character power" in question['question type']:
            response_index = self.character_power(question)
        fantom_logger.debug("fantom answers")
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
        if fantom in self.tier_list:
            old_index = self.tier_list.index(fantom)
            self.tier_list.insert(0, self.tier_list.pop(old_index))
        self.tier_list = self.top_tier_list + self.tier_list
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
