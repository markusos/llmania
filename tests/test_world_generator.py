import pytest

from src.world_generator import WorldGenerator
from src.world_map import WorldMap


@pytest.fixture
def generator():
    return WorldGenerator()


def test_generate_world_return_types(generator):
    # This test now implicitly tests the integration of WorldGenerator with WorldBuilder
    world_maps, player_start_full, amulet_full_pos, floor_details = generator.generate_world(15, 15, seed=777)

    assert isinstance(world_maps, dict)
    assert len(world_maps) > 0
    for floor_id, world_map in world_maps.items():
        assert isinstance(floor_id, int)
        assert isinstance(world_map, WorldMap)

    assert isinstance(player_start_full, tuple)
    assert len(player_start_full) == 3
    assert isinstance(amulet_full_pos, tuple)
    assert len(amulet_full_pos) == 3
    assert isinstance(floor_details, list)


def test_generate_world_reproducibility_with_seed(generator):
    width, height, seed = 20, 20, 42

    maps1, ps1, ap1, fd1 = generator.generate_world(width, height, seed=seed)
    maps2, ps2, ap2, fd2 = generator.generate_world(width, height, seed=seed)

    assert ps1 == ps2, "Player start positions differ with the same seed."
    assert ap1 == ap2, "Amulet positions differ with the same seed."
    assert len(maps1) == len(maps2), "Number of floors differs with the same seed."

    for floor_id in maps1:
        map1 = maps1[floor_id]
        map2 = maps2[floor_id]
        for y in range(height):
            for x in range(width):
                tile1 = map1.get_tile(x, y)
                tile2 = map2.get_tile(x, y)
                assert tile1.type == tile2.type, f"Tile type at ({x},{y}) on floor {floor_id} differs."
                # More detailed checks for items/monsters can be added if needed,
                # but are likely better placed in builder-specific tests.


def test_generate_world_with_different_seeds(generator):
    width, height = 10, 10
    seed1, seed2 = 123, 456

    maps1, ps1, ap1, _ = generator.generate_world(width, height, seed=seed1)
    maps2, ps2, ap2, _ = generator.generate_world(width, height, seed=seed2)

    # It's highly probable results will differ. A simple check of key positions is sufficient.
    are_different = ps1 != ps2 or ap1 != ap2 or len(maps1) != len(maps2)
    if not are_different:
        # If key positions are the same, do a deeper check of a map layout
        map1_repr = "".join(maps1[0].get_tile(x, y).type[0] for y in range(height) for x in range(width))
        map2_repr = "".join(maps2[0].get_tile(x, y).type[0] for y in range(height) for x in range(width))
        if map1_repr != map2_repr:
            are_different = True

    assert are_different, "Worlds generated with different seeds were identical, which is highly unlikely."
