import struct

def is_screaming(player):
    return player.will_scream

def is_suspect(player):
    return player.is_suspect

def in_dark(player):
    return True if player.position == 2 else False
