class Tile:
    def __init__(self, tile_type="floor"):
        self.type = tile_type
        self.item = None
        self.monster = None

    def display_char(self):
        if self.monster is not None:
            return "M"
        elif self.item is not None:
            return "I"
        elif self.type == "wall":
            return "#"
        elif self.type == "floor":
            return "."
        else:
            return "?"
