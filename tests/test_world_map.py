import pytest

from item import Item
from monster import Monster
from tile import Tile
from world_map import WorldMap


# Test Initialization
def test_world_map_initialization():
    w_map = WorldMap(width=10, height=8)
    assert w_map.width == 10
    assert w_map.height == 8
    assert len(w_map.grid) == 8  # height = rows
    assert len(w_map.grid[0]) == 10  # width = columns
    for y in range(w_map.height):
        for x in range(w_map.width):
            assert isinstance(w_map.grid[y][x], Tile)
            assert w_map.grid[y][x].type == "floor"


# Test get_tile
def test_get_tile_valid():
    w_map = WorldMap(width=5, height=5)
    tile = w_map.get_tile(2, 3)
    assert tile is not None
    assert isinstance(tile, Tile)
    assert tile == w_map.grid[3][2]


def test_get_tile_invalid():
    w_map = WorldMap(width=5, height=5)
    assert w_map.get_tile(-1, 2) is None
    assert w_map.get_tile(2, -1) is None
    assert w_map.get_tile(5, 2) is None  # x out of bounds
    assert w_map.get_tile(2, 5) is None  # y out of bounds


# Test set_tile_type
def test_set_tile_type_valid():
    w_map = WorldMap(width=3, height=3)
    assert w_map.set_tile_type(1, 1, "wall") is True
    tile = w_map.get_tile(1, 1)
    assert tile.type == "wall"


def test_set_tile_type_invalid():
    w_map = WorldMap(width=3, height=3)
    assert w_map.set_tile_type(3, 1, "wall") is False  # x out of bounds
    assert w_map.set_tile_type(1, 3, "wall") is False  # y out of bounds
    # Ensure the type was not changed for an in-bounds tile if an
    # out-of-bounds was attempted
    tile_in_bounds = w_map.get_tile(0, 0)
    assert tile_in_bounds.type == "floor"


# Test is_valid_move
def test_is_valid_move_floor():
    w_map = WorldMap(width=3, height=3)
    assert w_map.is_valid_move(1, 1) is True  # Default is floor


def test_is_valid_move_wall():
    w_map = WorldMap(width=3, height=3)
    w_map.set_tile_type(1, 1, "wall")
    assert w_map.is_valid_move(1, 1) is False


def test_is_valid_move_out_of_bounds():
    w_map = WorldMap(width=3, height=3)
    assert w_map.is_valid_move(3, 1) is False
    assert w_map.is_valid_move(1, 3) is False
    assert w_map.is_valid_move(-1, 1) is False


# Test place_item and remove_item
@pytest.fixture
def sample_item():
    return Item("Potion", "Heals 10 HP", {"type": "heal", "amount": 10})


def test_place_item_valid_empty_tile(sample_item):
    w_map = WorldMap(width=5, height=5)
    assert w_map.place_item(sample_item, 2, 2) is True
    tile = w_map.get_tile(2, 2)
    assert tile.item == sample_item
    assert tile.item.name == "Potion"


def test_place_item_invalid_coordinates(sample_item):
    w_map = WorldMap(width=5, height=5)
    assert w_map.place_item(sample_item, 5, 2) is False  # x out of bounds
    assert w_map.place_item(sample_item, 2, 5) is False  # y out of bounds


def test_place_item_tile_already_has_item(sample_item):
    w_map = WorldMap(width=5, height=5)
    another_item = Item("Key", "Opens a door", {})
    w_map.place_item(sample_item, 2, 2)  # Place first item
    assert w_map.place_item(another_item, 2, 2) is False  # Try to place another
    tile = w_map.get_tile(2, 2)
    assert tile.item == sample_item  # Original item should still be there


def test_remove_item_valid(sample_item):
    w_map = WorldMap(width=5, height=5)
    w_map.place_item(sample_item, 2, 2)

    removed_item = w_map.remove_item(2, 2)
    assert removed_item == sample_item
    assert removed_item.name == "Potion"
    tile = w_map.get_tile(2, 2)
    assert tile.item is None


def test_remove_item_empty_tile():
    w_map = WorldMap(width=5, height=5)
    assert w_map.remove_item(2, 2) is None  # Tile is empty


def test_remove_item_invalid_coordinates():
    w_map = WorldMap(width=5, height=5)
    assert w_map.remove_item(5, 2) is None  # x out of bounds
    assert w_map.remove_item(2, 5) is None  # y out of bounds


# Test place_monster and remove_monster
@pytest.fixture
def sample_monster():
    return Monster(
        "Goblin", health=30, attack_power=5
    )  # x,y will be set by place_monster


def test_place_monster_valid_empty_tile(sample_monster):
    w_map = WorldMap(width=5, height=5)
    assert w_map.place_monster(sample_monster, 3, 3) is True
    tile = w_map.get_tile(3, 3)
    assert tile.monster == sample_monster
    assert tile.monster.name == "Goblin"
    assert sample_monster.x == 3
    assert sample_monster.y == 3


def test_place_monster_invalid_coordinates(sample_monster):
    w_map = WorldMap(width=5, height=5)
    assert w_map.place_monster(sample_monster, 5, 3) is False  # x out of bounds
    assert w_map.place_monster(sample_monster, 3, 5) is False  # y out of bounds


def test_place_monster_tile_already_has_monster(sample_monster):
    w_map = WorldMap(width=5, height=5)
    another_monster = Monster("Orc", health=50, attack_power=10)
    w_map.place_monster(sample_monster, 3, 3)  # Place first monster
    assert w_map.place_monster(another_monster, 3, 3) is False  # Try to place another
    tile = w_map.get_tile(3, 3)
    assert tile.monster == sample_monster  # Original monster should still be there


def test_remove_monster_valid(sample_monster):
    w_map = WorldMap(width=5, height=5)
    w_map.place_monster(sample_monster, 3, 3)

    removed_monster = w_map.remove_monster(3, 3)
    assert removed_monster == sample_monster
    assert removed_monster.name == "Goblin"
    tile = w_map.get_tile(3, 3)
    assert tile.monster is None


def test_remove_monster_empty_tile():
    w_map = WorldMap(width=5, height=5)
    assert w_map.remove_monster(3, 3) is None  # Tile is empty


def test_remove_monster_invalid_coordinates():
    w_map = WorldMap(width=5, height=5)
    assert w_map.remove_monster(5, 3) is None  # x out of bounds
    assert w_map.remove_monster(3, 5) is None  # y out of bounds
