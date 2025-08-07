# Defines the symbols used for rendering different entities and tile types on the map.
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.items import Item
    from src.monster import Monster
    from src.player import Player

# Defines the symbols used for rendering different entities and tile types on the map.
ENTITY_SYMBOLS = {
    "monster": "M",  # Symbol for monsters
    "item": "$",  # Symbol for items
}
TILE_SYMBOLS = {
    "wall": "#",  # Symbol for wall tiles
    "floor": ".",  # Symbol for floor tiles
    "portal": "▢",  # Symbol for portal tiles
    "unknown": "?",  # Symbol for unknown or undefined tiles
    "fog": " ",  # Symbol for unexplored areas in AI mode
}
# Note: The TILE_REPRESENTATIONS dictionary was previously here but has been
# integrated into TILE_SYMBOLS and ENTITY_SYMBOLS for clarity and direct use.
# The player symbol "@" is handled by the Renderer, not directly by the Tile class.


class Tile:
    """
    Represents a single tile on the game map.

    A tile can have a base type (e.g., "wall", "floor", "portal") and can optionally
    contain a monster or an item. The tile's appearance is determined by its
    content, with monsters taking precedence over items, and items over the
    base tile type.

    Attributes:
        type (str): The base type of the tile (e.g., "floor", "wall", "portal").
        monster (Optional[Monster]): The monster occupying this tile, if any.
        item (Optional[Item]): The item on this tile, if any (and no monster).
        player (Optional[Player]): The player on this tile, if any.
        is_explored (bool): True if this tile has been seen by the player/AI.
        is_portal (bool): True if this tile is a portal.
        portal_to_floor_id (Optional[int]): If is_portal is True, this stores the
                                           ID of the floor this portal leads to.
    """

    def __init__(
        self,
        tile_type: str = "floor",
        monster: "Optional[Monster]" = None,
        item: "Optional[Item]" = None,
        player: "Optional[Player]" = None,
        portal_to_floor_id: Optional[int] = None,
    ):
        """
        Initializes a Tile instance.

        Args:
            tile_type: The base type of the tile. Defaults to "floor".
            monster: A Monster object if a monster is on this tile. Defaults to None.
            item: An Item object if an item is on this tile. Defaults to None.
            player: A Player object if the player is on this tile. Defaults to None.
            portal_to_floor_id: If this tile is a portal, the ID of the target floor.
                                Defaults to None.
        """
        self.type = tile_type
        self.monster = monster
        self.item = item
        self.player = player
        self.is_explored = False
        self.is_portal = tile_type == "portal"
        self.portal_to_floor_id = portal_to_floor_id
        if self.is_portal and portal_to_floor_id is None:
            # This state should ideally be prevented by the world generator,
            # but it's a good safeguard.
            raise ValueError("Portal tile must have a portal_to_floor_id.")

    def get_display_info(self, apply_fog: bool = False) -> tuple[str, str]:
        """
        Determines the character symbol and display type for rendering this tile.
        If `apply_fog` is True and the tile hasn't been explored, it returns fog.

        The display priority is: Monster > Item > Tile Type.

        Args:
            apply_fog (bool): If True, fog of war logic is applied. Unexplored
                              tiles will be rendered as fog.

        Returns:
            A tuple (symbol, display_type_str), where:
                - symbol (str): The character to display (e.g., "M", "$", "#",
                  ".", " ").
                - display_type_str (str): A string indicating the type of content
                  for coloring purposes (e.g., "monster", "item", "wall", "floor",
                  "fog").
        """
        if apply_fog and not self.is_explored:
            return TILE_SYMBOLS["fog"], "fog"

        # If fog is not applied, we show everything regardless of exploration.
        # The display priority is: Monster > Item > Tile Type.
        if self.monster:
            return (ENTITY_SYMBOLS["monster"], "monster")
        elif self.item:
            # Items should not be on portal tiles, but if they are, they take
            # precedence.
            return (ENTITY_SYMBOLS["item"], "item")
        elif self.is_portal:  # Check for portal before generic floor/wall
            return (TILE_SYMBOLS["portal"], "portal")
        elif self.type == "wall":
            return (TILE_SYMBOLS["wall"], "wall")
        elif self.type == "floor":
            return (TILE_SYMBOLS["floor"], "floor")
        else:
            # Fallback for any unknown tile type
            return (TILE_SYMBOLS["unknown"], "unknown")
