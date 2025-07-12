from src.world_generator import WorldGenerator
from src.world_map import WorldMap


def test_generate_world_returns_correct_types():
    width, height = 30, 20
    generator = WorldGenerator()
    world_maps, player_start_pos, amulet_pos, floor_details = generator.generate_world(
        width, height
    )

    assert isinstance(world_maps, dict)
    assert len(world_maps) > 0
    for floor_id, world_map in world_maps.items():
        assert isinstance(floor_id, int)
        assert isinstance(world_map, WorldMap)
        assert world_map.width == width
        assert world_map.height == height

    assert isinstance(player_start_pos, tuple) and len(player_start_pos) == 3
    assert 0 <= player_start_pos[0] < width and 0 <= player_start_pos[1] < height
    assert player_start_pos[2] in world_maps

    assert isinstance(amulet_pos, tuple) and len(amulet_pos) == 3
    assert 0 <= amulet_pos[0] < width and 0 <= amulet_pos[1] < height
    assert amulet_pos[2] in world_maps

    assert isinstance(floor_details, list) and len(floor_details) == len(world_maps)
    if floor_details:
        for detail in floor_details:
            assert isinstance(detail, dict)
            assert "id" in detail and "map" in detail
            assert "start" in detail and "poi" in detail


def test_world_generation_with_seed_is_deterministic():
    width, height, seed = 25, 15, 12345
    generator1 = WorldGenerator()
    maps1, ps1, ap1, fd1 = generator1.generate_world(width, height, seed=seed)

    generator2 = WorldGenerator()
    maps2, ps2, ap2, fd2 = generator2.generate_world(width, height, seed=seed)

    assert ps1 == ps2
    assert ap1 == ap2
    assert len(maps1) == len(maps2)

    # Compare floor details
    fd1_sorted = sorted(fd1, key=lambda x: x["id"])
    fd2_sorted = sorted(fd2, key=lambda x: x["id"])
    for d1, d2 in zip(fd1_sorted, fd2_sorted):
        assert d1["start"] == d2["start"]
        assert d1["poi"] == d2["poi"]

    # Compare maps tile by tile
    for floor_id in maps1:
        assert floor_id in maps2
        map1 = maps1[floor_id]
        map2 = maps2[floor_id]
        for y in range(height):
            for x in range(width):
                tile1 = map1.get_tile(x, y)
                tile2 = map2.get_tile(x, y)
                assert tile1.type == tile2.type
                assert tile1.is_portal == tile2.is_portal
                assert tile1.portal_to_floor_id == tile2.portal_to_floor_id


def test_world_generation_without_seed_is_non_deterministic():
    width, height = 22, 18
    generator = WorldGenerator()
    maps1, ps1, ap1, _ = generator.generate_world(width, height, seed=None)
    maps2, ps2, ap2, _ = generator.generate_world(width, height, seed=None)

    are_different = ps1 != ps2 or ap1 != ap2 or len(maps1) != len(maps2)
    if not are_different:
        maps3, ps3, ap3, _ = generator.generate_world(width, height, seed=None)
        are_different = ps1 != ps3 or ap1 != ap3 or len(maps1) != len(maps3)

    assert are_different, "Worlds generated without seed were identical."
