import random
from unittest.mock import MagicMock

import pytest

from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.density import FloorDensityAdjuster
from src.world_map import WorldMap


@pytest.fixture
def setup_world():
    width, height = 10, 10
    world_map = WorldMap(width, height)
    for y in range(height):
        for x in range(width):
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                world_map.set_tile_type(x, y, "wall")
            else:
                world_map.set_tile_type(x, y, "wall")
    player_start_pos = (1, 1)
    original_win_pos = (width - 2, height - 2)
    world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")
    world_map.set_tile_type(original_win_pos[0], original_win_pos[1], "floor")

    mock_connectivity_manager = MagicMock(spec=MapConnectivityManager)
    # Ensure all necessary methods are mocked
    mock_connectivity_manager.path_exists_between = MagicMock(return_value=True)
    mock_connectivity_manager.check_connectivity = MagicMock(return_value=True)
    mock_connectivity_manager.get_reachable_floor_tiles = MagicMock(
        return_value=set([(1, 1), original_win_pos])
    )  # Basic reachability

    adjuster = FloorDensityAdjuster(
        mock_connectivity_manager, random_generator=random.Random()
    )

    return adjuster, world_map, player_start_pos, original_win_pos


def _count_floor_tiles(world_map: WorldMap) -> int:
    count = 0
    for y in range(1, world_map.height - 1):
        for x in range(1, world_map.width - 1):
            if tile := world_map.get_tile(x, y):
                if tile.type == "floor":
                    count += 1
    return count


def test_adjust_density_increase_floor_tiles(setup_world):
    adjuster, world_map, player_start_pos, original_win_pos = setup_world

    # Start with minimal floors (player_start and original_win_pos)
    for y in range(1, world_map.height - 1):
        for x in range(1, world_map.width - 1):
            if (x, y) != player_start_pos and (x, y) != original_win_pos:
                world_map.set_tile_type(x, y, "wall")

    initial_floor_count = _count_floor_tiles(world_map)  # Should be 2
    total_inner_tiles = (world_map.width - 2) * (world_map.height - 2)  # 8*8 = 64
    target_portion = 0.5
    expected_floor_tiles = int(total_inner_tiles * target_portion)  # 32

    adjuster.adjust_density(
        world_map,
        player_start_pos,
        original_win_pos,
        world_map.width,
        world_map.height,
        target_portion,
    )
    final_floor_count = _count_floor_tiles(world_map)

    assert final_floor_count >= initial_floor_count, "Floor count should not decrease."
    # Allow for deviation due to connectivity constraints and discrete tiles
    assert (
        abs(final_floor_count - expected_floor_tiles) <= total_inner_tiles * 0.1
        or final_floor_count >= expected_floor_tiles
    ), (
        f"Final floor count {final_floor_count} not close to target "
        f"{expected_floor_tiles}. Initial: {initial_floor_count}"
    )


def test_adjust_density_decrease_floor_tiles(setup_world):
    adjuster, world_map, player_start_pos, original_win_pos = setup_world

    for y in range(1, world_map.height - 1):
        for x in range(1, world_map.width - 1):
            world_map.set_tile_type(x, y, "floor")  # Make all inner tiles floor

    initial_floor_count = _count_floor_tiles(world_map)  # Should be 64
    total_inner_tiles = (world_map.width - 2) * (world_map.height - 2)
    target_portion = 0.2
    expected_floor_tiles = int(
        total_inner_tiles * target_portion
    )  # 0.2 * 64 = 12.8 -> 12

    adjuster.adjust_density(
        world_map,
        player_start_pos,
        original_win_pos,
        world_map.width,
        world_map.height,
        target_portion,
    )
    final_floor_count = _count_floor_tiles(world_map)

    assert final_floor_count <= initial_floor_count, "Floor count should not increase."
    # Allow some flexibility due to connectivity preservation
    assert final_floor_count >= expected_floor_tiles - (
        total_inner_tiles * 0.05
    ) and final_floor_count <= expected_floor_tiles + (
        total_inner_tiles * 0.15
    ), f"Final {final_floor_count} not close to target {expected_floor_tiles}"


def test_adjust_density_with_protected_coords(setup_world):
    adjuster, world_map, player_start_pos, original_win_pos = setup_world
    protected = [(2, 2), (3, 3)]
    for x, y in protected:
        world_map.set_tile_type(x, y, "wall")  # Ensure they start as walls

    adjuster.adjust_density(
        world_map,
        player_start_pos,
        original_win_pos,
        world_map.width,
        world_map.height,
        0.5,
        protected_coords=protected,
    )

    for x, y in protected:
        tile = world_map.get_tile(x, y)
        assert tile is not None
        assert tile.type == "wall", (
            f"Protected coordinate ({x},{y}) was modified from wall."
        )

    # Player start and win pos are implicitly protected and should remain floor
    assert world_map.get_tile(player_start_pos[0], player_start_pos[1]).type == "floor"  # type: ignore
    assert world_map.get_tile(original_win_pos[0], original_win_pos[1]).type == "floor"  # type: ignore


def test_density_adjustment_respects_minimal_connectivity(setup_world):
    adjuster, _, _, _ = setup_world  # We use the adjuster from the fixture
    small_width, small_height = 5, 5
    small_map = WorldMap(small_width, small_height)
    for y in range(small_height):  # Fill with walls
        for x in range(small_width):
            small_map.set_tile_type(x, y, "wall")

    player_s, win_s = (1, 1), (3, 3)  # These will be protected
    path_coords = [(1, 1), (1, 2), (2, 2), (3, 2), (3, 3)]
    for x, y in path_coords:
        small_map.set_tile_type(x, y, "floor")

    # Adjuster's mock connectivity manager will return True for path_exists_between
    adjuster.adjust_density(
        small_map, player_s, win_s, small_width, small_height, 0.1
    )  # Target very few floors

    for x, y in path_coords:
        tile = small_map.get_tile(x, y)
        assert tile is not None and tile.type == "floor", (
            f"Path tile ({x},{y}) was changed to {tile.type if tile else 'None'}."
        )  # type: ignore

    final_floors = _count_floor_tiles(small_map)
    # It should keep at least the path tiles, plus player_s and win_s if not in
    # path_coords (they are here)
    # The algorithm might keep slightly more to ensure connectivity.
    assert final_floors >= len(path_coords), (
        f"Final floor count {final_floors} is less than min path {len(path_coords)}."
    )
