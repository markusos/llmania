import pytest

from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.pathfinding import PathFinder
from src.map_builders.single_floor_builder import SingleFloorBuilder
from src.world_map import WorldMap


@pytest.fixture
def single_floor_builder_factory():
    def _factory(
        width: int,
        height: int,
        seed: int = None,
        floor_portion: float = 0.5,
        existing_map: WorldMap = None,
    ):
        return SingleFloorBuilder(
            width,
            height,
            seed=seed,
            floor_portion=floor_portion,
            existing_map=existing_map,
        )

    return _factory


def test_single_floor_builder_initialization(single_floor_builder_factory):
    builder = single_floor_builder_factory(20, 20, seed=123, floor_portion=0.6)
    assert builder.width == 20
    assert builder.height == 20
    assert builder.seed == 123
    assert builder.floor_portion == 0.6
    assert isinstance(builder.world_map, WorldMap)
    assert isinstance(builder.connectivity_manager, MapConnectivityManager)
    assert isinstance(builder.path_finder, PathFinder)


def test_single_floor_builder_build_return_types(single_floor_builder_factory):
    builder = single_floor_builder_factory(10, 10)  # Valid size
    world_map, player_start, poi_pos = builder.build()
    assert isinstance(world_map, WorldMap)
    assert isinstance(player_start, tuple) and len(player_start) == 2
    assert isinstance(poi_pos, tuple) and len(poi_pos) == 2
    assert world_map.get_tile(player_start[0], player_start[1]).type == "floor"  # type: ignore
    assert world_map.get_tile(poi_pos[0], poi_pos[1]).type == "floor"  # type: ignore


def test_single_floor_builder_map_boundaries_are_walls(single_floor_builder_factory):
    width, height = 10, 10
    builder = single_floor_builder_factory(width, height)
    world_map, _, _ = builder.build()
    for x in range(width):
        assert world_map.get_tile(x, 0).type == "wall"  # type: ignore
        assert world_map.get_tile(x, height - 1).type == "wall"  # type: ignore
    for y in range(height):
        assert world_map.get_tile(0, y).type == "wall"  # type: ignore
        assert world_map.get_tile(width - 1, y).type == "wall"  # type: ignore


@pytest.mark.parametrize("seed_val", [None] + list(range(5)))
def test_single_floor_guaranteed_path_exists(single_floor_builder_factory, seed_val):
    width, height = 10, 10  # Use valid minimum size
    builder = single_floor_builder_factory(width, height, seed=seed_val)
    world_map, player_start, poi_pos = builder.build()

    pathfinder = PathFinder()
    path = pathfinder.a_star_search(world_map, player_start, poi_pos, width, height)

    assert path is not None, f"No path found for seed {seed_val}"
    assert len(path) > 0


def test_single_floor_start_poi_positions_not_on_edge(single_floor_builder_factory):
    for seed_val in range(5):  # Test a few seeds
        width, height = 10, 10  # Use valid minimum
        builder = single_floor_builder_factory(width, height, seed=seed_val)
        _, player_start, poi_pos = builder.build()

        assert 0 < player_start[0] < width - 1, (
            f"Player start X on edge: {player_start} (seed {seed_val})"
        )
        assert 0 < player_start[1] < height - 1, (
            f"Player start Y on edge: {player_start} (seed {seed_val})"
        )
        assert 0 < poi_pos[0] < width - 1, f"POI X on edge: {poi_pos} (seed {seed_val})"
        assert 0 < poi_pos[1] < height - 1, (
            f"POI Y on edge: {poi_pos} (seed {seed_val})"
        )
        assert player_start != poi_pos, (
            f"Player start and POI are same: {player_start} (seed {seed_val})"
        )


def test_single_floor_builder_valid_minimum_size(single_floor_builder_factory):
    valid_sizes = [(10, 10), (12, 15), (15, 12)]
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
            assert player_tile.type == "floor"  # type: ignore
            assert poi_tile.type == "floor"  # type: ignore
        except ValueError:
            pytest.fail(
                f"SingleFloorBuilder raised ValueError for valid size {width}x{height}"
            )


def test_single_floor_builder_invalid_small_size(single_floor_builder_factory):
    # Updated to reflect 10x10 minimum
    invalid_sizes = [(2, 2), (1, 5), (5, 1), (9, 9), (10, 9), (9, 10)]
    for width, height in invalid_sizes:
        with pytest.raises(
            ValueError,
            match=r"Map too small for single floor generation. Minimum size is 10x10",
        ):
            builder = single_floor_builder_factory(width, height, seed=1)
            builder.build()


def test_single_floor_outer_layer_is_always_wall(single_floor_builder_factory):
    sizes_to_test = [(10, 10), (12, 15)]  # Valid sizes
    for width, height in sizes_to_test:
        builder = single_floor_builder_factory(width, height, seed=1)
        world_map, _, _ = builder.build()
        for x in range(width):
            assert world_map.get_tile(x, 0).type == "wall", (
                f"Top edge not wall at ({x},0) for size {width}x{height}"
            )  # type: ignore
            assert world_map.get_tile(x, height - 1).type == "wall", (
                f"Bottom edge not wall at ({x},{height - 1}) for size {width}x{height}"
            )  # type: ignore
        for y in range(1, height - 1):  # Exclude corners already checked
            assert world_map.get_tile(0, y).type == "wall", (
                f"Left edge not wall at (0,{y}) for size {width}x{height}"
            )  # type: ignore
            assert world_map.get_tile(width - 1, y).type == "wall", (
                f"Right edge not wall at ({width - 1},{y}) for size {width}x{height}"
            )  # type: ignore


def test_single_floor_all_floor_tiles_are_accessible(single_floor_builder_factory):
    width, height = 10, 10  # Valid size
    builder = single_floor_builder_factory(width, height, seed=123)
    world_map, player_start_pos, _ = builder.build()

    floor_tiles = []
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if tile := world_map.get_tile(c, r):
                if tile.type == "floor":
                    floor_tiles.append((c, r))

    if (
        not floor_tiles
    ):  # If somehow no floor tiles were generated (should not happen with valid size)
        return  # Or assert False if this state is considered an error

    # Check reachability from player_start_pos to all other floor_tiles
    # This uses the actual MapConnectivityManager, not a mock
    connectivity_manager = MapConnectivityManager()
    reachable_from_start = connectivity_manager.get_reachable_floor_tiles(
        world_map, [player_start_pos], width, height
    )

    for ft_x, ft_y in floor_tiles:
        assert (ft_x, ft_y) in reachable_from_start, (
            f"Unreachable floor tile at ({ft_x},{ft_y}) from {player_start_pos}."
        )


def test_single_floor_floor_portion_respected(single_floor_builder_factory):
    sizes = [(10, 10), (20, 15)]
    portions_to_test = [0.2, 0.5, 0.8]
    # Tolerance for floor portion can be a bit loose due to connectivity constraints
    # and discrete nature of tiles. It's an approximation.
    tolerance_factor = 0.20  # Allow 20% deviation from target portion for this test

    for width, height in sizes:
        total_inner_tiles = (width - 2) * (height - 2)
        for portion in portions_to_test:
            builder = single_floor_builder_factory(
                width, height, seed=1, floor_portion=portion
            )
            world_map, _, _ = builder.build()

            num_floor_tiles = 0
            for r in range(1, height - 1):
                for c in range(1, width - 1):
                    if tile := world_map.get_tile(c, r):
                        if tile.type == "floor":
                            num_floor_tiles += 1

            actual_portion = (
                num_floor_tiles / total_inner_tiles if total_inner_tiles > 0 else 0
            )

            lower_bound = portion - tolerance_factor
            upper_bound = portion + tolerance_factor

            assert lower_bound <= actual_portion <= upper_bound, (
                f"Floor portion mismatch for {width}x{height} map. "
                f"Target: {portion:.2f}, Actual: {actual_portion:.2f}."
            )
