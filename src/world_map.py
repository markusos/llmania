from src.item import Item
from src.monster import Monster
from src.player import Player
from src.tile import Tile


class WorldMap:
    """
    Represents the game map as a 2D grid of Tiles.

    Attributes:
        width (int): The width of the map in tiles.
        height (int): The height of the map in tiles.
        grid (List[List[Tile]]): The 2D list representing the map, where
                                 grid[y][x] is the Tile at coordinates (x,y).
    """

    def __init__(self, width: int, height: int):
        """
        Initializes a new WorldMap of the given dimensions.
        By default, all tiles are initialized as "floor" tiles.
        This might be overridden by WorldGenerator (fills with walls first).

        Args:
            width: The width of the map.
            height: The height of the map.
        """
        self.width = width
        self.height = height
        # Initialize the grid with default Tile objects (e.g., floor tiles).
        # WorldGenerator will typically override these with specific types like "wall".
        self.grid = [
            [Tile(tile_type="floor") for _ in range(width)] for _ in range(height)
        ]

    def iter_coords(self):
        """Returns an iterator over all coordinates in the map."""
        for y in range(self.height):
            for x in range(self.width):
                yield y, x

    def is_in_bounds(self, x: int, y: int) -> bool:
        """
        Checks if the given coordinates are within the map's bounds.

        Args:
            x: The x-coordinate to check.
            y: The y-coordinate to check.

        Returns:
            True if (x, y) is within the map's bounds, False otherwise.
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> Tile | None:
        """
        Retrieves the Tile object at the specified coordinates.

        Args:
            x: The x-coordinate of the tile.
            y: The y-coordinate of the tile.

        Returns:
            The Tile object if the coordinates are within map bounds, otherwise None.
        """
        if self.is_in_bounds(x, y):
            return self.grid[y][x]
        return None  # Coordinates are out of bounds

    def set_tile_type(self, x: int, y: int, tile_type: str) -> bool:
        """
        Sets the base type of the tile at the specified coordinates.

        Args:
            x: The x-coordinate of the tile.
            y: The y-coordinate of the tile.
            tile_type: The new type for the tile (e.g., "wall", "floor").

        Returns:
            True if tile type was set, False if coords are out of bounds.
        """
        tile = self.get_tile(x, y)
        if tile:
            tile.type = tile_type  # Update the tile's base type
            return True
        return False  # Tile not found (out of bounds)

    def is_valid_move(self, x: int, y: int) -> bool:
        """
        Checks if a move to the specified coordinates is valid.
        A move is valid if the coordinates are within map bounds and the
        tile is not a "wall".

        Args:
            x: The target x-coordinate.
            y: The target y-coordinate.

        Returns:
            True if the move is valid, False otherwise.
        """
        tile = self.get_tile(x, y)
        # Valid if tile exists and not wall (entities don't block movement here).
        if tile and (tile.type != "wall" or tile.is_portal):
            return True
        return False

    def place_item(self, item: Item, x: int, y: int) -> bool:
        """
        Places an Item on the tile at the specified coordinates.
        Item can only be placed if tile exists and does not already contain an item.

        Args:
            item: The Item object to place.
            x: The x-coordinate for placement.
            y: The y-coordinate for placement.

        Returns:
            True if item placed, False otherwise (e.g., out of bounds, occupied).
        """
        tile = self.get_tile(x, y)
        if tile and tile.item is None:  # Check if tile exists and is empty of items
            tile.item = item
            return True
        return False  # Tile not found or already has an item

    def remove_item(self, x: int, y: int) -> Item | None:
        """
        Removes an Item from the tile at the specified coordinates.

        Args:
            x: The x-coordinate of the tile.
            y: The y-coordinate of the tile.

        Returns:
            Removed Item object, or None if no item on tile or out of bounds.
        """
        tile = self.get_tile(x, y)
        if tile and tile.item is not None:
            item_removed = tile.item
            tile.item = None  # Clear the item from the tile
            return item_removed
        return None  # No item to remove or tile not found

    def place_monster(self, monster: Monster, x: int, y: int) -> bool:
        """
        Places a Monster on the tile at the specified coordinates.
        Monster can only be placed if tile exists and does not already contain one.
        Also updates the monster's internal x, y coordinates.

        Args:
            monster: The Monster object to place.
            x: The x-coordinate for placement.
            y: The y-coordinate for placement.

        Returns:
            True if the monster was successfully placed, False otherwise.
        """
        tile = self.get_tile(x, y)
        if (
            tile and tile.monster is None
        ):  # Check if tile exists and is empty of monsters
            tile.monster = monster
            monster.x = x  # Update monster's own position tracking
            monster.y = y
            return True
        return False  # Tile not found or already has a monster

    def remove_monster(self, x: int, y: int) -> Monster | None:
        """
        Removes a Monster from the tile at the specified coordinates.

        Args:
            x: The x-coordinate of the tile.
            y: The y-coordinate of the tile.

        Returns:
            Removed Monster object, or None if no monster on tile or out of bounds.
        """
        tile = self.get_tile(x, y)
        if tile and tile.monster is not None:
            monster_removed = tile.monster
            tile.monster = None  # Clear the monster from the tile
            return monster_removed
        return None  # No monster to remove or tile not found

    def place_player(self, player: Player, x: int, y: int) -> bool:
        """
        Places the Player on the tile at the specified coordinates.
        """
        tile = self.get_tile(x, y)
        if tile and tile.player is None:
            tile.player = player
            return True
        return False

    def remove_player(self, x: int, y: int) -> Player | None:
        """
        Removes the Player from the tile at the specified coordinates.
        """
        tile = self.get_tile(x, y)
        if tile and tile.player is not None:
            player_removed = tile.player
            tile.player = None
            return player_removed
        return None

    def get_monsters(self):
        """
        Returns a list of all monsters on the map.
        """
        monsters = []
        for y, x in self.iter_coords():
            tile = self.get_tile(x, y)
            if tile and tile.monster:
                monsters.append(tile.monster)
        return monsters

    def get_map_as_string(self, renderer, message_log) -> list[str]:
        """
        Returns a string representation of the map for debugging.
        """
        return renderer.render_all(
            player_x=-1,
            player_y=-1,
            player_health=0,
            world_map_to_render=self,
            input_mode="",
            current_command_buffer="",
            message_log=message_log,
            debug_render_to_list=True,
            current_floor_id=0,  # Floor ID doesn't matter for this
            apply_fog=False,
        )
