from gamebot import GameBot, InvalidActionException


class Bot(GameBot):

    def play(self, player_id, game_map):
        """Implement your logic here"""
        for unit in self.iterate_over_units(game_map):
            for direction in self.DIRECTIONS:
                try:
                    self.move(unit, direction)
                except InvalidActionException:
                    continue

    def iterate_over_units(self, game_map):
        for tile in game_map.itervalues():
            for unit in tile.units:
                yield unit

