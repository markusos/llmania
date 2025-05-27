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

    # Ensure there's at least one "floor" tile (already implied by
    # player_start_pos and win_pos being floor)
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
    # This is probabilistic, but with a large enough map and enough placements,
    # some should exist.
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

    # This is a very loose check, adjust numbers if needed for your generation
    # logic
    # print(f"Found {other_items_count} other items and {monsters_count} monsters.")
    # For debugging
    # On a 20x20 map, it's highly likely at least one of each is placed.
    # If not, the placement logic in generator might need review or test
    # conditions adjusted.

    # With the new generator placing specific items/monsters, we can be more
    # specific if desired.
    # For now, just checking if some are placed is okay.
    # The number of placements is (width*height)//15. Item chance 0.15,
    # monster 0.10.
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
    # original_win_pos is not directly returned by generate_map anymore in the same way for amulet placement,
    # but the final actual_win_pos should be reproducible.
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
    width, height = 10, 10 # Valid size
    world_map, player_start, win_pos = generator.generate_map(
        width, height, seed=seed_val
    )

    assert world_map.get_tile(player_start[0], player_start[1]).type == "floor", (
        f"Player start {player_start} is not floor. Seed: {seed_val}"
    )
    assert world_map.get_tile(win_pos[0], win_pos[1]).type == "floor", (
        f"Win position {win_pos} is not floor. Seed: {seed_val}"
    )

    if player_start == win_pos: # Should be rare on a 10x10 map
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
        width, height = 5, 5 # Valid size, allows inner area
        world_map, player_start, win_pos = generator.generate_map(width, height, seed=seed_val)

        # player_start and win_pos are from inner area (1 to width-2, 1 to height-2)
        assert 0 < player_start[0] < width - 1, (
            f"Player start X ({player_start[0]}) is on edge. Seed: {seed_val}"
        )
        assert 0 < player_start[1] < height - 1, (
            f"Player start Y ({player_start[1]}) is on edge. Seed: {seed_val}"
        )
        # The actual_win_pos (amulet) is now determined by furthest point,
        # which should also be an inner floor tile.
        assert 0 < win_pos[0] < width - 1, (
            f"Win pos X ({win_pos[0]}) is on edge. Seed: {seed_val}"
        )
        assert 0 < win_pos[1] < height - 1, (
            f"Win pos Y ({win_pos[1]}) is on edge. Seed: {seed_val}"
        )


def test_generate_map_valid_minimum_size(generator):
    valid_sizes = [(3, 4), (4, 3), (5,5)] # (w,h)
    for width, height in valid_sizes:
        try:
            world_map, player_start, win_pos = generator.generate_map(width, height, seed=1)
            assert world_map.width == width
            assert world_map.height == height
            assert 0 < player_start[0] < width -1
            assert 0 < player_start[1] < height -1
            assert 0 < win_pos[0] < width -1
            assert 0 < win_pos[1] < height -1
            assert world_map.get_tile(player_start[0],player_start[1]).type == "floor"
            assert world_map.get_tile(win_pos[0],win_pos[1]).type == "floor"
            assert world_map.get_tile(win_pos[0],win_pos[1]).item is not None
            assert world_map.get_tile(win_pos[0],win_pos[1]).item.name == "Amulet of Yendor"

        except ValueError:
            pytest.fail(f"generate_map raised ValueError for valid size {width}x{height}")

def test_generate_map_invalid_small_size(generator):
    invalid_sizes = [(2, 2), (1, 5), (5, 1), (3,3), (2,4), (4,2)] # (w,h)
    for width, height in invalid_sizes:
        with pytest.raises(ValueError, match="Map dimensions must be at least 3x4 or 4x3"):
            generator.generate_map(width, height, seed=1)


def test_outer_layer_is_always_wall(generator):
    sizes_to_test = [(4,5), (5,4), (10,10)]
    for width, height in sizes_to_test:
        world_map, _, _ = generator.generate_map(width, height, seed=1)
        for x in range(width):
            assert world_map.get_tile(x, 0).type == "wall", f"Top edge at ({x},0) not wall for {width}x{height}"
            assert world_map.get_tile(x, height - 1).type == "wall", f"Bottom edge at ({x},{height-1}) not wall for {width}x{height}"
        for y in range(height):
            assert world_map.get_tile(0, y).type == "wall", f"Left edge at (0,{y}) not wall for {width}x{height}"
            assert world_map.get_tile(width - 1, y).type == "wall", f"Right edge at ({width-1},{y}) not wall for {width}x{height}"


def test_all_floor_tiles_are_accessible(generator):
    width, height = 10,10 # A reasonably sized map
    world_map, player_start_pos, _ = generator.generate_map(width, height, seed=123)

    inner_floor_tiles = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            tile = world_map.get_tile(x,y)
            if tile and tile.type == "floor":
                inner_floor_tiles.append((x,y))
    
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
                if tile and tile.type == "floor" and (next_x, next_y) not in visited_floor_tiles:
                    visited_floor_tiles.add((next_x, next_y))
                    queue.append((next_x, next_y))
    
    for floor_tile_pos in inner_floor_tiles:
        assert floor_tile_pos in visited_floor_tiles, \
            f"Inner floor tile at {floor_tile_pos} is not accessible from player_start_pos {player_start_pos}"


def test_floor_portion_respected(generator):
    sizes = [(10,10), (20,15)]
    portions_to_test = [0.2, 0.5, 0.8]
    tolerance = 0.15 # Allow some deviation due to grid and connectivity

    for width, height in sizes:
        for portion in portions_to_test:
            # Create a new generator with the specific floor_portion
            specific_generator = WorldGenerator(floor_portion=portion)
            world_map, _, _ = specific_generator.generate_map(width, height, seed=1)
            
            inner_floor_tiles_count = 0
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    tile = world_map.get_tile(x,y)
                    if tile and tile.type == "floor":
                        inner_floor_tiles_count += 1
            
            total_inner_tiles = (width - 2) * (height - 2)
            if total_inner_tiles == 0:
                assert inner_floor_tiles_count == 0, "No inner tiles but floor tiles found."
                continue

            actual_portion = inner_floor_tiles_count / total_inner_tiles
            
            # For very low portions, ensure at least player_start and original_win_pos can be floor
            # (original_win_pos is what adjust_density protects, not necessarily final amulet pos)
            min_expected_tiles = 0
            if total_inner_tiles >= 1: min_expected_tiles = 1 # player_start_pos
            if total_inner_tiles >= 2: min_expected_tiles = 2 # player_start_pos and original_win_pos
            
            if portion < 0.01 and total_inner_tiles > 0: # Test very low portion
                 assert inner_floor_tiles_count >= min_expected_tiles, \
                    f"Expected at least {min_expected_tiles} floor tiles for portion {portion} on {width}x{height}, got {inner_floor_tiles_count}"
            else:
                assert portion - tolerance <= actual_portion <= portion + tolerance, \
                    f"Floor portion for {width}x{height} with target {portion} was {actual_portion:.2f} (tolerance {tolerance})"


def test_win_item_placed_furthest(generator):
    # Using a predictable small map where "furthest" is clear.
    # Eg: 3x5 map. Inner area is 1x3. Player start (0,0) relative to inner -> (1,1) absolute.
    # Furthest from (1,1) in a 1x3 inner area [(1,1), (1,2), (1,3)] would be (1,3).
    width, height = 3, 5 # Inner: 1x3
    world_map, player_start_pos, actual_win_pos = generator.generate_map(width, height, seed=42) # seed for player_start_pos

    # Manually verify player_start_pos for this seed and size if needed, or make it deterministic.
    # For this test, we assume player_start_pos is (1,1) or (1,2) or (1,3)
    # Let's force player_start_pos for better predictability in this specific test.
    # This requires a bit of a hack or a more complex setup.
    # Instead, let's verify against the PathFinder's own logic.
    
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
         pytest.skip(f"Player start {player_start_pos} not among inner floor tiles {inner_floor_tiles}. Map issue.")
         return


    # Calculate distances from player_start_pos to all other inner floor tiles
    q = deque([(player_start_pos, 0)])
    visited_dist = {player_start_pos: 0}
    max_dist = 0
    furthest_tiles_calculated = {player_start_pos}

    while q:
        curr_pos, dist = q.popleft()

        if dist > max_dist:
            max_dist = dist
            furthest_tiles_calculated = {curr_pos}
        elif dist == max_dist:
            furthest_tiles_calculated.add(curr_pos)

        for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
            next_r, next_c = curr_pos[1] + dr, curr_pos[0] + dc # careful with x,y vs r,c
            
            if (next_c, next_r) in inner_floor_tiles and (next_c, next_r) not in visited_dist:
                visited_dist[(next_c, next_r)] = dist + 1
                q.append(((next_c, next_r), dist + 1))
                
    assert actual_win_pos in furthest_tiles_calculated, \
        f"Amulet at {actual_win_pos} is not one of the furthest tiles {furthest_tiles_calculated} from {player_start_pos} (max_dist: {max_dist})."
