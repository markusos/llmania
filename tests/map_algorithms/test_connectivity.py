import pytest
from collections import deque
from src.world_map import WorldMap
from src.tile import Tile
from src.map_algorithms.connectivity import MapConnectivityManager

@pytest.fixture
def connectivity_manager():
    return MapConnectivityManager()

@pytest.fixture
def base_world_map():
    # Creates a 5x5 world_map (inner 3x3)
    # Outer border is wall, inner is potential_floor
    # (0,0) (1,0) (2,0) (3,0) (4,0)
    # (0,1) (1,1) (2,1) (3,1) (4,1)
    # (0,2) (1,2) (2,2) (3,2) (4,2)
    # (0,3) (1,3) (2,3) (3,3) (4,3)
    # (0,4) (1,4) (2,4) (3,4) (4,4)
    world_map = WorldMap(5, 5)
    for y in range(5):
        for x in range(5):
            if x == 0 or x == 4 or y == 0 or y == 4:
                world_map.set_tile_type(x, y, "wall")
            else:
                world_map.set_tile_type(x, y, "potential_floor")
    return world_map

# Tests for ensure_connectivity
def test_ensure_connectivity_all_potential_becomes_floor(connectivity_manager, base_world_map):
    # Player start is (1,1), which is potential_floor
    base_world_map.set_tile_type(1,1, "floor") # Set player start as floor
    
    connectivity_manager.ensure_connectivity(base_world_map, (1,1), 5, 5)
    
    # All inner tiles (3x3) should become floor as they are all connected
    for y in range(1, 4): # 1, 2, 3
        for x in range(1, 4): # 1, 2, 3
            assert base_world_map.get_tile(x,y).type == "floor", f"Tile ({x},{y}) should be floor"

def test_ensure_connectivity_unreachable_potential_becomes_wall(connectivity_manager, base_world_map):
    # player_start_pos = (1,1)
    base_world_map.set_tile_type(1,1, "floor") # Player start

    # Create a barrier of wall within potential_floor
    base_world_map.set_tile_type(2,1, "wall")
    base_world_map.set_tile_type(2,2, "wall")
    base_world_map.set_tile_type(2,3, "wall")

    # Tile (1,2) is potential_floor, (3,2) is potential_floor but separated by wall line at x=2
    
    connectivity_manager.ensure_connectivity(base_world_map, (1,1), 5, 5)

    # Reachable from (1,1)
    assert base_world_map.get_tile(1,1).type == "floor"
    assert base_world_map.get_tile(1,2).type == "floor"
    assert base_world_map.get_tile(1,3).type == "floor"
    
    # The barrier itself
    assert base_world_map.get_tile(2,1).type == "wall"
    assert base_world_map.get_tile(2,2).type == "wall"
    assert base_world_map.get_tile(2,3).type == "wall"

    # Unreachable potential_floor tiles should become wall
    assert base_world_map.get_tile(3,1).type == "wall"
    assert base_world_map.get_tile(3,2).type == "wall"
    assert base_world_map.get_tile(3,3).type == "wall"

def test_ensure_connectivity_start_pos_already_floor(connectivity_manager, base_world_map):
    base_world_map.set_tile_type(1,1,"floor") # Player start
    connectivity_manager.ensure_connectivity(base_world_map, (1,1), 5, 5)
    assert base_world_map.get_tile(1,1).type == "floor"


# Tests for check_connectivity
def test_check_connectivity_connected_points(connectivity_manager, base_world_map):
    base_world_map.set_tile_type(1,1,"floor")
    base_world_map.set_tile_type(1,2,"floor")
    base_world_map.set_tile_type(1,3,"floor")
    base_world_map.set_tile_type(2,3,"floor")
    base_world_map.set_tile_type(3,3,"floor")
    
    assert connectivity_manager.check_connectivity(base_world_map, (1,1), (3,3), 5, 5) is True
    assert connectivity_manager.check_connectivity(base_world_map, (1,1), (1,3), 5, 5) is True

def test_check_connectivity_disconnected_points(connectivity_manager, base_world_map):
    base_world_map.set_tile_type(1,1,"floor")
    base_world_map.set_tile_type(1,2,"floor")
    # (1,3) is potential_floor (effectively a wall for this test unless ensure_connectivity is called)
    base_world_map.set_tile_type(2,3,"floor") # This will be unreachable from (1,1) if (1,3) is not floor
    base_world_map.set_tile_type(3,3,"floor")
    
    assert connectivity_manager.check_connectivity(base_world_map, (1,1), (3,3), 5, 5) is False

def test_check_connectivity_same_point(connectivity_manager, base_world_map):
    base_world_map.set_tile_type(1,1,"floor")
    assert connectivity_manager.check_connectivity(base_world_map, (1,1), (1,1), 5, 5) is True
    
    # A non-floor tile is not connected to itself in terms of pathing
    base_world_map.set_tile_type(2,2,"wall") # was potential_floor
    assert connectivity_manager.check_connectivity(base_world_map, (2,2), (2,2), 5, 5) is False

def test_check_connectivity_start_or_end_not_floor(connectivity_manager, base_world_map):
    base_world_map.set_tile_type(1,1,"floor")
    # (1,2) is potential_floor
    assert connectivity_manager.check_connectivity(base_world_map, (1,1), (1,2), 5, 5) is False # (1,2) not floor
    base_world_map.set_tile_type(1,2,"floor")
    base_world_map.set_tile_type(1,3,"wall") # (1,3) is wall
    assert connectivity_manager.check_connectivity(base_world_map, (1,2), (1,3), 5, 5) is False # (1,3) not floor

def test_check_connectivity_out_of_inner_bounds(connectivity_manager, base_world_map):
    base_world_map.set_tile_type(1,1,"floor")
    # (0,1) is an outer wall, (1,0) is an outer wall
    assert connectivity_manager.check_connectivity(base_world_map, (1,1), (0,1), 5, 5) is False
    assert connectivity_manager.check_connectivity(base_world_map, (1,1), (1,0), 5, 5) is False

def test_ensure_connectivity_no_floor_tiles_initially_except_start(connectivity_manager, base_world_map):
    # All inner tiles are potential_floor. player_start_pos is (2,2)
    # ensure_connectivity should make (2,2) floor, then explore from there.
    # No, _select_start_and_win_positions already sets player_start_pos to "floor".
    base_world_map.set_tile_type(2,2, "floor") # Explicitly set for the test
    connectivity_manager.ensure_connectivity(base_world_map, (2,2), 5, 5)
    for y in range(1,4):
        for x in range(1,4):
            assert base_world_map.get_tile(x,y).type == "floor"

def test_ensure_connectivity_on_3x4_map(connectivity_manager):
    # Inner 1x2
    world_map = WorldMap(3,4)
    for y in range(4):
        for x in range(3):
            if x==0 or x==2 or y==0 or y==3:
                world_map.set_tile_type(x,y,"wall")
            else: # (1,1), (1,2) are potential_floor
                world_map.set_tile_type(x,y,"potential_floor")

    world_map.set_tile_type(1,1,"floor") # Player start
    connectivity_manager.ensure_connectivity(world_map, (1,1), 3, 4)
    assert world_map.get_tile(1,1).type == "floor"
    assert world_map.get_tile(1,2).type == "floor"

def test_check_connectivity_on_3x4_map(connectivity_manager):
    world_map = WorldMap(3,4)
    for y in range(4):
        for x in range(3):
            if x==0 or x==2 or y==0 or y==3:
                world_map.set_tile_type(x,y,"wall")
            else:
                world_map.set_tile_type(x,y,"potential_floor") # Initially not floor

    world_map.set_tile_type(1,1,"floor")
    world_map.set_tile_type(1,2,"floor")
    assert connectivity_manager.check_connectivity(world_map, (1,1), (1,2), 3, 4) is True
    
    world_map.set_tile_type(1,2,"wall") # Break connection
    assert connectivity_manager.check_connectivity(world_map, (1,1), (1,2), 3, 4) is False
