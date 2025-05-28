
import pytest

from src.map_algorithms.pathfinding import PathFinder
from src.world_map import WorldMap


@pytest.fixture
def path_finder():
    return PathFinder()


@pytest.fixture
def map_5x5_all_wall():
    # Inner 3x3 area
    world_map = WorldMap(5, 5)
    for y in range(5):
        for x in range(5):
            world_map.set_tile_type(x, y, "wall")
    return world_map


# Tests for find_furthest_point
def test_find_furthest_point_simple_line(path_finder, map_5x5_all_wall):
    # Inner: (1,1) to (3,3)
    # Make a line: (1,1) - (1,2) - (1,3) floor
    map_5x5_all_wall.set_tile_type(1, 1, "floor")
    map_5x5_all_wall.set_tile_type(1, 2, "floor")
    map_5x5_all_wall.set_tile_type(1, 3, "floor")

    start_pos = (1, 1)
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, start_pos, 5, 5)
    assert furthest == (1, 3)

    start_pos = (1, 3)
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, start_pos, 5, 5)
    assert furthest == (1, 1)

    start_pos = (1, 2)
    # Furthest could be (1,1) or (1,3) - both are distance 1
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, start_pos, 5, 5)
    assert furthest in [(1, 1), (1, 3)]


def test_find_furthest_point_l_shape(path_finder, map_5x5_all_wall):
    # (1,1) (1,2) (1,3) (2,3) (3,3)
    map_5x5_all_wall.set_tile_type(1, 1, "floor")
    map_5x5_all_wall.set_tile_type(1, 2, "floor")
    map_5x5_all_wall.set_tile_type(1, 3, "floor")
    map_5x5_all_wall.set_tile_type(2, 3, "floor")
    map_5x5_all_wall.set_tile_type(3, 3, "floor")

    start_pos = (1, 1)
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, start_pos, 5, 5)
    assert furthest == (3, 3)  # Dist 4

    start_pos = (3, 3)
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, start_pos, 5, 5)
    assert furthest == (1, 1)  # Dist 4


def test_find_furthest_point_no_path_or_single_point(path_finder, map_5x5_all_wall):
    map_5x5_all_wall.set_tile_type(1, 1, "floor")
    # Start from a floor tile, but no other floor tiles exist in inner area
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, (1, 1), 5, 5)
    assert furthest == (1, 1)

    # Start from a non-floor tile (wall)
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, (2, 2), 5, 5)
    assert furthest == (2, 2)  # Returns start_pos if start_pos is not floor

    # Start from out of inner bounds
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, (0, 0), 5, 5)
    assert furthest == (0, 0)


def test_find_furthest_point_empty_map_no_floor(path_finder, map_5x5_all_wall):
    # map_5x5_all_wall is already all walls in inner area
    start_pos = (1, 1)  # which is a wall
    furthest = path_finder.find_furthest_point(map_5x5_all_wall, start_pos, 5, 5)
    assert furthest == start_pos  # Returns start_pos as it's not floor


# Tests for carve_bresenham_line
def test_carve_bresenham_line_horizontal(path_finder, map_5x5_all_wall):
    start_pos = (1, 2)
    end_pos = (3, 2)  # Inner map points: (1,2), (2,2), (3,2)
    path_finder.carve_bresenham_line(map_5x5_all_wall, start_pos, end_pos, 5, 5)
    assert map_5x5_all_wall.get_tile(1, 2).type == "floor"
    assert map_5x5_all_wall.get_tile(2, 2).type == "floor"
    assert map_5x5_all_wall.get_tile(3, 2).type == "floor"
    assert map_5x5_all_wall.get_tile(1, 1).type == "wall"  # Check others are untouched


def test_carve_bresenham_line_vertical(path_finder, map_5x5_all_wall):
    start_pos = (2, 1)
    end_pos = (2, 3)
    path_finder.carve_bresenham_line(map_5x5_all_wall, start_pos, end_pos, 5, 5)
    assert map_5x5_all_wall.get_tile(2, 1).type == "floor"
    assert map_5x5_all_wall.get_tile(2, 2).type == "floor"
    assert map_5x5_all_wall.get_tile(2, 3).type == "floor"
    assert map_5x5_all_wall.get_tile(1, 1).type == "wall"


def test_carve_bresenham_line_diagonal(path_finder, map_5x5_all_wall):
    start_pos = (1, 1)
    end_pos = (3, 3)
    path_finder.carve_bresenham_line(map_5x5_all_wall, start_pos, end_pos, 5, 5)
    # Expected path for Bresenham (1,1)-(3,3) can vary slightly based on
    # implementation (e.g., (1,1), (1,2), (2,2), (2,3), (3,3)).
    # The current implementation uses round(), which should generally hit
    # (1,1), (2,2), (3,3) for a perfect diagonal.
    # Let's check points on the direct line:
    assert map_5x5_all_wall.get_tile(1, 1).type == "floor"
    assert map_5x5_all_wall.get_tile(2, 2).type == "floor"
    assert map_5x5_all_wall.get_tile(3, 3).type == "floor"
    # Check a point that should NOT be on a perfect diagonal line
    assert map_5x5_all_wall.get_tile(1, 2).type == "wall"
    assert map_5x5_all_wall.get_tile(2, 1).type == "wall"


def test_carve_bresenham_line_single_point(path_finder, map_5x5_all_wall):
    start_pos = (2, 2)
    path_finder.carve_bresenham_line(map_5x5_all_wall, start_pos, start_pos, 5, 5)
    assert map_5x5_all_wall.get_tile(2, 2).type == "floor"
    assert map_5x5_all_wall.get_tile(1, 1).type == "wall"


def test_carve_bresenham_line_includes_edges_if_specified(path_finder):
    # Test carving to the very edge of the map (0 or width-1).
    # carve_bresenham_line allows this, though WorldGenerator typically
    # uses it for inner points.
    map_3x3 = WorldMap(3, 3)
    for y in range(3):
        for x in range(3):
            map_3x3.set_tile_type(x, y, "wall")

    path_finder.carve_bresenham_line(map_3x3, (0, 0), (2, 2), 3, 3)
    assert map_3x3.get_tile(0, 0).type == "floor"
    assert map_3x3.get_tile(1, 1).type == "floor"
    assert map_3x3.get_tile(2, 2).type == "floor"

    map_3x3_v2 = WorldMap(3, 3)
    for y in range(3):
        for x in range(3):
            map_3x3_v2.set_tile_type(x, y, "wall")
    path_finder.carve_bresenham_line(map_3x3_v2, (0, 1), (2, 1), 3, 3)
    # Horizontal line on edge
    assert map_3x3_v2.get_tile(0, 1).type == "floor"
    assert map_3x3_v2.get_tile(1, 1).type == "floor"
    assert map_3x3_v2.get_tile(2, 1).type == "floor"
