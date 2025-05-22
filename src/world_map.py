from src.item import Item
from src.monster import Monster
from src.tile import Tile


class WorldMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [
            [Tile(tile_type="floor") for _ in range(width)] for _ in range(height)
        ]

    def get_tile(self, x: int, y: int) -> Tile | None:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def set_tile_type(self, x: int, y: int, tile_type: str) -> bool:
        tile = self.get_tile(x, y)
        if tile:
            tile.type = tile_type
            return True
        return False

    def is_valid_move(self, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)
        if tile and tile.type != "wall":
            return True
        return False

    def place_item(self, item: Item, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)
        if tile and tile.item is None:
            tile.item = item
            return True
        return False

    def remove_item(self, x: int, y: int) -> Item | None:
        tile = self.get_tile(x, y)
        if tile and tile.item is not None:
            item = tile.item
            tile.item = None
            return item
        return None

    def place_monster(self, monster: Monster, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)
        if tile and tile.monster is None:
            tile.monster = monster
            monster.x = x
            monster.y = y
            return True
        return False

    def remove_monster(self, x: int, y: int) -> Monster | None:
        tile = self.get_tile(x, y)
        if tile and tile.monster is not None:
            monster = tile.monster
            tile.monster = None
            return monster
        return None
