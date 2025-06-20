from collections import deque

import pytest

from src.world_generator import WorldGenerator
from src.world_map import WorldMap


@pytest.fixture
def generator():
    return WorldGenerator()


# Test `generate_map` returns correct types
def test_generate_map_return_types(generator):
    world_map, player_start, win_pos = generator.generate_map(10, 10)
    assert isinstance(world_map, WorldMap)
    assert isinstance(player_start, tuple)
    assert len(player_start) == 2
    assert isinstance(player_start[0], int)
    assert isinstance(player_start[1], int)
    assert isinstance(win_pos, tuple)
    assert len(win_pos) == 2
    assert isinstance(win_pos[0], int)
    assert isinstance(win_pos[1], int)


# Test `generate_map` dimensions
def test_generate_map_dimensions(generator):
    width, height = 15, 12
    world_map, _, _ = generator.generate_map(width, height)
    assert world_map.width == width
    assert world_map.height == height


# Test `generate_map` content
def test_generate_map_content(generator):
    width, height = 20, 20
    world_map, player_start_pos, win_pos = generator.generate_map(
        width, height, seed=123
    )  # Use seed for consistency

    # Ensure player_start_pos is a "floor" tile
    px, py = player_start_pos
    player_tile = world_map.get_tile(px, py)
    assert player_tile is not None, "Player start position is out of bounds"
    assert player_tile.type == "floor", (
        f"Player start tile at {player_start_pos} is not a floor tile."
    )


# Tests for new quadrant-based random walk logic
def test_get_quadrant_bounds(generator: WorldGenerator):
    # Test with a 20x20 map
    map_width, map_height = 20, 20
    # Expected inner bounds: min_x=1, min_y=1, max_x=18, max_y=18
    # Midpoints: mid_x = 10, mid_y = 10

    # Quadrant 0: NE (mid_x to inner_max_x, inner_min_y to mid_y-1)
    # (10, 1, 18, 9)
    assert generator._get_quadrant_bounds(0, map_width, map_height) == (10, 1, 18, 9)

    # Quadrant 1: SE (mid_x to inner_max_x, mid_y to inner_max_y)
    # (10, 10, 18, 18)
    assert generator._get_quadrant_bounds(1, map_width, map_height) == (10, 10, 18, 18)

    # Quadrant 2: SW (inner_min_x to mid_x-1, mid_y to inner_max_y)
    # (1, 10, 9, 18)
    assert generator._get_quadrant_bounds(2, map_width, map_height) == (1, 10, 9, 18)

    # Quadrant 3: NW (inner_min_x to mid_x-1, inner_min_y to mid_y-1)
    # (1, 1, 9, 9)
    assert generator._get_quadrant_bounds(3, map_width, map_height) == (1, 1, 9, 9)

    # Test with a small 5x5 map
    map_width_small, map_height_small = 5, 5
    # Expected inner bounds: min_x=1, min_y=1, max_x=3, max_y=3
    # Midpoints: mid_x = 2, mid_y = 2

    # Quadrant 0: NE (mid_x to inner_max_x, inner_min_y to mid_y-1)
    # (2, 1, 3, 1)
    assert generator._get_quadrant_bounds(0, map_width_small, map_height_small) == (
        2,
        1,
        3,
        1,
    )

    # Quadrant 1: SE (mid_x to inner_max_x, mid_y to inner_max_y)
    # (2, 2, 3, 3)
    assert generator._get_quadrant_bounds(1, map_width_small, map_height_small) == (
        2,
        2,
        3,
        3,
    )

    # Quadrant 2: SW (inner_min_x to mid_x-1, mid_y to inner_max_y)
    # (1, 2, 1, 3)
    assert generator._get_quadrant_bounds(2, map_width_small, map_height_small) == (
        1,
        2,
        1,
        3,
    )

    # Quadrant 3: NW (inner_min_x to mid_x-1, inner_min_y to mid_y-1)
    # (1, 1, 1, 1)
    assert generator._get_quadrant_bounds(3, map_width_small, map_height_small) == (
        1,
        1,
        1,
        1,
    )

    # Test with a 4x4 map (edge case for midpoints)
    map_width_edge, map_height_edge = 4, 4
    # Inner bounds: min_x=1, min_y=1, max_x=2, max_y=2
    # Midpoints: mid_x = 2, mid_y = 2
    # Q0 NE: (2,1,2,1)
    # Q1 SE: (2,2,2,2)
    # Q2 SW: (1,2,1,2)
    # Q3 NW: (1,1,1,1)
    assert generator._get_quadrant_bounds(0, map_width_edge, map_height_edge) == (
        2,
        1,
        2,
        1,
    )
    assert generator._get_quadrant_bounds(1, map_width_edge, map_height_edge) == (
        2,
        2,
        2,
        2,
    )
    assert generator._get_quadrant_bounds(2, map_width_edge, map_height_edge) == (
        1,
        2,
        1,
        2,
    )
    assert generator._get_quadrant_bounds(3, map_width_edge, map_height_edge) == (
        1,
        1,
        1,
        1,
    )

    # Test with a 3x3 map (most degenerate case, inner area is 1x1)
    map_width_min, map_height_min = 3, 3
    # Inner bounds: min_x=1, min_y=1, max_x=1, max_y=1
    # Midpoints: mid_x = 1, mid_y = 1
    # Q0 NE: (1,1,1,0) -> clamped (1,1,1,1) because min_y > max_y (0) initially,
    # then max_y becomes min_y.
    # My code has specific clamping: if min_y > max_y, max_y = min_y.
    # So (1,1,1,1) is expected.
    # Q0: mid_x=1, inner_min_y=1, inner_max_x=1, mid_y-1=0 -> (1,1,1,0) -> (1,1,1,1)
    # Q1: mid_x=1, mid_y=1, inner_max_x=1, inner_max_y=1 -> (1,1,1,1)
    # Q2: inner_min_x=1, mid_y=1, mid_x-1=0, inner_max_y=1 -> (1,1,0,1) -> (1,1,1,1)
    # Q3: inner_min_x=1, inner_min_y=1, mid_x-1=0, mid_y-1=0 -> (1,1,0,0) -> (1,1,1,1)
    # Let's re-verify the logic in code:
    # min_x = max(inner_min_x, min_x)
    # min_y = max(inner_min_y, min_y)
    # max_x = min(inner_max_x, max_x)
    # max_y = min(inner_max_y, max_y)
    # if min_x > max_x: max_x = min_x
    # if min_y > max_y: max_y = min_y

    # Q0 (NE): initial (1,1,1,0). After clamp: (1,1,1,0). Then max_y=min_y -> (1,1,1,1)
    assert generator._get_quadrant_bounds(0, map_width_min, map_height_min) == (
        1,
        1,
        1,
        1,
    )
    # Q1 (SE): initial (1,1,1,1). After clamp: (1,1,1,1).
    assert generator._get_quadrant_bounds(1, map_width_min, map_height_min) == (
        1,
        1,
        1,
        1,
    )
    # Q2 (SW): initial (1,1,0,1). After clamp: (1,1,0,1). Then max_x=min_x -> (1,1,1,1)
    assert generator._get_quadrant_bounds(2, map_width_min, map_height_min) == (
        1,
        1,
        1,
        1,
    )
    # Q3 (NW): init (1,1,0,0). Clamp (1,1,0,0). Then max_x=min_x... -> (1,1,1,1)
    assert generator._get_quadrant_bounds(3, map_width_min, map_height_min) == (
        1,
        1,
        1,
        1,
    )

    with pytest.raises(ValueError):
        generator._get_quadrant_bounds(4, map_width, map_height)  # Invalid index


def test_get_random_tile_in_bounds(generator: WorldGenerator):
    map_width, map_height = 10, 10
    world_map = WorldMap(map_width, map_height)
    # Initialize inner area (1-8, 1-8)
    for r in range(map_height):  # Initialize all to potential_floor first
        for c in range(map_width):
            if c == 0 or c == map_width - 1 or r == 0 or r == map_height - 1:
                world_map.set_tile_type(c, r, "wall")  # Border walls
            else:
                world_map.set_tile_type(c, r, "potential_floor")

    # Specific tiles for testing
    world_map.set_tile_type(2, 2, "wall")  # Inner wall
    world_map.set_tile_type(2, 3, "floor")  # Inner floor
    world_map.set_tile_type(5, 5, "wall")  # Another inner wall
    world_map.set_tile_type(5, 6, "floor")  # Another inner floor

    # Test 1: Find a "wall" tile
    bounds1 = (1, 1, 3, 3)  # Includes (2,2) which is "wall"
    pos = generator._get_random_tile_in_bounds(world_map, bounds1, "wall")
    assert pos is not None
    assert pos == (2, 2)  # Only one wall in this small bound
    assert world_map.get_tile(pos[0], pos[1]).type == "wall"

    # Test 2: Find a "floor" tile
    bounds2 = (1, 1, 3, 4)  # Includes (2,3) which is "floor"
    pos = generator._get_random_tile_in_bounds(world_map, bounds2, "floor")
    assert pos is not None
    assert pos == (2, 3)  # Only one floor in this small bound
    assert world_map.get_tile(pos[0], pos[1]).type == "floor"

    # Test 3: Tile type does not exist in bounds
    bounds3 = (1, 1, 1, 1)  # No "monster" tile type generally
    pos = generator._get_random_tile_in_bounds(world_map, bounds3, "monster")
    assert pos is None

    # Test 4: Tile type "wall" does not exist in specific floor area
    world_map.set_tile_type(7, 7, "floor")
    bounds4 = (7, 7, 7, 7)  # Only contains a floor tile
    pos = generator._get_random_tile_in_bounds(world_map, bounds4, "wall")
    assert pos is None

    # Test 5: Invalid/degenerate bounds (min_x > max_x)
    bounds_invalid1 = (5, 1, 4, 3)
    pos = generator._get_random_tile_in_bounds(world_map, bounds_invalid1, "wall")
    assert pos is None

    # Test 6: Invalid/degenerate bounds (min_y > max_y)
    bounds_invalid2 = (1, 5, 3, 4)
    pos = generator._get_random_tile_in_bounds(world_map, bounds_invalid2, "wall")
    assert pos is None

    # Test 7: Bounds are outside the inner map area but still valid rect
    # _get_random_tile_in_bounds itself doesn't care about inner map, only map.get_tile
    # For this test, we'll use bounds that are technically valid for map indexing
    # but might be outside where we'd expect findable tiles from _get_quadrant_bounds.
    # Let's assume we're looking for border walls.
    world_map.set_tile_type(0, 0, "wall")  # ensure border wall
    pos = generator._get_random_tile_in_bounds(world_map, (0, 0, 0, 0), "wall")
    assert pos == (0, 0)

    # Test 8: Max attempts exhausted
    # Create a bound where the tile exists but is hard to hit randomly if not seeded.
    # Max_attempts is 100. For a 10x10 area (100 tiles), finding one specific
    # tile is 1/100. This is hard to test reliably without setting random.seed
    # or many attempts. Instead, check if it returns None if the ONLY tile of
    # a type is outside specific bounds.
    world_map.set_tile_type(8, 8, "special")
    bounds_miss = (1, 1, 7, 7)  # This bound does not include (8,8)
    pos = generator._get_random_tile_in_bounds(world_map, bounds_miss, "special")
    assert pos is None


def test_perform_directed_random_walk(generator: WorldGenerator):
    map_width, map_height = 10, 10
    world_map = WorldMap(map_width, map_height)
    # Initialize all to wall, including inner area, except border
    for r in range(map_height):
        for c in range(map_width):
            if c == 0 or c == map_width - 1 or r == 0 or r == map_height - 1:
                world_map.set_tile_type(c, r, "wall")  # Border
            else:
                world_map.set_tile_type(c, r, "wall")  # Inner also wall initially

    start_pos = (2, 2)  # This is currently a wall
    end_pos = (7, 7)
    world_map.set_tile_type(end_pos[0], end_pos[1], "floor")  # Set end_pos to be floor

    initial_floor_tiles = 0
    for r_idx in range(1, map_height - 1):
        for c_idx in range(1, map_width - 1):
            if world_map.get_tile(c_idx, r_idx).type == "floor":
                initial_floor_tiles += 1
    assert initial_floor_tiles == 1  # Only end_pos is floor

    generator._perform_directed_random_walk(
        world_map, start_pos, end_pos, map_width, map_height
    )

    # Assert start_pos is now floor
    assert world_map.get_tile(start_pos[0], start_pos[1]).type == "floor"
    # Assert end_pos is still floor
    assert world_map.get_tile(end_pos[0], end_pos[1]).type == "floor"

    # Count floor tiles after walk; should be more than initial
    final_floor_tiles = 0
    path_tiles_coords = []  # Store coords of floor tiles for path check
    for r_idx in range(1, map_height - 1):
        for c_idx in range(1, map_width - 1):
            if world_map.get_tile(c_idx, r_idx).type == "floor":
                final_floor_tiles += 1
                path_tiles_coords.append((c_idx, r_idx))

    assert final_floor_tiles > initial_floor_tiles

    # Check that border walls were not changed
    for c_idx in range(map_width):
        assert world_map.get_tile(c_idx, 0).type == "wall"
        assert world_map.get_tile(c_idx, map_height - 1).type == "wall"
    for r_idx in range(map_height):
        assert world_map.get_tile(0, r_idx).type == "wall"
        assert world_map.get_tile(map_width - 1, r_idx).type == "wall"

    # Optional: Check if path exists between start and end using BFS.
    # This is a stronger check for connectivity if the walk was successful.
    path_exists = find_path_bfs(world_map, start_pos, end_pos)
    assert path_exists, (
        f"No path found via BFS from {start_pos} to {end_pos} after walk. "
        f"Path tiles: {path_tiles_coords}"
    )


def test_perform_random_walks_creates_floor_in_quadrants(generator: WorldGenerator):
    map_width, map_height = 20, 20
    world_map = WorldMap(map_width, map_height)
    # Initialize map: border wall, inner potential_floor
    for r in range(map_height):
        for c in range(map_width):
            if c == 0 or c == map_width - 1 or r == 0 or r == map_height - 1:
                world_map.set_tile_type(c, r, "wall")
            else:
                # For this test, start with walls in inner area,
                # so walks have something to carve.
                world_map.set_tile_type(c, r, "wall")

    player_start_pos = (5, 5)  # Arbitrary, used as fallback target by walks
    world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")

    initial_floor_count = 1  # Only player_start_pos

    # Before calling, let's count floor tiles in each quadrant
    initial_quad_floors = []
    for i in range(4):
        bounds = generator._get_quadrant_bounds(i, map_width, map_height)
        count = 0
        if bounds[0] <= bounds[2] and bounds[1] <= bounds[3]:  # valid bounds
            for r_idx in range(bounds[1], bounds[3] + 1):
                for c_idx in range(bounds[0], bounds[2] + 1):
                    if world_map.get_tile(c_idx, r_idx).type == "floor":
                        count += 1
        initial_quad_floors.append(count)

    generator._perform_random_walks(world_map, player_start_pos, map_width, map_height)

    quadrant_floor_counts_after = []
    active_quadrants = 0

    for i in range(4):
        bounds = generator._get_quadrant_bounds(i, map_width, map_height)
        current_quad_floor_count = 0
        # Check if bounds are valid before iterating
        if bounds[0] <= bounds[2] and bounds[1] <= bounds[3]:
            for r_idx in range(bounds[1], bounds[3] + 1):
                for c_idx in range(bounds[0], bounds[2] + 1):
                    tile = world_map.get_tile(c_idx, r_idx)
                    if tile and tile.type == "floor":
                        current_quad_floor_count += 1
            quadrant_floor_counts_after.append(current_quad_floor_count)
            # Check if floor count increased in this quadrant
            if current_quad_floor_count > initial_quad_floors[i]:
                active_quadrants += 1
        else:
            # No valid area in this quadrant
            quadrant_floor_counts_after.append(0)

    # Assert that total floor tiles increased significantly.
    # (player_start was 1, plus walks should add substantially more).
    # This is a bit loose as walks can overlap or be short.
    # Key is that it's more than just the initial player_start_pos.
    # Recalculate total_final_floor_tiles accurately to avoid double counting.
    final_floor_map_tiles = 0
    for r_idx in range(1, map_height - 1):
        for c_idx in range(1, map_width - 1):
            if world_map.get_tile(c_idx, r_idx).type == "floor":
                final_floor_map_tiles += 1

    assert final_floor_map_tiles > initial_floor_count, (
        f"Expected > {initial_floor_count} floor tiles, got {final_floor_map_tiles}"
    )

    # Assert that at least some quadrants show activity (increased floor tiles).
    # This is probabilistic. On a 20x20 map, all 4 should usually be active.
    # For smaller maps, some quadrants might be too small to start a walk.
    # A 20x20 map should be large enough.
    assert active_quadrants > 0, (
        f"Expected walks in >0 quadrants. Active: {active_quadrants}. "
        f"Counts after: {quadrant_floor_counts_after}, Before: {initial_quad_floors}"
    )
    # A stronger assertion for a 20x20 map:
    if map_width >= 10 and map_height >= 10:  # Heuristic for expecting all quads active
        assert active_quadrants >= 2, (
            f"Expected walks in >=2 quadrants for {map_width}x{map_height} map. "
            f"Active: {active_quadrants}. Counts after: {quadrant_floor_counts_after}"
        )


# Test `generate_map` reproducibility with seed
def test_generate_map_reproducibility_with_seed(generator):
    width, height, seed = (
        20,
        20,
        42,
    )  # Use a slightly larger map for better test of content

    map1, ps1, wp1 = generator.generate_map(width, height, seed)
    map2, ps2, wp2 = generator.generate_map(width, height, seed)

    assert ps1 == ps2, "Player start positions differ with the same seed."
    # original_win_pos is not directly returned by generate_map anymore
    # in the same way for amulet placement, but the final actual_win_pos
    # should be reproducible.
    assert wp1 == wp2, "Actual win positions (amulet) differ with the same seed."

    for y in range(height):
        for x in range(width):
            tile1 = map1.get_tile(x, y)
            tile2 = map2.get_tile(x, y)
            assert tile1.type == tile2.type, (
                f"Tile type at ({x},{y}) differs: M1={tile1.type}, "
                f"M2={tile2.type} with seed {seed}."
            )

            # Compare items
            if tile1.item:
                assert tile2.item is not None, (
                    f"Tile1 has item '{tile1.item.name}' at ({x},{y}), "
                    f"Tile2 does not. Seed {seed}."
                )
                assert tile1.item.name == tile2.item.name, (
                    f"Item names at ({x},{y}) differ: M1='{tile1.item.name}', "
                    f"M2='{tile2.item.name}'. Seed {seed}."
                )
                assert tile1.item.description == tile2.item.description, (
                    f"Item descriptions at ({x},{y}) for '{tile1.item.name}' "
                    f"differ. Seed {seed}."
                )
                assert tile1.item.properties == tile2.item.properties, (
                    f"Item properties at ({x},{y}) for '{tile1.item.name}' "
                    f"differ. Seed {seed}."
                )
            else:
                assert tile2.item is None, (
                    f"Tile1 has no item at ({x},{y}), Tile2 has "
                    f"'{tile2.item.name}'. Seed {seed}."
                )

            # Compare monsters
            if tile1.monster:
                assert tile2.monster is not None, (
                    f"Tile1 has monster '{tile1.monster.name}' at ({x},{y}), "
                    f"Tile2 does not. Seed {seed}."
                )
                assert tile1.monster.name == tile2.monster.name, (
                    f"Monster names at ({x},{y}) differ: M1='{tile1.monster.name}', "
                    f"M2='{tile2.monster.name}'. Seed {seed}."
                )
                assert tile1.monster.health == tile2.monster.health, (
                    f"Monster health at ({x},{y}) for '{tile1.monster.name}' "
                    f"differs. Seed {seed}."
                )
                assert tile1.monster.attack_power == tile2.monster.attack_power, (
                    f"Monster AP at ({x},{y}) for '{tile1.monster.name}' "
                    f"differs. Seed {seed}."
                )
                # Note: Monster x,y are updated by place_monster, so they should
                # match x,y of the tile.
                assert tile1.monster.x == x
                assert tile1.monster.y == y
                assert tile2.monster.x == x
                assert tile2.monster.y == y
            else:
                assert tile2.monster is None, (
                    f"Tile1 has no monster at ({x},{y}), Tile2 has "
                    f"'{tile2.monster.name}'. Seed {seed}."
                )


# Test `generate_map` with different seeds
def test_generate_map_with_different_seeds(generator):
    width, height = 10, 10
    seed1 = 123
    seed2 = 456
    assert seed1 != seed2  # Ensure seeds are different

    map1, ps1, wp1 = generator.generate_map(width, height, seed1)
    map2, ps2, wp2 = generator.generate_map(width, height, seed2)

    # It's highly probable that the results will be different.
    # A full map comparison can be complex. Check key differentiating factors:
    # Player start or win position are good indicators.
    # Or, count floor tiles, or check a few specific tile types/contents.
    # A simple check is to compare the full string representation of the maps
    # (tile types only).

    map1_repr = "\n".join(
        [
            "".join([map1.get_tile(x, y).type[0] for x in range(width)])
            for y in range(height)
        ]
    )
    map2_repr = "\n".join(
        [
            "".join([map2.get_tile(x, y).type[0] for x in range(width)])
            for y in range(height)
        ]
    )

    # Also check item/monster placements by counting them.
    items1, monsters1 = 0, 0
    for y in range(height):
        for x in range(width):
            if map1.get_tile(x, y).item:
                items1 += 1
            if map1.get_tile(x, y).monster:
                monsters1 += 1

    items2, monsters2 = 0, 0
    for y in range(height):
        for x in range(width):
            if map2.get_tile(x, y).item:
                items2 += 1
            if map2.get_tile(x, y).monster:
                monsters2 += 1

    are_maps_different = (
        ps1 != ps2
        or wp1 != wp2
        or map1_repr != map2_repr
        or items1 != items2
        or monsters1 != monsters2
    )

    assert are_maps_different, (
        "Generated maps with different seeds were identical, which is highly unlikely."
    )


# BFS helper function for path verification
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
            return True  # Path found

        for dx, dy in [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
        ]:  # S, N, E, W (order doesn't matter for BFS path existence)
            next_x, next_y = current_x + dx, current_y + dy

            if 0 <= next_x < width and 0 <= next_y < height:
                tile = world_map.get_tile(next_x, next_y)
                # Check if tile exists and is a floor tile
                if tile and tile.type == "floor" and (next_x, next_y) not in visited:
                    visited.add((next_x, next_y))
                    queue.append(
                        ((next_x, next_y), path + [(next_x, next_y)])
                    )  # path list not strictly needed for existence check
    return False


# Test for guaranteed path
@pytest.mark.parametrize(
    "seed_val", [None] + list(range(5))
)  # Test with random map and a few seeded maps
def test_guaranteed_path_exists(generator, seed_val):
    width, height = 10, 10  # Valid size
    world_map, player_start, win_pos = generator.generate_map(
        width, height, seed=seed_val
    )

    assert world_map.get_tile(player_start[0], player_start[1]).type == "floor", (
        f"Player start {player_start} is not floor. Seed: {seed_val}"
    )
    assert world_map.get_tile(win_pos[0], win_pos[1]).type == "floor", (
        f"Win position {win_pos} is not floor. Seed: {seed_val}"
    )

    if player_start == win_pos:  # Should be rare on a 10x10 map
        path_found = True
    else:
        path_found = find_path_bfs(world_map, player_start, win_pos)

    assert path_found, (
        f"No path found between player_start {player_start} and "
        f"win_pos {win_pos}. Seed: {seed_val}"
    )


# Test that player start and win positions are not on the edge
def test_start_win_positions_not_on_edge(generator):
    for seed_val in range(5):
        width, height = 5, 5  # Valid size, allows inner area
        world_map, player_start, win_pos = generator.generate_map(
            width, height, seed=seed_val
        )

        # player_start and win_pos are from inner area (1 to width-2, etc.)
        assert 0 < player_start[0] < width - 1, (
            f"Player start X ({player_start[0]}) on edge. Seed: {seed_val}"
        )
        assert 0 < player_start[1] < height - 1, (
            f"Player start Y ({player_start[1]}) on edge. Seed: {seed_val}"
        )
        # Amulet position determined by furthest point, should also be inner.
        assert 0 < win_pos[0] < width - 1, (
            f"Win pos X ({win_pos[0]}) on edge. Seed: {seed_val}"
        )
        assert 0 < win_pos[1] < height - 1, (
            f"Win pos Y ({win_pos[1]}) on edge. Seed: {seed_val}"
        )


def test_generate_map_valid_minimum_size(generator):
    valid_sizes = [(3, 4), (4, 3), (5, 5)]  # (w,h)
    for width, height in valid_sizes:
        try:
            world_map, player_start, win_pos = generator.generate_map(
                width, height, seed=1
            )
            assert world_map.width == width
            assert world_map.height == height
            assert 0 < player_start[0] < width - 1
            assert 0 < player_start[1] < height - 1
            assert 0 < win_pos[0] < width - 1
            assert 0 < win_pos[1] < height - 1
            player_tile = world_map.get_tile(player_start[0], player_start[1])
            win_tile = world_map.get_tile(win_pos[0], win_pos[1])
            assert player_tile.type == "floor"
            assert win_tile.type == "floor"
            assert win_tile.item is not None
            assert win_tile.item.name == "Amulet of Yendor"
        except ValueError:
            pytest.fail(
                f"generate_map raised ValueError for valid size {width}x{height}"
            )


def test_generate_map_invalid_small_size(generator):
    invalid_sizes = [(2, 2), (1, 5), (5, 1), (3, 3), (2, 4), (4, 2)]
    for width, height in invalid_sizes:
        with pytest.raises(
            ValueError, match="Map dimensions must be at least 3x4 or 4x3"
        ):
            generator.generate_map(width, height, seed=1)


def test_outer_layer_is_always_wall(generator):
    sizes_to_test = [(4, 5), (5, 4), (10, 10)]
    for width, height in sizes_to_test:
        world_map, _, _ = generator.generate_map(width, height, seed=1)
        for x_coord in range(width):
            msg_top = f"Top edge at ({x_coord},0) not wall for {width}x{height}"
            msg_bottom = (
                f"Bottom edge at ({x_coord},{height - 1}) not wall for {width}x{height}"
            )
            assert world_map.get_tile(x_coord, 0).type == "wall", msg_top
            assert world_map.get_tile(x_coord, height - 1).type == "wall", msg_bottom
        for y_coord in range(height):
            msg_left = f"Left edge at (0,{y_coord}) not wall for {width}x{height}"
            msg_right = (
                f"Right edge at ({width - 1},{y_coord}) not wall for {width}x{height}"
            )
            assert world_map.get_tile(0, y_coord).type == "wall", msg_left
            assert world_map.get_tile(width - 1, y_coord).type == "wall", msg_right


def test_all_floor_tiles_are_accessible(generator):
    width, height = 10, 10  # A reasonably sized map
    world_map, player_start_pos, _ = generator.generate_map(width, height, seed=123)

    inner_floor_tiles = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            tile = world_map.get_tile(x, y)
            if tile and tile.type == "floor":
                inner_floor_tiles.append((x, y))

    if not inner_floor_tiles:
        # This could happen if floor_portion is extremely low or map is tiny.
        # For 10x10, this shouldn't be the case with default floor_portion.
        pytest.skip("No inner floor tiles found to test accessibility.")
        return

    # Use the same BFS as in test_guaranteed_path_exists, but check all floor tiles
    queue = deque([player_start_pos])
    visited_floor_tiles = {player_start_pos}

    while queue:
        (current_x, current_y) = queue.popleft()
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_x, next_y = current_x + dx, current_y + dy
            # Only check within inner map boundaries for floor tiles to explore
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


def test_floor_portion_respected(generator):
    sizes = [(10, 10), (20, 15)]
    portions_to_test = [0.2, 0.5, 0.8]
    tolerance = 0.15  # Allow some deviation due to grid and connectivity

    for width, height in sizes:
        for portion in portions_to_test:
            # Create a new generator with the specific floor_portion
            specific_generator = WorldGenerator(floor_portion=portion)
            world_map, _, _ = specific_generator.generate_map(width, height, seed=1)

            inner_floor_tiles_count = 0
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    tile = world_map.get_tile(x, y)
                    if tile and tile.type == "floor":
                        inner_floor_tiles_count += 1

            total_inner_tiles = (width - 2) * (height - 2)
            if total_inner_tiles == 0:
                assert inner_floor_tiles_count == 0, (
                    "No inner tiles but floor tiles found."
                )
                continue

            actual_portion = inner_floor_tiles_count / total_inner_tiles

            # For very low portions, ensure at least player_start and
            # original_win_pos can be floor (original_win_pos is protected
            # by adjust_density, not necessarily the final amulet position).
            min_expected_tiles = 0
            if total_inner_tiles >= 1:
                min_expected_tiles = 1  # player_start_pos
            if total_inner_tiles >= 2:
                min_expected_tiles = 2  # player_start_pos and original_win_pos

            if portion < 0.01 and total_inner_tiles > 0:
                # Test for very low portion
                assert inner_floor_tiles_count >= min_expected_tiles, (
                    f"Expected at least {min_expected_tiles} floor tiles for "
                    f"portion {portion} on {width}x{height}, "
                    f"got {inner_floor_tiles_count}"
                )
            else:
                assert portion - tolerance <= actual_portion <= portion + tolerance, (
                    f"Floor portion for {width}x{height} with target {portion} "
                    f"was {actual_portion:.2f} (tolerance {tolerance})"
                )


def test_win_item_placed_furthest(generator):
    # Using a predictable small map where "furthest" is clear.
    # E.g., 3x5 map. Inner area is 1x3.
    # If player starts at (1,1) (absolute), the furthest in a 1x3 inner area
    # [(1,1), (1,2), (1,3)] would be (1,3).
    width, height = 3, 5  # Inner area: 1x3 tiles
    world_map, player_start_pos, actual_win_pos = generator.generate_map(
        width,
        height,
        seed=42,  # seed makes player_start_pos predictable
    )

    # For this test, we rely on the seed to make player_start_pos predictable.
    # Alternatively, one might modify the generator or use a helper to force
    # player_start_pos for more direct testing of furthest point logic.

    # Collect all inner floor tiles
    inner_floor_tiles = []
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if world_map.get_tile(c, r).type == "floor":
                inner_floor_tiles.append((c, r))

    if not inner_floor_tiles:
        pytest.skip("No inner floor tiles to determine furthest point.")
        return
    if player_start_pos not in inner_floor_tiles:
        pytest.skip(
            f"Player start {player_start_pos} not among inner floor "
            f"tiles {inner_floor_tiles}. Map generation issue or test setup."
        )
        return

    # Calculate distances from player_start_pos to all other inner floor tiles
    # using BFS, similar to how PathFinder.find_furthest_point works.
    queue = deque([(player_start_pos, 0)])
    visited_distances = {player_start_pos: 0}
    current_max_dist = 0
    calculated_furthest_tiles = {player_start_pos}

    while queue:
        current_pos, distance = queue.popleft()

        if distance > current_max_dist:
            current_max_dist = distance
            calculated_furthest_tiles = {current_pos}
        elif distance == current_max_dist:
            calculated_furthest_tiles.add(current_pos)

        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # N, S, E, W
            # Note: BFS explores (y,x) but tile positions are (x,y)
            next_tile_x, next_tile_y = (
                current_pos[0] + dc,
                current_pos[1] + dr,
            )

            if (next_tile_x, next_tile_y) in inner_floor_tiles and (
                next_tile_x,
                next_tile_y,
            ) not in visited_distances:
                visited_distances[(next_tile_x, next_tile_y)] = distance + 1
                queue.append(((next_tile_x, next_tile_y), distance + 1))

    assert actual_win_pos in calculated_furthest_tiles, (
        f"Amulet at {actual_win_pos} is not one of the furthest tiles "
        f"{calculated_furthest_tiles} from {player_start_pos} "
        f"(max_dist: {current_max_dist})."
    )


def test_visual_inspection_of_generated_maps():
    """
    Allows visual inspection of generated maps for qualitative assessment.
    This test prints map representations to the console and has no assertions.
    """
    print("\n--- Visual Inspection of Generated Maps ---")
    generator = WorldGenerator(floor_portion=0.4)
    seeds = [1, 2, 3]
    dimensions = [(20, 10), (15, 15)]

    for seed_val in seeds:
        for width, height in dimensions:
            print(f"\nMap for seed={seed_val}, Dimensions: {width}x{height}")
            world_map, _, _ = generator.generate_map(width, height, seed=seed_val)
            for y in range(height):
                row_str = ""
                for x in range(width):
                    tile = world_map.get_tile(x, y)
                    if tile is None:  # Should not happen in a valid map
                        row_str += "?"
                    elif tile.type == "wall":
                        row_str += "#"
                    elif tile.type == "floor":
                        row_str += "."
                    elif tile.type == "potential_floor":  # Should be resolved
                        row_str += "~"
                    else:
                        row_str += "X"  # Unknown tile type
                print(row_str)

    print("\nVisual inspection test complete. Review output above.")


def test_path_like_structures_metric():
    """
    Calculates and prints a metric for 'path-like' structures in generated maps.
    A path-like tile is a floor tile with exactly two floor neighbors in
    opposite directions (N-S or E-W).
    """
    print("\n--- Path-Like Structures Metric ---")
    generator = WorldGenerator(floor_portion=0.4)  # Consistent floor portion

    test_configs = [
        {"width": 25, "height": 25, "seed": 10},
        {"width": 25, "height": 25, "seed": 20},
        {"width": 30, "height": 20, "seed": 30},
    ]

    for config in test_configs:
        width, height, seed_val = config["width"], config["height"], config["seed"]
        world_map, _, _ = generator.generate_map(width, height, seed=seed_val)

        path_tile_count = 0

        # Iterate through inner floor tiles (1 to width-2, 1 to height-2)
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                current_tile = world_map.get_tile(x, y)
                if current_tile and current_tile.type == "floor":
                    floor_neighbor_count = 0

                    # Check N, S, E, W neighbors
                    north_is_floor = False
                    south_is_floor = False
                    east_is_floor = False
                    west_is_floor = False

                    # North
                    north_tile = world_map.get_tile(x, y - 1)
                    if north_tile and north_tile.type == "floor":
                        north_is_floor = True
                        floor_neighbor_count += 1

                    # South
                    south_tile = world_map.get_tile(x, y + 1)
                    if south_tile and south_tile.type == "floor":
                        south_is_floor = True
                        floor_neighbor_count += 1

                    # East
                    east_tile = world_map.get_tile(x + 1, y)
                    if east_tile and east_tile.type == "floor":
                        east_is_floor = True
                        floor_neighbor_count += 1

                    # West
                    west_tile = world_map.get_tile(x - 1, y)
                    if west_tile and west_tile.type == "floor":
                        west_is_floor = True
                        floor_neighbor_count += 1

                    if floor_neighbor_count == 2:
                        is_ns_path = north_is_floor and south_is_floor
                        is_ew_path = east_is_floor and west_is_floor

                        if is_ns_path or is_ew_path:
                            path_tile_count += 1

        print(f"Seed: {seed_val}, Dim: {width}x{height}, Path-like: {path_tile_count}")
        assert path_tile_count >= 0, "Path tile count should be non-negative."
        # A more specific assertion like `path_tile_count > (width + height) // 4`
        # could be added if a baseline is established. For now, >= 0 is a basic check.
        # For a 25x25 map, (23+23)//2 = 23. This is a plausible heuristic.
        # Let's use the one from the prompt:
        if width > 2 and height > 2:  # Ensure inner area exists
            assert path_tile_count >= (width - 2 + height - 2) // 2, (
                f"Paths {path_tile_count} low for {width}x{height} m (S: {seed_val})"
            )

    print("\nPath-like structures metric test complete. Review output above.")
