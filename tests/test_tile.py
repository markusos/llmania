from src.tile import Tile


def test_tile_initialization_default():
    tile = Tile()
    assert tile.type == "floor"
    assert tile.item is None
    assert tile.monster is None


def test_tile_initialization_custom():
    tile = Tile("wall")
    assert tile.type == "wall"
    assert tile.item is None
    assert tile.monster is None


def test_display_char_monster():
    tile = Tile()
    tile.monster = "Goblin"  # Simulate a monster
    assert tile.display_char() == "M"


def test_display_char_item():
    tile = Tile()
    tile.item = "Potion"  # Simulate an item
    assert tile.display_char() == "I"


def test_display_char_wall():
    tile = Tile("wall")
    assert tile.display_char() == "#"


def test_display_char_floor():
    tile = Tile("floor")
    assert tile.display_char() == "."


def test_display_char_unknown():
    tile = Tile("unknown_type")
    assert tile.display_char() == "?"


def test_display_char_item_and_monster():
    tile = Tile()
    tile.monster = "Dragon"
    tile.item = "Gold"
    assert tile.display_char() == "M"  # Monster should take precedence
