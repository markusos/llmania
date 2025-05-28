import random

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
    ) -> None:
        """
        Adjusts the number of floor tiles in the inner map area to match
        target_floor_portion, while maintaining connectivity between player_start_pos
        and original_win_pos.
        This method was formerly _adjust_floor_density in WorldGenerator.
        """
        if map_width < 3 or map_height < 3:
            return  # Should be caught by generator earlier

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
                        tile = world_map.get_tile(r_x, r_y)
                        if tile and tile.type == "wall":
                            is_adjacent_to_floor = False
                            # Check N, S, E, W neighbors for an existing floor tile
                            for dr, dc in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                                adj_x, adj_y = r_x + dr, r_y + dc
                                # Adjacency check can be to any tile on map,
                                # not just inner ones.
                                adj_tile_check = world_map.get_tile(adj_x, adj_y)
                                if adj_tile_check and adj_tile_check.type == "floor":
                                    is_adjacent_to_floor = True
                                    break
                            if is_adjacent_to_floor:
                                candidate_walls_to_floor.append((r_x, r_y))

                if not candidate_walls_to_floor:
                    break  # No more walls can be converted by adjacency

                random.shuffle(candidate_walls_to_floor)

                made_change_in_pass = False
                for c_x, c_y in candidate_walls_to_floor:
                    if num_current_floor >= target_floor_tiles:
                        break
                    world_map.set_tile_type(c_x, c_y, "floor")
                    num_current_floor += 1  # Increment actual current floor count
                    made_change_in_pass = True

                if not made_change_in_pass:
                    break  # No progress in this pass, stop to prevent infinite loop

        # Case 2: Too Many Floors
        elif num_current_floor > target_floor_tiles:
            # Note: current_inner_floor_tiles and num_current_floor are up-to-date
            # from the collection before the "Too Few Floors" / "Too Many Floors" split.
            # No need to re-collect unless floors were added in the "Too Few" branch,
            # but these branches are exclusive.

            protected_tiles = {player_start_pos, original_win_pos}
            candidate_floors_to_wall = [
                (f_x, f_y)
                for f_x, f_y in current_inner_floor_tiles
                if (f_x, f_y) not in protected_tiles
            ]
            random.shuffle(candidate_floors_to_wall)

            converted_count = 0
            for c_x, c_y in candidate_floors_to_wall:
                if num_current_floor - converted_count <= target_floor_tiles:
                    break

                world_map.set_tile_type(c_x, c_y, "wall")

                if self.connectivity_manager.check_connectivity(
                    world_map,
                    player_start_pos,
                    original_win_pos,
                    map_width,
                    map_height,
                ):
                    converted_count += 1
                else:
                    world_map.set_tile_type(c_x, c_y, "floor")  # Revert
