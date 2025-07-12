import random

import pytest

from src.map_builders.world_builder import WorldBuilder
from src.world_map import WorldMap


def test_world_generation_multiple_floors():
    width, height, num_floors = 20, 20, 3
    builder = WorldBuilder(
        width, height, num_floors=num_floors, random_generator=random.Random(123)
    )
    world_maps, player_start, amulet_pos, floor_details = builder.build()

    assert len(world_maps) == num_floors
    assert len(floor_details) == num_floors
    for floor_id, world_map in world_maps.items():
        assert isinstance(world_map, WorldMap)
        assert world_map.width == width
        assert world_map.height == height

    assert 0 <= player_start[0] < width
    assert 0 <= player_start[1] < height
    assert 0 <= player_start[2] < num_floors
    assert 0 <= amulet_pos[0] < width
    assert 0 <= amulet_pos[1] < height
    assert 0 <= amulet_pos[2] < num_floors

    if num_floors > 1:
        assert player_start[2] != amulet_pos[2], "Amulet on different floor"


def test_portal_connectivity_and_bidirectionality():
    width, height, num_floors = 15, 15, 4
    builder = WorldBuilder(
        width, height, num_floors=num_floors, random_generator=random.Random(42)
    )
    world_maps, _, _, _ = builder.build()

    portals_found = 0
    for floor_id, current_map in world_maps.items():
        for y in range(height):
            for x in range(width):
                tile = current_map.get_tile(x, y)
                if tile and tile.is_portal:
                    portals_found += 1
                    assert tile.type == "portal"
                    assert tile.portal_to_floor_id is not None
                    assert tile.portal_to_floor_id in world_maps

                    dest_map = world_maps[tile.portal_to_floor_id]
                    dest_tile = dest_map.get_tile(x, y)
                    assert dest_tile is not None and dest_tile.is_portal
                    assert dest_tile.portal_to_floor_id == floor_id

    if num_floors > 1 and width > 5 and height > 5:
        assert portals_found > 0, "No portals found."


def test_no_items_or_monsters_on_portal_tiles():
    builder = WorldBuilder(12, 12, num_floors=2, random_generator=random.Random(777))
    world_maps, _, _, _ = builder.build()

    for floor_id, current_map in world_maps.items():
        for y in range(12):
            for x in range(12):
                tile = current_map.get_tile(x, y)
                if tile and tile.is_portal:
                    assert tile.item is None, f"Item on portal at ({x},{y})"
                    assert tile.monster is None, f"Monster on portal at ({x},{y})"


def test_amulet_placement():
    builder = WorldBuilder(10, 10, num_floors=1, random_generator=random.Random(1))
    world_maps, _, amulet_pos, _ = builder.build()
    amulet_map = world_maps[amulet_pos[2]]
    amulet_tile = amulet_map.get_tile(amulet_pos[0], amulet_pos[1])
    assert amulet_tile is not None and amulet_tile.item is not None
    assert amulet_tile.item.name == "Amulet of Yendor"


def test_minimum_floor_size():
    with pytest.raises(ValueError, match="Map too small"):
        WorldBuilder(5, 5, num_floors=1, random_generator=random.Random(1)).build()
    with pytest.raises(ValueError, match="Map too small"):
        WorldBuilder(10, 5, num_floors=1, random_generator=random.Random(2)).build()
    try:
        WorldBuilder(10, 10, num_floors=1, random_generator=random.Random(4)).build()
    except ValueError:
        pytest.fail("WorldBuilder failed with valid dimensions.")


def test_portal_uniqueness_on_floor():
    builder = WorldBuilder(20, 20, num_floors=3, random_generator=random.Random(12345))
    world_maps, _, _, _ = builder.build()

    for floor_id, current_map in world_maps.items():
        portal_coords = set()
        for y in range(20):
            for x in range(20):
                tile = current_map.get_tile(x, y)
                if tile and tile.is_portal:
                    pos = (x, y)
                    assert pos not in portal_coords, f"Duplicate portal at {pos}"
                    portal_coords.add(pos)


def test_all_floors_connected():
    num_floors = 5
    builder = WorldBuilder(
        20, 20, num_floors=num_floors, random_generator=random.Random(67890)
    )
    world_maps, _, _, _ = builder.build()

    adj = {i: [] for i in range(num_floors)}
    for floor_id, current_map in world_maps.items():
        for y in range(20):
            for x in range(20):
                tile = current_map.get_tile(x, y)
                if tile and tile.is_portal and tile.portal_to_floor_id is not None:
                    if floor_id != tile.portal_to_floor_id:
                        adj[floor_id].append(tile.portal_to_floor_id)

    q, visited = [0], {0}
    head = 0
    while head < len(q):
        u = q[head]
        head += 1
        for v_neighbor in adj.get(u, []):
            if v_neighbor not in visited:
                visited.add(v_neighbor)
                q.append(v_neighbor)

    assert len(visited) == num_floors, f"Not all floors connected: {visited}"


def test_world_builder_with_seed_is_deterministic():
    width, height, num_floors, seed = 20, 20, 3, 123
    builder1 = WorldBuilder(
        width, height, num_floors=num_floors, random_generator=random.Random(seed)
    )
    world_maps1, player_start1, amulet_pos1, _ = builder1.build()

    builder2 = WorldBuilder(
        width, height, num_floors=num_floors, random_generator=random.Random(seed)
    )
    world_maps2, player_start2, amulet_pos2, _ = builder2.build()

    assert player_start1 == player_start2
    assert amulet_pos1 == amulet_pos2
    assert len(world_maps1) == len(world_maps2)

    for floor_id in world_maps1:
        assert floor_id in world_maps2
        map1 = world_maps1[floor_id]
        map2 = world_maps2[floor_id]
        for y in range(height):
            for x in range(width):
                tile1 = map1.get_tile(x, y)
                tile2 = map2.get_tile(x, y)
                assert tile1.type == tile2.type
                assert tile1.is_portal == tile2.is_portal
                assert tile1.portal_to_floor_id == tile2.portal_to_floor_id
