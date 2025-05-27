from collections import deque
from src.world_map import WorldMap # For type hinting

class MapConnectivityManager:
    """
    Manages map connectivity operations like ensuring all tiles are accessible
    and checking if two points are connected.
    """

    def ensure_connectivity(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> None:
        """
        Ensures all accessible "potential_floor" tiles from player_start_pos are
        converted to "floor", and inaccessible "potential_floor" tiles become "wall".
        The search area is confined to the inner map (excluding the strict outer border).
        This method was formerly _ensure_all_tiles_accessible in WorldGenerator.
        """
        queue = deque([player_start_pos])
        visited = {player_start_pos}

        # Ensure player_start_pos itself is marked as floor if it's a potential_floor
        # This can happen if _select_start_and_win_positions sets it so.
        # The original _ensure_all_tiles_accessible implicitly handled this by starting BFS
        # and then converting all visited to floor.
        # Explicitly setting it here can be a good idea if player_start_pos was potential_floor.
        # However, _select_start_and_win_positions already sets it to "floor".

        while queue:
            curr_x, curr_y = queue.popleft()

            # Explorable neighbors (N, S, E, W)
            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                next_x, next_y = curr_x + dx, curr_y + dy

                # Check bounds (must be within inner map area)
                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue

                if (next_x, next_y) not in visited:
                    tile = world_map.get_tile(next_x, next_y)
                    # Explorable if it's potential_floor or already floor
                    if tile and (tile.type == "potential_floor" or tile.type == "floor"):
                        visited.add((next_x, next_y))
                        queue.append((next_x, next_y))

        # Convert all visited tiles to "floor"
        # This includes player_start_pos and original_win_pos if they were visited.
        for x_coord, y_coord in visited:
            world_map.set_tile_type(x_coord, y_coord, "floor")

        # Convert unvisited inner "potential_floor" tiles to "wall"
        for y_coord in range(1, map_height - 1):
            for x_coord in range(1, map_width - 1):
                if (x_coord, y_coord) not in visited:
                    tile = world_map.get_tile(x_coord, y_coord)
                    if tile and tile.type == "potential_floor":
                        world_map.set_tile_type(x_coord, y_coord, "wall")

    def check_connectivity(
        self,
        world_map: WorldMap,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> bool:
        """
        Checks if there is a path of floor tiles between start_pos and end_pos
        within the inner map area using BFS.
        This method was formerly _is_connected in WorldGenerator.
        """
        if start_pos == end_pos:
            # Tile is connected to itself if it's a floor.
            # We assume start_pos and end_pos are valid floor tiles for this check.
            # Or, if they are the same tile, connectivity depends on it being floor.
            tile = world_map.get_tile(start_pos[0], start_pos[1])
            return tile is not None and tile.type == "floor"


        queue = deque([start_pos])
        visited = {start_pos}

        # Ensure start_pos itself is a floor tile before starting BFS
        start_tile_obj = world_map.get_tile(start_pos[0], start_pos[1])
        if not start_tile_obj or start_tile_obj.type != "floor":
            return False # Cannot start BFS from a non-floor tile

        while queue:
            curr_x, curr_y = queue.popleft()

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:  # N, S, E, W
                next_x, next_y = curr_x + dx, curr_y + dy

                if (next_x, next_y) == end_pos:
                    # Check if end_pos is actually a floor tile
                    end_tile_obj = world_map.get_tile(next_x, next_y)
                    return end_tile_obj is not None and end_tile_obj.type == "floor"

                # Check bounds (must be within inner map area)
                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue

                if (next_x, next_y) not in visited:
                    tile = world_map.get_tile(next_x, next_y)
                    if tile and tile.type == "floor":
                        visited.add((next_x, next_y))
                        queue.append((next_x, next_y))
        return False
