import random
from typing import Optional, List # Ensure this is present

from src.map_algorithms.connectivity import MapConnectivityManager
from src.world_map import WorldMap  # For type hinting


class FloorDensityAdjuster:
    """
    Adjusts the floor density of a map.
    """

    def __init__(self, connectivity_manager: MapConnectivityManager):
        """
        Initializes the FloorDensityAdjuster.

        Args:
            connectivity_manager: An instance of MapConnectivityManager
                                for checking connectivity.
        """
        self.connectivity_manager = connectivity_manager

    def _collect_inner_floor_tiles(
        self, world_map: WorldMap, map_width: int, map_height: int
    ) -> list[tuple[int, int]]:
        """
        Scans the inner area of the map and returns a list of coordinates for
        all "floor" tiles. This method was formerly _collect_floor_tiles in
        WorldGenerator, restricted to inner tiles.
        """
        floor_tiles = []
        # Iterate only over inner tiles
        for y_coord in range(1, map_height - 1):
            for x_coord in range(1, map_width - 1):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "floor":
                    floor_tiles.append((x_coord, y_coord))
        return floor_tiles

    def adjust_density(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],
        original_win_pos: tuple[int, int],  # Still needed to protect this tile
        map_width: int,
        map_height: int,
        target_floor_portion: float,
        protected_coords: Optional[list[tuple[int,int]]] = None
    ) -> None:
        """
        Adjusts the number of floor tiles in the inner map area to match
        target_floor_portion, while maintaining connectivity between player_start_pos
        and original_win_pos. Tiles in protected_coords are not modified.
        This method was formerly _adjust_floor_density in WorldGenerator.
        """
        effective_protected_coords = set(protected_coords) if protected_coords else set()
        # Add player_start and original_win_pos to protected_coords implicitly
        effective_protected_coords.add(player_start_pos)
        effective_protected_coords.add(original_win_pos)

        if map_width < 3 or map_height < 3:
            return

        total_inner_tiles = (map_width - 2) * (map_height - 2)
        if total_inner_tiles <= 0:
            return

        target_floor_tiles = int(target_floor_portion * total_inner_tiles)
        target_floor_tiles = max(
            target_floor_tiles, min(2, total_inner_tiles)
        )  # Ensure at least 2 floors if possible, e.g., for start/win

        current_inner_floor_tiles = self._collect_inner_floor_tiles(
            world_map, map_width, map_height
        )
        num_current_floor = len(current_inner_floor_tiles)

        # Case 1: Too Few Floors
        if num_current_floor < target_floor_tiles:
            # Iteratively convert walls to floors
            while num_current_floor < target_floor_tiles:
                candidate_walls_to_floor = []
                for r_y in range(1, map_height - 1):
                    for r_x in range(1, map_width - 1):
                        if (r_x, r_y) in effective_protected_coords: # Skip protected tiles
                            continue
                        tile = world_map.get_tile(r_x, r_y)
                        if tile and tile.type == "wall":
                            is_adjacent_to_floor = False
                            for dr, dc in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                                adj_x, adj_y = r_x + dr, r_y + dc
                                adj_tile_check = world_map.get_tile(adj_x, adj_y)
                                if adj_tile_check and adj_tile_check.type == "floor":
                                    is_adjacent_to_floor = True
                                    break # Found one adjacent floor, that's enough

                            if is_adjacent_to_floor:
                                # Store without adjacent_floor_count for now, can be added if needed for sorting
                                candidate_walls_to_floor.append((r_x, r_y))

                if not candidate_walls_to_floor:
                    break

                # Sort by adjacent_floor_count (ascending), then shuffle within counts
                # For simplicity now, just sort. Add shuffle later if needed.
                candidate_walls_to_floor.sort(key=lambda x: x[0])
                # For simplicity, just shuffle candidates now. Sorting by adjacency can be added if needed.
                random.shuffle(candidate_walls_to_floor)

                made_change_in_pass = False
                for c_x, c_y in candidate_walls_to_floor: # No longer sorting by adj_count
                    if num_current_floor >= target_floor_tiles:
                        break
                    # Already checked if (c_x,c_y) in effective_protected_coords when building list
                    world_map.set_tile_type(c_x, c_y, "floor")
                    num_current_floor += 1
                    made_change_in_pass = True

                if not made_change_in_pass:
                    break # No suitable walls converted in this pass

        # Case 2: Too Many Floors
        elif num_current_floor > target_floor_tiles:
            # effective_protected_coords already includes player_start_pos and original_win_pos
            candidate_floors_to_wall = [
                (f_x, f_y)
                for f_x, f_y in current_inner_floor_tiles
                if (f_x, f_y) not in effective_protected_coords # Use the broader set
            ]
            random.shuffle(candidate_floors_to_wall)

            path_tiles_to_defer = []
            converted_count = 0

            # First pass: non-deferred tiles
            for c_x, c_y in candidate_floors_to_wall:
                if num_current_floor - converted_count <= target_floor_tiles:
                    break

                # Path Protection Check
                floor_neighbor_count = 0
                neighbors = []  # Store (dx, dy) for actual floor neighbors
                for dr, dc in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # N, S, W, E
                    adj_x, adj_y = c_x + dr, c_y + dc
                    # Ensure neighbor is within map bounds for get_tile
                    if 0 <= adj_x < map_width and 0 <= adj_y < map_height:
                        adj_tile = world_map.get_tile(adj_x, adj_y)
                        if adj_tile and adj_tile.type == "floor":
                            floor_neighbor_count += 1
                            neighbors.append((dr, dc))

                is_path_tile = False
                if floor_neighbor_count == 2:
                    # Check if neighbors are opposite
                    n1_dr, n1_dc = neighbors[0]
                    n2_dr, n2_dc = neighbors[1]
                    if (n1_dr == -n2_dr and n1_dc == n2_dc) or (
                        n1_dc == -n2_dc and n1_dr == n2_dr
                    ):
                        is_path_tile = True

                if is_path_tile:
                    path_tiles_to_defer.append((c_x, c_y))
                    continue  # Defer this tile

                # Not a path tile, attempt conversion
                world_map.set_tile_type(c_x, c_y, "wall")
                if self.connectivity_manager.check_connectivity(
                    world_map, player_start_pos, original_win_pos, map_width, map_height
                ):
                    converted_count += 1
                else:
                    world_map.set_tile_type(c_x, c_y, "floor")  # Revert

            # Second pass: deferred path tiles (if still needed)
            if num_current_floor - converted_count > target_floor_tiles:
                random.shuffle(path_tiles_to_defer)
                for p_x, p_y in path_tiles_to_defer:
                    if num_current_floor - converted_count <= target_floor_tiles:
                        break

                    world_map.set_tile_type(p_x, p_y, "wall")
                    if self.connectivity_manager.check_connectivity(
                        world_map,
                        player_start_pos,
                        original_win_pos,
                        map_width,
                        map_height,
                    ):
                        converted_count += 1
                    else:
                        world_map.set_tile_type(p_x, p_y, "floor")  # Revert
