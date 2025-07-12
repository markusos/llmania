from collections import deque
from typing import Optional

import pytest

from src.map_builders.single_floor_builder import SingleFloorBuilder
from src.world_map import WorldMap


@pytest.fixture
def single_floor_builder_factory():
    def _factory(
        width,
        height,
        seed=None,
        floor_portion=None,
        existing_map: Optional[WorldMap] = None,
    ):
        return SingleFloorBuilder(
            width, height, seed, floor_portion, existing_map=existing_map
        )

    return _factory


# Test `build` returns correct types for SingleFloorBuilder
def test_single_floor_builder_build_return_types(single_floor_builder_factory):
    builder = single_floor_builder_factory(10, 10)
    world_map, player_start, poi_pos = builder.build()
    assert isinstance(world_map, WorldMap)
    assert isinstance(player_start, tuple)
    assert len(player_start) == 2
    assert isinstance(player_start[0], int)
    assert isinstance(player_start[1], int)
    assert isinstance(poi_pos, tuple)
    assert len(poi_pos) == 2
    assert isinstance(poi_pos[0], int)
    assert isinstance(poi_pos[1], int)


# Test `build` dimensions for SingleFloorBuilder
def test_single_floor_builder_build_dimensions(single_floor_builder_factory):
    width, height = 15, 12
    builder = single_floor_builder_factory(width, height)
    world_map, _, _ = builder.build()
    assert world_map.width == width
    assert world_map.height == height


# Test `build` content for SingleFloorBuilder
def test_single_floor_builder_build_content(single_floor_builder_factory):
    width, height = 20, 20
    builder = single_floor_builder_factory(width, height, seed=123)
    world_map, player_start_pos, poi_pos = builder.build()

    px, py = player_start_pos
    player_tile = world_map.get_tile(px, py)
    assert player_tile is not None, "Player start position is out of bounds"
    assert (
        player_tile.type == "floor"
    ), f"Player start tile at {player_start_pos} is not a floor tile."

    poi_x, poi_y = poi_pos
    poi_tile = world_map.get_tile(poi_x, poi_y)
    assert poi_tile is not None, "POI position is out of bounds"
    assert poi_tile.type == "floor", f"POI tile at {poi_pos} is not a floor tile."
    if poi_tile.item:
        assert (
            poi_tile.item.name != "Amulet of Yendor"
        ), "Single floor POI should not be the final Amulet"


# BFS helper function for path verification (can be shared or duplicated)
def find_path_bfs(
    world_map: WorldMap, start_pos: tuple[int, int], end_pos: tuple[int, int]
) -> bool:
    queue = deque([(start_pos, [start_pos])])
    visited = {start_pos}
    width = world_map.width
    height = world_map.height

    while queue:
        (current_x, current_y), path = queue.popleft()

        if (current_x, current_y) == end_pos:
            return True

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_x, next_y = current_x + dx, current_y + dy
            if 0 <= next_x < width and 0 <= next_y < height:
                tile = world_map.get_tile(next_x, next_y)
                if tile and tile.type == "floor" and (next_x, next_y) not in visited:
                    visited.add((next_x, next_y))
                    queue.append(((next_x, next_y), path + [(next_x, next_y)]))
    return False


@pytest.mark.parametrize("seed_val", [None] + list(range(5)))
def test_single_floor_guaranteed_path_exists(
    single_floor_builder_factory, seed_val
):
    width, height = 10, 10
    builder = single_floor_builder_factory(width, height, seed=seed_val)
    world_map, player_start, poi_pos = builder.build()

    assert world_map.get_tile(player_start[0], player_start[1]).type == "floor", (
        f"Player start {player_start} is not floor. Seed: {seed_val}"
    )
    assert world_map.get_tile(poi_pos[0], poi_pos[1]).type == "floor", (
        f"POI position {poi_pos} is not floor. Seed: {seed_val}"
    )

    if player_start == poi_pos:
        path_found = True
    else:
        path_found = find_path_bfs(world_map, player_start, poi_pos)

    assert path_found, (
        f"No path found between player_start {player_start} and "
        f"poi_pos {poi_pos}. Seed: {seed_val}"
    )


def test_single_floor_start_poi_positions_not_on_edge(single_floor_builder_factory):
    for seed_val in range(5):
        width, height = 5, 5
        builder = single_floor_builder_factory(width, height, seed=seed_val)
        world_map, player_start, poi_pos = builder.build()

        assert (
            0 < player_start[0] < width - 1
        ), f"Player start X ({player_start[0]}) on edge. Seed: {seed_val}"
        assert (
            0 < player_start[1] < height - 1
        ), f"Player start Y ({player_start[1]}) on edge. Seed: {seed_val}"
        assert (
            0 < poi_pos[0] < width - 1
        ), f"POI pos X ({poi_pos[0]}) on edge. Seed: {seed_val}"
        assert (
            0 < poi_pos[1] < height - 1
        ), f"POI pos Y ({poi_pos[1]}) on edge. Seed: {seed_val}"


def test_single_floor_builder_valid_minimum_size(single_floor_builder_factory):
    valid_sizes = [(3, 4), (4, 3), (5, 5)]
    for width, height in valid_sizes:
        try:
            builder = single_floor_builder_factory(width, height, seed=1)
            world_map, player_start, poi_pos = builder.build()
            assert world_map.width == width
            assert world_map.height == height
            assert 0 < player_start[0] < width - 1
            assert 0 < player_start[1] < height - 1
            assert 0 < poi_pos[0] < width - 1
            assert 0 < poi_pos[1] < height - 1
            player_tile = world_map.get_tile(player_start[0], player_start[1])
            poi_tile = world_map.get_tile(poi_pos[0], poi_pos[1])
            assert player_tile.type == "floor"
            assert poi_tile.type == "floor"
        except ValueError:
            pytest.fail(
                f"SingleFloorBuilder raised ValueError for {width}x{height}"
            )


def test_single_floor_builder_invalid_small_size(single_floor_builder_factory):
    invalid_sizes = [(2, 2), (1, 5), (5, 1), (3, 3), (2, 4), (4, 2)]
    for width, height in invalid_sizes:
        with pytest.raises(ValueError, match="Map too small for gen single floor"):
            builder = single_floor_builder_factory(width, height, seed=1)
            builder.build()


def test_single_floor_outer_layer_is_always_wall(single_floor_builder_factory):
    sizes_to_test = [(4, 5), (5, 4), (10, 10)]
    for width, height in sizes_to_test:
        builder = single_floor_builder_factory(width, height, seed=1)
        world_map, _, _ = builder.build()
        for x_coord in range(width):
            msg_top = f"Top edge at ({x_coord},0) not wall for {width}x{height}"
            msg_bottom = f"Bottom edge at ({x_coord},{height - 1}) not wall for {width}x{height}"
            assert world_map.get_tile(x_coord, 0).type == "wall", msg_top
            assert world_map.get_tile(x_coord, height - 1).type == "wall", msg_bottom
        for y_coord in range(height):
            msg_left = f"Left edge at (0,{y_coord}) not wall for {width}x{height}"
            msg_right = f"Right edge at ({width - 1},{y_coord}) not wall for {width}x{height}"
            assert world_map.get_tile(0, y_coord).type == "wall", msg_left
            assert world_map.get_tile(width - 1, y_coord).type == "wall", msg_right


def test_single_floor_all_floor_tiles_are_accessible(single_floor_builder_factory):
    width, height = 10, 10
    builder = single_floor_builder_factory(width, height, seed=123)
    world_map, player_start_pos, _ = builder.build()

    inner_floor_tiles = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            tile = world_map.get_tile(x, y)
            if tile and tile.type == "floor":
                inner_floor_tiles.append((x, y))

    if not inner_floor_tiles:
        pytest.skip("No inner floor tiles found to test accessibility.")
        return

    queue = deque([player_start_pos])
    visited_floor_tiles = {player_start_pos}

    while queue:
        (current_x, current_y) = queue.popleft()
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_x, next_y = current_x + dx, current_y + dy
            if 1 <= next_x < width - 1 and 1 <= next_y < height - 1:
                tile = world_map.get_tile(next_x, next_y)
                if (
                    tile
                    and tile.type == "floor"
                    and (next_x, next_y) not in visited_floor_tiles
                ):
                    visited_floor_tiles.add((next_x, next_y))
                    queue.append((next_x, next_y))

    for floor_tile_pos in inner_floor_tiles:
        assert floor_tile_pos in visited_floor_tiles, (
            f"Inner floor tile at {floor_tile_pos} is not accessible from "
            f"player_start_pos {player_start_pos}"
        )


def test_single_floor_floor_portion_respected(single_floor_builder_factory):
    sizes = [(10, 10), (20, 15)]
    portions_to_test = [0.2, 0.5, 0.8]
    tolerance = 0.15

    for width, height in sizes:
        for portion in portions_to_test:
            builder = single_floor_builder_factory(
                width, height, seed=1, floor_portion=portion
            )
            world_map, _, _ = builder.build()

            inner_floor_tiles_count = 0
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    tile = world_map.get_tile(x, y)
                    if tile and tile.type == "floor":
                        inner_floor_tiles_count += 1

            total_inner_tiles = (width - 2) * (height - 2)
            if total_inner_tiles == 0:
                assert (
                    inner_floor_tiles_count == 0
                ), "No inner tiles but floor tiles found."
                continue

            actual_portion = inner_floor_tiles_count / total_inner_tiles
            min_expected_tiles = 0
            if total_inner_tiles >= 1:
                min_expected_tiles = 1
            if total_inner_tiles >= 2:
                min_expected_tiles = 2

            if portion < 0.01 and total_inner_tiles > 0:
                assert inner_floor_tiles_count >= min_expected_tiles, (
                    f"Expected at least {min_expected_tiles} floor tiles for "
                    f"portion {portion} on {width}x{height}, "
                    f"got {inner_floor_tiles_count}"
                )
            else:
                current_tolerance = tolerance
                if portion < 0.4:
                    current_tolerance = 0.22
                assert (
                    portion - current_tolerance
                    <= actual_portion
                    <= portion + current_tolerance
                ), (
                    f"Floor portion for {width}x{height} with target {portion} "
                    f"was {actual_portion:.2f} (tolerance {current_tolerance})"
                )
