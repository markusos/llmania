from src.tile import Tile, ENTITY_SYMBOLS, TILE_SYMBOLS


def test_tile_initialization_default():
    tile = Tile()
    assert tile.type == "floor" # Changed from tile_type to type
    assert tile.item is None
    assert tile.monster is None


def test_tile_initialization_custom():
    tile = Tile("wall")
    assert tile.type == "wall" # Changed from tile_type to type
    assert tile.item is None
    assert tile.monster is None


def test_get_display_info_monster(): # Renamed test, method and expected symbol
    tile = Tile()
    tile.monster = "Goblin"
    char, display_type = tile.get_display_info()
    assert char == ENTITY_SYMBOLS["monster"] # "👹"
    assert display_type == "monster_on_floor"


def test_get_display_info_item(): # Renamed test, method and expected symbol
    tile = Tile()
    tile.item = "Potion"
    char, display_type = tile.get_display_info()
    assert char == ENTITY_SYMBOLS["item"] # "💰"
    assert display_type == "item_on_floor"


def test_get_display_info_wall(): # Renamed test, method and expected symbol
    tile = Tile("wall")
    char, display_type = tile.get_display_info()
    assert char == TILE_SYMBOLS["wall"] # "#"
    assert display_type == "wall"


def test_get_display_info_floor(): # Renamed test, method and expected symbol
    tile = Tile("floor")
    char, display_type = tile.get_display_info()
    assert char == TILE_SYMBOLS["floor"] # "."
    assert display_type == "floor"


def test_get_display_info_unknown(): # Renamed test, method and expected symbol
    tile = Tile("unknown_type")
    char, display_type = tile.get_display_info()
    assert char == TILE_SYMBOLS["unknown"] # "?"
    assert display_type == "unknown"


def test_get_display_info_item_and_monster(): # Renamed test and method
    tile = Tile()
    tile.monster = "Dragon"
    tile.item = "Gold"
    char, display_type = tile.get_display_info() # Monster should take precedence
    assert char == ENTITY_SYMBOLS["monster"]
    assert display_type == "monster_on_floor"
