# Defines the symbols used for rendering different entities and tile types on the map.
ENTITY_SYMBOLS = {
    "monster": "M",  # Symbol for monsters
    "item": "$",  # Symbol for items
}
TILE_SYMBOLS = {
    "wall": "#",  # Symbol for wall tiles
    "floor": ".",  # Symbol for floor tiles
    "unknown": "?",  # Symbol for unknown or undefined tiles
    "fog": " ", # Symbol for unexplored areas in AI mode
}
# Note: The TILE_REPRESENTATIONS dictionary was previously here but has been
# integrated into TILE_SYMBOLS and ENTITY_SYMBOLS for clarity and direct use.
# The player symbol "@" is handled by the Renderer, not directly by the Tile class.


class Tile:
    """
    Represents a single tile on the game map.

    A tile can have a base type (e.g., "wall", "floor") and can optionally
    contain a monster or an item. The tile's appearance is determined by its
    content, with monsters taking precedence over items, and items over the
    base tile type.

    Attributes:
        type (str): The base type of the tile (e.g., "floor", "wall").
        monster (Optional[Monster]): The monster occupying this tile, if any.
        item (Optional[Item]): The item on this tile, if any (and no monster).
    """

    def __init__(
        self, tile_type: str = "floor", monster=None, item=None
    ):  # monster and item types are Optional[Monster] and Optional[Item]
        """
        Initializes a Tile instance.

        Args:
            tile_type: The base type of the tile. Defaults to "floor".
            monster: A Monster object if a monster is on this tile. Defaults to None.
            item: An Item object if an item is on this tile. Defaults to None.
        """
        self.type = tile_type  # The base type of the tile (e.g., "wall", "floor")
        self.monster = monster  # Monster object on the tile, if any
        self.item = item  # Item object on the tile, if any
        self.is_explored = False # True if the AI has seen this tile

    def get_display_info(self, for_ai_fog: bool = False) -> tuple[str, str]:
        """
        Determines the character symbol and display type for rendering this tile.

        The display priority is: Monster > Item > Tile Type.

        Returns:
            A tuple (symbol, display_type_str), where:
                - symbol (str): The character to display (e.g., "M", "$", "#", ".").
                - display_type_str (str): A string indicating the type of content
                  for coloring purposes (e.g., "monster", "item", "wall", "floor", "fog").
        """
        if for_ai_fog and not self.is_explored:
            return (TILE_SYMBOLS["fog"], "fog")

        if self.monster:
            return (ENTITY_SYMBOLS["monster"], "monster")
        elif self.item:
            return (ENTITY_SYMBOLS["item"], "item")
        elif self.type == "wall":
            return (TILE_SYMBOLS["wall"], "wall")
        elif self.type == "floor":
            return (TILE_SYMBOLS["floor"], "floor")
        else:
            # Fallback for any unknown tile type
            return (TILE_SYMBOLS["unknown"], "unknown")
