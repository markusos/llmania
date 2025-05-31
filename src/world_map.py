from item import Item
from monster import Monster
from tile import Tile


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

    def get_tile(self, x: int, y: int) -> Tile | None:
        """
        Retrieves the Tile object at the specified coordinates.

        Args:
            x: The x-coordinate of the tile.
            y: The y-coordinate of the tile.

        Returns:
            The Tile object if the coordinates are within map bounds, otherwise None.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
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
        if tile and tile.type != "wall":
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
