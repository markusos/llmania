import pytest
from src.world_map import WorldMap
from src.tile import Tile
from src.map_algorithms.connectivity import MapConnectivityManager
from src.map_algorithms.density import FloorDensityAdjuster

@pytest.fixture
def connectivity_manager():
    return MapConnectivityManager()

@pytest.fixture
def density_adjuster(connectivity_manager):
    return FloorDensityAdjuster(connectivity_manager)

@pytest.fixture
def simple_map_5x5():
    # Inner 3x3 area
    world_map = WorldMap(5, 5)
    for y in range(5):
        for x in range(5):
            if x == 0 or x == 4 or y == 0 or y == 4:
                world_map.set_tile_type(x, y, "wall") # Outer wall
            else:
                world_map.set_tile_type(x, y, "wall") # Inner initially all wall
    return world_map

# Test _collect_inner_floor_tiles (indirectly tested by adjust_density, but a direct test is good)
def test_collect_inner_floor_tiles(density_adjuster, simple_map_5x5):
    # simple_map_5x5 has all inner walls initially
    assert len(density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5)) == 0
    
    simple_map_5x5.set_tile_type(1,1, "floor")
    simple_map_5x5.set_tile_type(2,2, "floor")
    simple_map_5x5.set_tile_type(3,3, "floor")
    # Outer floor tile, should not be collected
    simple_map_5x5.set_tile_type(0,0, "floor") 


    floor_tiles = density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5)
    assert len(floor_tiles) == 3
    assert (1,1) in floor_tiles
    assert (2,2) in floor_tiles
    assert (3,3) in floor_tiles
    assert (0,0) not in floor_tiles


# Tests for adjust_density
def test_adjust_density_too_few_floors(density_adjuster, simple_map_5x5):
    # Inner 3x3 = 9 tiles. Target 50% = 4.5 -> 4 tiles (or 5 depending on rounding)
    # Start with 2 floor tiles
    player_start = (1,1)
    original_win = (3,3) # Also a floor tile
    simple_map_5x5.set_tile_type(player_start[0], player_start[1], "floor")
    simple_map_5x5.set_tile_type(original_win[0], original_win[1], "floor")

    initial_floor_count = len(density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5))
    assert initial_floor_count == 2
    
    target_portion = 0.5 # Expect int(0.5 * 9) = 4 tiles
    density_adjuster.adjust_density(simple_map_5x5, player_start, original_win, 5, 5, target_portion)
    
    final_floor_count = len(density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5))
    
    # target_floor_tiles = int(target_floor_portion * total_inner_tiles) -> int(0.5*9)=4
    # target_floor_tiles = max(target_floor_tiles, min(2, total_inner_tiles)) -> max(4, min(2,9)) = max(4,2) = 4
    assert final_floor_count >= 4 # Should add tiles to reach target
    assert simple_map_5x5.get_tile(player_start[0], player_start[1]).type == "floor" # Protected
    assert simple_map_5x5.get_tile(original_win[0], original_win[1]).type == "floor" # Protected

def test_adjust_density_too_many_floors(density_adjuster, connectivity_manager, simple_map_5x5):
    # Inner 3x3 = 9 tiles.
    # Make all 9 inner tiles floor initially
    player_start = (1,1)
    original_win = (3,3) # Must be different for some connectivity tests
    for y in range(1,4):
        for x in range(1,4):
            simple_map_5x5.set_tile_type(x,y,"floor")
    
    initial_floor_count = len(density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5))
    assert initial_floor_count == 9
    
    target_portion = 0.3 # Expect int(0.3 * 9) = 2 tiles
                         # max(2, min(2,9)) = 2. So target is 2.
    density_adjuster.adjust_density(simple_map_5x5, player_start, original_win, 5, 5, target_portion)
    
    final_floor_count = len(density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5))
    
    assert final_floor_count <= 2 or final_floor_count == initial_floor_count # Should remove tiles or do nothing if it can't
    assert simple_map_5x5.get_tile(player_start[0], player_start[1]).type == "floor" # Protected
    assert simple_map_5x5.get_tile(original_win[0], original_win[1]).type == "floor" # Protected
    
    # Check connectivity between player_start and original_win is maintained
    assert connectivity_manager.check_connectivity(simple_map_5x5, player_start, original_win, 5, 5)

def test_adjust_density_target_zero_portion(density_adjuster, connectivity_manager, simple_map_5x5):
    player_start = (1,1)
    original_win = (1,3) # Different from start
    simple_map_5x5.set_tile_type(1,1,"floor")
    simple_map_5x5.set_tile_type(1,2,"floor")
    simple_map_5x5.set_tile_type(1,3,"floor")
    
    target_portion = 0.0 # Expect min 2 tiles (player_start, original_win)
    density_adjuster.adjust_density(simple_map_5x5, player_start, original_win, 5, 5, target_portion)
    
    final_floor_count = len(density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5))
    # total_inner_tiles = 9. target = int(0*9)=0. max(0, min(2,9)) = 2.
    assert final_floor_count == 2
    assert simple_map_5x5.get_tile(player_start[0], player_start[1]).type == "floor"
    assert simple_map_5x5.get_tile(original_win[0], original_win[1]).type == "floor"
    assert connectivity_manager.check_connectivity(simple_map_5x5, player_start, original_win, 5, 5)

def test_adjust_density_target_full_portion(density_adjuster, simple_map_5x5):
    player_start = (1,1)
    original_win = (3,3)
    simple_map_5x5.set_tile_type(player_start[0], player_start[1], "floor")
    
    target_portion = 1.0 # Expect all 9 inner tiles to be floor
    density_adjuster.adjust_density(simple_map_5x5, player_start, original_win, 5, 5, target_portion)
    
    final_floor_count = len(density_adjuster._collect_inner_floor_tiles(simple_map_5x5, 5, 5))
    assert final_floor_count == 9 # All inner tiles should be floor

def test_adjust_density_minimal_map_3x4(density_adjuster, connectivity_manager):
    # Inner 1x2 area (2 tiles total)
    world_map = WorldMap(3,4)
    for y in range(4):
        for x in range(3):
            world_map.set_tile_type(x,y,"wall") # Start all wall

    player_start = (1,1)
    original_win = (1,2)
    world_map.set_tile_type(player_start[0],player_start[1],"floor")
    world_map.set_tile_type(original_win[0],original_win[1],"floor")

    # Target 50% of 2 tiles = 1 tile. But min(2,2) = 2. So target is 2.
    density_adjuster.adjust_density(world_map, player_start, original_win, 3, 4, 0.5)
    final_floor_count = len(density_adjuster._collect_inner_floor_tiles(world_map, 3, 4))
    assert final_floor_count == 2

    # Target 100% of 2 tiles = 2 tiles.
    world_map.set_tile_type(player_start[0],player_start[1],"wall") # Reset one
    world_map.set_tile_type(original_win[0],original_win[1],"floor")
    density_adjuster.adjust_density(world_map, original_win, player_start, 3, 4, 1.0) # original_win is start, player_start is end
    final_floor_count = len(density_adjuster._collect_inner_floor_tiles(world_map, 3, 4))
    assert final_floor_count == 2
    assert world_map.get_tile(1,1).type == "floor"
    assert world_map.get_tile(1,2).type == "floor"
    assert connectivity_manager.check_connectivity(world_map, player_start, original_win, 3, 4)
