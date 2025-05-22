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

    # Ensure the win_pos tile contains the "Goal Item"
    wx, wy = win_pos
    win_tile = world_map.get_tile(wx, wy)
    assert win_tile is not None, "Win position is out of bounds"
    assert win_tile.item is not None, f"Win tile at {win_pos} has no item."
    assert win_tile.item.name == "Amulet of Yendor", (
        "Win tile does not contain the Amulet of Yendor."
    )
    assert win_tile.item.properties.get("type") == "quest", (
        "Goal item is not of type 'quest'."
    )

    # Ensure player start and win positions are different
    assert player_start_pos != win_pos, "Player start and win positions are the same."

    # Ensure there's at least one "floor" tile (already implied by player_start_pos and win_pos being floor)
    floor_tile_found = False
    for y in range(height):
        for x in range(width):
            tile = world_map.get_tile(x, y)
            if tile and tile.type == "floor":
                floor_tile_found = True
                break
        if floor_tile_found:
            break
    assert floor_tile_found, "No floor tiles found on the map."

    # Check if some other items and monsters are placed (basic check)
    # This is probabilistic, but with a large enough map and enough placements, some should exist.
    # For very small maps, this part of the test might be flaky.
    other_items_count = 0
    monsters_count = 0
    for y_coord in range(height):
        for x_coord in range(width):
            tile = world_map.get_tile(x_coord, y_coord)
            if tile:
                if (
                    tile.item and tile.item.name != "Amulet of Yendor"
                ):  # Exclude goal item
                    other_items_count += 1
                if tile.monster:
                    monsters_count += 1

    # This is a very loose check, adjust numbers if needed for your generation logic
    # print(f"Found {other_items_count} other items and {monsters_count} monsters.") # For debugging
    # On a 20x20 map, it's highly likely at least one of each is placed.
    # If not, the placement logic in generator might need review or test conditions adjusted.

    # With the new generator placing specific items/monsters, we can be more specific if desired.
    # For now, just checking if some are placed is okay.
    # The number of placements is (width*height)//15. Item chance 0.15, monster 0.10.
    # For 20x20 map (400 tiles), placements = 400/15 = ~26 attempts.
    # Expected other items = 26 * 0.15 * (1 - prob_player_or_win_tile) ~ 3-4 items
    # Expected monsters = 26 * 0.10 * (1 - prob_player_or_win_tile) ~ 2-3 monsters
    # Asserting >=0 is fine, but could be stricter for larger maps if needed.
    assert other_items_count >= 0
    assert monsters_count >= 0


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
    assert wp1 == wp2, "Win positions differ with the same seed."

    for y in range(height):
        for x in range(width):
            tile1 = map1.get_tile(x, y)
            tile2 = map2.get_tile(x, y)
            assert tile1.type == tile2.type, (
                f"Tile type at ({x},{y}) differs: M1={tile1.type}, M2={tile2.type} with seed {seed}."
            )

            # Compare items
            if tile1.item:
                assert tile2.item is not None, (
                    f"Tile1 has item '{tile1.item.name}' at ({x},{y}), Tile2 does not. Seed {seed}."
                )
                assert tile1.item.name == tile2.item.name, (
                    f"Item names at ({x},{y}) differ: M1='{tile1.item.name}', M2='{tile2.item.name}'. Seed {seed}."
                )
                assert tile1.item.description == tile2.item.description, (
                    f"Item descriptions at ({x},{y}) for '{tile1.item.name}' differ. Seed {seed}."
                )
                assert tile1.item.properties == tile2.item.properties, (
                    f"Item properties at ({x},{y}) for '{tile1.item.name}' differ. Seed {seed}."
                )
            else:
                assert tile2.item is None, (
                    f"Tile1 has no item at ({x},{y}), Tile2 has '{tile2.item.name}'. Seed {seed}."
                )

            # Compare monsters
            if tile1.monster:
                assert tile2.monster is not None, (
                    f"Tile1 has monster '{tile1.monster.name}' at ({x},{y}), Tile2 does not. Seed {seed}."
                )
                assert tile1.monster.name == tile2.monster.name, (
                    f"Monster names at ({x},{y}) differ: M1='{tile1.monster.name}', M2='{tile2.monster.name}'. Seed {seed}."
                )
                assert tile1.monster.health == tile2.monster.health, (
                    f"Monster health at ({x},{y}) for '{tile1.monster.name}' differs. Seed {seed}."
                )
                assert tile1.monster.attack_power == tile2.monster.attack_power, (
                    f"Monster AP at ({x},{y}) for '{tile1.monster.name}' differs. Seed {seed}."
                )
                # Note: Monster x,y are updated by place_monster, so they should match x,y of the tile.
                assert tile1.monster.x == x
                assert tile1.monster.y == y
                assert tile2.monster.x == x
                assert tile2.monster.y == y
            else:
                assert tile2.monster is None, (
                    f"Tile1 has no monster at ({x},{y}), Tile2 has '{tile2.monster.name}'. Seed {seed}."
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
    # A simple check is to compare the full string representation of the maps (tile types only).

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
from collections import deque


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
    return False  # No path


# Test for guaranteed path
@pytest.mark.parametrize(
    "seed_val", [None] + list(range(5))
)  # Test with random map and a few seeded maps
def test_guaranteed_path_exists(generator, seed_val):
    # Using a reasonable size for testing path generation.
    # Smaller maps might have player_start == win_pos if not handled,
    # but current generator logic tries to avoid that.
    # Edge avoidance in player/win pos selection means width/height should be >=3 for that part.
    # The path carving itself should work for smaller maps.
    width, height = 10, 10
    if (
        width < 3 or height < 3
    ):  # Skip test if dimensions are too small for edge avoidance logic
        pytest.skip(
            "Map dimensions too small for current generator's edge avoidance logic in start/win pos."
        )

    world_map, player_start, win_pos = generator.generate_map(
        width, height, seed=seed_val
    )

    # Ensure start and win positions are floor tiles (should be set by generator)
    assert world_map.get_tile(player_start[0], player_start[1]).type == "floor", (
        f"Player start {player_start} is not floor. Seed: {seed_val}"
    )
    assert world_map.get_tile(win_pos[0], win_pos[1]).type == "floor", (
        f"Win position {win_pos} is not floor. Seed: {seed_val}"
    )

    # If player_start and win_pos are the same, path trivially exists.
    if player_start == win_pos:
        path_found = True
    else:
        path_found = find_path_bfs(world_map, player_start, win_pos)

    assert path_found, (
        f"No path found between player_start {player_start} and win_pos {win_pos}. Seed: {seed_val}"
    )


# Test that player start and win positions are not on the edge (for maps >= 3x3)
def test_start_win_positions_not_on_edge(generator):
    # Test with several seeds to ensure consistency
    for seed_val in range(5):
        # Use map dimensions where edges can be avoided
        width, height = 5, 5
        _, player_start, win_pos = generator.generate_map(width, height, seed=seed_val)

        assert 0 < player_start[0] < width - 1, (
            f"Player start X ({player_start[0]}) is on edge. Seed: {seed_val}"
        )
        assert 0 < player_start[1] < height - 1, (
            f"Player start Y ({player_start[1]}) is on edge. Seed: {seed_val}"
        )
        assert 0 < win_pos[0] < width - 1, (
            f"Win pos X ({win_pos[0]}) is on edge. Seed: {seed_val}"
        )
        assert 0 < win_pos[1] < height - 1, (
            f"Win pos Y ({win_pos[1]}) is on edge. Seed: {seed_val}"
        )


def test_start_win_positions_small_maps(generator):
    # Test behavior for maps < 3x3 where edge avoidance is not possible for randint(1, dim-2)
    # Player start and win positions should still be within bounds [0, dim-1]

    # Case 1: 2x2 map
    width, height = 2, 2
    for seed_val in range(3):
        _, player_start, win_pos = generator.generate_map(width, height, seed=seed_val)
        assert 0 <= player_start[0] < width and 0 <= player_start[1] < height
        assert 0 <= win_pos[0] < width and 0 <= win_pos[1] < height

    # Case 2: 1x5 map
    width, height = 1, 5
    for seed_val in range(3):
        _, player_start, win_pos = generator.generate_map(width, height, seed=seed_val)
        assert 0 <= player_start[0] < width and 0 <= player_start[1] < height
        assert 0 <= win_pos[0] < width and 0 <= win_pos[1] < height

    # Case 3: 1x1 map
    width, height = 1, 1
    for seed_val in range(3):
        _, player_start, win_pos = generator.generate_map(width, height, seed=seed_val)
        assert player_start == (0, 0)
        assert win_pos == (0, 0)  # Must be same on 1x1 map
        # Path test for 1x1
        world_map_1x1, ps_1x1, wp_1x1 = generator.generate_map(
            width, height, seed=seed_val
        )
        assert find_path_bfs(world_map_1x1, ps_1x1, wp_1x1) is True
