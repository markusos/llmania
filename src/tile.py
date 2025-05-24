ENTITY_SYMBOLS = {
    "monster": "👹",
    "item": "💰",
}
TILE_SYMBOLS = {
    "wall": "#",  # Using '#' for wall character as per new instructions
    "floor": ".",  # Using '.' for floor character as per new instructions
    "unknown": "?",
}
# Note: TILE_REPRESENTATIONS is removed as its functionality is replaced
# by the above and new logic.
# The player symbol "🧑" was in TILE_REPRESENTATIONS but not used by
# Tile class directly. It's handled in GameEngine.render_map.


class Tile:
    def __init__(
        self, tile_type="floor", monster=None, item=None
    ):  # Parameter name is tile_type for clarity
        self.type = tile_type  # Attribute name is type
        self.monster = monster
        self.item = item

    def get_display_info(self):
        FLOOR_SYMBOL = TILE_SYMBOLS["floor"]
        grid = [[FLOOR_SYMBOL for _ in range(3)] for _ in range(3)]
        display_type = "unknown"

        if self.monster:
            return (ENTITY_SYMBOLS["monster"], "monster")
        elif self.item:
            return (ENTITY_SYMBOLS["item"], "item")
        elif self.type == "wall":
            return (TILE_SYMBOLS["wall"], "wall")
        elif self.type == "floor":
            return (TILE_SYMBOLS["floor"], "floor")
        else:
            return (TILE_SYMBOLS["unknown"], "unknown")
