import os
import time
from functools import partial
from termcolor import colored

PLAYER_ID = 1
ENEMY_ID = 2

HQ = "H:{}Id:{}"
UNIT = "U:{}Id:{}"
BLOCKER = "B"


class Tile(object):

    def __init__(self, enemy=False, blocked=False, own_hq=False, enemy_hq=False):
        self.enemy = enemy
        self.blocked = blocked
        self.own_hq = own_hq
        self.enemy_hq = enemy_hq
        self.units = []

    def __repr__(self):
        if self.blocked:
            return BLOCKER

        parts = []
        if self.own_hq:
            parts.append(HQ.format(PLAYER_ID, 0))
        elif self.enemy_hq:
            parts.append(HQ.format(PLAYER_ID, 0))

        if self.enemy:
            parts.append(UNIT.format(ENEMY_ID, 0))
        elif self.units:
            parts.append(','.join([UNIT.format(PLAYER_ID, i) for i in self.units]))

        return ",".join(parts)

    def __str__(self):
        if self.blocked:
            return colored('B', 'grey', 'on_white')
        if self.enemy_hq:
            return colored('H', 'grey', 'on_red')
        if self.own_hq:
            return colored('H', 'grey', 'on_green')
        if self.units:
            return colored('U', 'grey', 'on_green')
        if self.enemy:
            return colored('E', 'grey', 'on_red')

        return colored(' ', 'white', 'on_grey')


CHAR_TILE_MAP = {
    'E': partial(Tile, enemy=True),
    'B': partial(Tile, blocked=True),
    'H': partial(Tile, own_hq=True),
    'G': partial(Tile, enemy_hq=True),
    ' ': Tile
}


class Game(object):

    def __init__(self, fh, bot):
        self.game_map = []
        self.turns = 100
        self.bot = bot
        self.base = None
        self.goal = None
        self.load_tiles(fh)

    def load_tiles(self, fh):
        self.game_map = []
        self.enemies = []

        for y, line in enumerate(fh.readlines()):
            row = []
            for x, letter in enumerate(line.replace('\n', '')):
                row.append(CHAR_TILE_MAP.get(letter)())
                if letter == 'H':
                    self.base = (x, y)
                elif letter == 'G':
                    self.goal = (x, y)
                elif letter == 'E':
                    self.enemies.append((x, y))

            self.game_map.append(row)

        self.units = {str(n): self.base for n in xrange(0, 5)}
        x, y = self.base
        self.game_map[y][x].units = self.units.keys()

    def display(self):
        for row in self.game_map:
            print ''.join(str(t) for t in row)

    @property
    def enemy_base_owned(self):
        x, y = self.goal
        return bool(self.game_map[y][x].units)

    def encode_map(self):
        out = []
        for row in self.game_map:
            out.append([repr(t) for t in row])

        return out

    @property
    def all_enemies_killed(self):
        return not self.enemies

    def run(self):
        while not (self.enemy_base_owned or self.all_enemies_killed or not self.turns):
            time.sleep(0.5)
            os.system('clear')
            self.process_turn()
            self.display()
            self.turns -= 1

        if self.enemy_base_owned or self.all_enemies_killed:
            print "You win!!"
        elif not self.turns:
            print "Game over"

    def process_turn(self):
        """This dont validate anything"""
        data = self.bot.on_turn({'map': self.encode_map(), 'player_num': PLAYER_ID})
        for action in data.get('ACTIONS', []):
            f = getattr(self, action['action_type'].lower(), lambda **k: None)
            f(**action)


    def attack(self, to, **_):
        x, y = to
        self.game_map[y][x].enemy = False

    def move(self, unit_id, direction, **_):
        dx, dy = direction
        x, y = self.units[unit_id]
        self.game_map[y][x].units.remove(unit_id)
        x += dx
        y += dy
        self.units[unit_id] = (x, y)
        self.game_map[y][x].units.append(unit_id)


if __name__ == "__main__":
    #from script import Bot
    from bot import Bot
    with open('map.txt') as fh:
        game_map = Game(fh, Bot())
        game_map.run()
