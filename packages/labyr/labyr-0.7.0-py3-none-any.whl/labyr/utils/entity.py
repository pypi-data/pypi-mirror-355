from . import getchar


class Player:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y


class EntMan:
    """entity manager"""

    def __init__(self, levels: dict[int, list[list[str]]], chars) -> None:
        self.lvls = levels
        self._entities = {}

        def retTable(matrix: list[list[str]]):
            out = {}
            player_char = getchar(chars, "player")[0]
            for y, row in enumerate(matrix):
                for x, char in enumerate(row):
                    if char == player_char:
                        out["player"] = Player(x, y)
            return out

        for lvl, lmap in levels.items():
            self._entities[lvl] = retTable(lmap)

    def get(self, lvl: int, entity: str):
        return self._entities[lvl][entity]


def handlemove(chars, curMap: list, entity: Player, move: str):
    if not isinstance(entity, Player):
        return

    x, y = entity.x, entity.y
    move_offsets = {"w": (0, 1), "a": (-1, 0), "s": (0, -1), "d": (1, 0)}
    dx, dy = move_offsets.get(move, (0, 0))
    nx, ny = x + dx, y + dy

    if 0 <= ny < len(curMap) and 0 <= nx < len(curMap[0]):
        target = curMap[ny][nx]
        player_char = getchar(chars, "player")[0]
        space_char = getchar(chars, "space")[0]
        if target in (space_char,):
            curMap[y][x] = space_char
            curMap[ny][nx] = player_char
            entity.x, entity.y = nx, ny
