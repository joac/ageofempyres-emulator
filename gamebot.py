import re

HQ_expression = re.compile(r"HQ:(\d+)Id:(\d+)")
UNIT_expression = re.compile(r"U:(\d+)Id:(\d+)")
BLOCK_expression = re.compile(r"B")


class InvalidActionException(Exception):
    pass


class PointInMap(object):

    def __init__(self, coord_x, coord_y):
        self.x = coord_x
        self.y = coord_y

    def __add__(self, other):
        return PointInMap(coord_x=self.x + other.x, coord_y=self.y + other.y)

    def as_tuple(self):
        return (self.x, self.y)


class PlayerUnit(PointInMap):

    def __init__(self, unit_id, coord_x, coord_y):
        self.unit_id = unit_id
        super(PlayerUnit, self).__init__(coord_x=coord_x, coord_y=coord_y)


class Tile(PointInMap):

    def __init__(self, player_id, content, coord_x, coord_y):
        super(Tile, self).__init__(coord_x, coord_y)
        self.units = []
        self.enemies_count = 0
        self.enemy_hq = False
        self.own_hq = False
        self.reachable = False
        self._parse_tile_string(player_id, content)

    def _parse_tile_string(self, player_id, content_str):

        for p_id, _ in HQ_expression.findall(content_str):
            self.own_hq = p_id == player_id
            self.enemy_hq = p_id != player_id

        for p_id, unit_id in UNIT_expression.findall(content_str):
            if p_id == player_id:
                self.units.append(PlayerUnit(unit_id=unit_id, coord_x=self.x, coord_y=self.y))
            else:
                self.enemies_count += 1

        self.reachable = BLOCK_expression.match(content_str) is None


class Map(dict):
    pass


class GameBot(object):

    NW = PointInMap(-1, -1)
    N = PointInMap(0, -1)
    NE = PointInMap(1, -1)
    E = PointInMap(1, 0)
    SE = PointInMap(1, 1)
    S = PointInMap(0, 1)
    SW = PointInMap(-1, 1)
    W = PointInMap(-1, 0)

    DIRECTIONS = [NW, N, NE, W, SE, S, SW, W]

    def parse(self, feedback):
        """:feedback: <dict> that has
        {
           'payer_num': <player_id>,
           'map': <arena_map> [
               [<tile_str>, .... ],
           ],
        }
        """
        game_map = Map()
        player_id = str(feedback['player_num'])
        for y, row in enumerate(feedback['map']):
            for x, tile_str in enumerate(row):
                game_map[x, y] = Tile(
                    player_id=player_id,
                    content=tile_str,
                    coord_x=x,
                    coord_y=y
                )
        self.game_map = game_map
        return player_id, game_map

    def on_turn(self, feedback):
        self.actions = []
        player_id, game_map = self.parse(feedback)
        self.play(player_id, game_map)
        return {'ACTIONS': self.actions}

    def attack(self, tile, direction):
        target_point = (tile + direction).as_tuple()
        target_tile = self.game_map.get(target_point)
        self.validate_target(tile + direction)
        if not target_tile.enemies_count:
            raise InvalidActionException("Target tile is empty")
        self.actions.append({
            'action_type': 'ATTACK',
            'from': tile.as_tuple(),
            'to': target_point,
        })

    def validate_target(self, target_point):
        """Validates that a tile is inside the map and reachable"""
        coordinates = target_point.as_tuple()
        if coordinates not in self.game_map:
            raise InvalidActionException("Out of map")
        if not self.game_map[coordinates].reachable:
            raise InvalidActionException("Unreacheable")

    def move(self, unit, direction):
        target_point = (unit + direction)
        self.validate_target(target_point)

        if self.game_map[target_point.as_tuple()].enemies_count:
            raise InvalidActionException("Target not empty")

        self.actions.append({
            'action_type': 'MOVE',
            'unit_id': unit.unit_id,
            'direction': direction.as_tuple(),
        })
