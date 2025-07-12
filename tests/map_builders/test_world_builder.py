import pytest

from src.map_builders.world_builder import WorldBuilder
from src.world_map import WorldMap


@pytest.fixture
def world_builder():
    return WorldBuilder(20, 20, seed=123, num_floors=3)


def test_world_builder_initialization(world_builder):
    assert world_builder.width == 20
    assert world_builder.height == 20
    assert world_builder.seed == 123
    assert world_builder.num_floors == 3


def test_world_builder_build_return_types(world_builder):
    (
        world_maps,
        player_start_full,
        amulet_full_pos,
        floor_details,
    ) = world_builder.build()
    assert isinstance(world_maps, dict)
    assert len(world_maps) == 3
    for floor_id, world_map in world_maps.items():
        assert isinstance(floor_id, int)
        assert isinstance(world_map, WorldMap)

    assert isinstance(player_start_full, tuple)
    assert len(player_start_full) == 3
    assert isinstance(amulet_full_pos, tuple)
    assert len(amulet_full_pos) == 3
    assert isinstance(floor_details, list)
    assert len(floor_details) == 3


def test_portal_properties_and_bidirectionality(world_builder):
    world_maps, _, _, _ = world_builder.build()
    if len(world_maps) <= 1:
        pytest.skip("Not enough floors to test portal properties meaningfully.")
        return

    portals_found = 0
    for floor_id, current_map in world_maps.items():
        for y in range(1, world_builder.height - 1):
            for x in range(1, world_builder.width - 1):
                tile = current_map.get_tile(x, y)
                if tile and tile.is_portal:
                    portals_found += 1
                    assert (
                        tile.type == "portal"
                    ), f"Tile ({x},{y}) on floor {floor_id} is_portal but type is {tile.type}"
                    assert (
                        tile.portal_to_floor_id is not None
                    ), f"Portal at ({x},{y}) on floor {floor_id} has no destination."
                    assert (
                        tile.portal_to_floor_id in world_maps
                    ), f"Portal at ({x},{y}) on floor {floor_id} leads to non-existent floor {tile.portal_to_floor_id}"

                    dest_floor_id = tile.portal_to_floor_id
                    dest_map = world_maps[dest_floor_id]
                    dest_tile = dest_map.get_tile(x, y)

                    assert (
                        dest_tile is not None
                    ), f"Portal destination ({x},{y}) on floor {dest_floor_id} is None (from floor {floor_id})."
                    assert (
                        dest_tile.is_portal
                    ), f"Portal destination ({x},{y}) on floor {dest_floor_id} is not a portal. (Linked from floor {floor_id})"
                    assert (
                        dest_tile.type == "portal"
                    ), f"Portal destination ({x},{y}) on floor {dest_floor_id} is not of type 'portal'."
                    assert (
                        dest_tile.portal_to_floor_id == floor_id
                    ), f"Portal at ({x},{y}) on floor {dest_floor_id} does not lead back to floor {floor_id}."

    assert (
        portals_found > 0
    ), "No portals found in a multi-floor world. Connectivity issue."


def test_no_items_or_monsters_on_portal_tiles(world_builder):
    world_maps, _, _, _ = world_builder.build()
    for floor_id, current_map in world_maps.items():
        for y in range(current_map.height):
            for x in range(current_map.width):
                tile = current_map.get_tile(x, y)
                if tile and tile.is_portal:
                    assert (
                        tile.item is None
                    ), f"Item {tile.item.name if tile.item else ''} found on portal at ({x},{y}) on floor {floor_id}"
                    assert (
                        tile.monster is None
                    ), f"Monster {tile.monster.name if tile.monster else ''} found on portal at ({x},{y}) on floor {floor_id}"
