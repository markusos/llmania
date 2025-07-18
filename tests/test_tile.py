from unittest.mock import MagicMock

from src.tile import ENTITY_SYMBOLS, TILE_SYMBOLS, Tile


def test_tile_initialization_default():
    tile = Tile()
    assert tile.type == "floor"
    assert tile.item is None
    assert tile.monster is None


def test_tile_initialization_custom():
    tile = Tile(tile_type="wall")
    assert tile.type == "wall"
    assert tile.item is None
    assert tile.monster is None


def test_get_display_info_monster():
    mock_monster = MagicMock()
    tile = Tile(monster=mock_monster)
    symbol, display_type = tile.get_display_info()
    assert symbol == ENTITY_SYMBOLS["monster"]
    assert display_type == "monster"


def test_get_display_info_item():
    mock_item = MagicMock()
    tile = Tile(item=mock_item)
    symbol, display_type = tile.get_display_info()
    assert symbol == ENTITY_SYMBOLS["item"]
    assert display_type == "item"


def test_get_display_info_wall():
    tile = Tile(tile_type="wall")
    symbol, display_type = tile.get_display_info()
    assert symbol == TILE_SYMBOLS["wall"]
    assert display_type == "wall"


def test_get_display_info_floor():
    tile = Tile(tile_type="floor")
    symbol, display_type = tile.get_display_info()
    assert symbol == TILE_SYMBOLS["floor"]
    assert display_type == "floor"


def test_get_display_info_unknown():
    tile = Tile(tile_type="unknown_type")
    symbol, display_type = tile.get_display_info()
    assert symbol == TILE_SYMBOLS["unknown"]
    assert display_type == "unknown"


def test_get_display_info_item_and_monster():
    # Monster should take precedence
    mock_monster = MagicMock()
    mock_item = MagicMock()
    tile = Tile(monster=mock_monster, item=mock_item)
    symbol, display_type = tile.get_display_info()
    assert symbol == ENTITY_SYMBOLS["monster"]
    assert display_type == "monster"
