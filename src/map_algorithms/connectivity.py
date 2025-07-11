import random
from collections import deque
from typing import Set, Optional, List # Added Optional, List

from src.map_algorithms.pathfinding import (
    PathFinder,  # For carve_bresenham_line
)
from src.world_map import WorldMap  # For type hinting


class MapConnectivityManager:
    """
    Manages map connectivity operations like ensuring all tiles are accessible
    and checking if two points are connected.
    """

    def _bfs_collect_component(
        self,
        world_map: WorldMap,
        start_node: tuple[int, int],
        map_width: int,
        map_height: int,
        visited_overall: set[tuple[int, int]],
    ) -> set[tuple[int, int]]:
        """
        Performs BFS from start_node to find all connected floor tiles
        that haven't been visited_overall. Marks newly visited nodes
        in visited_overall.
        """
        component_nodes = set()
        if start_node in visited_overall:
            return component_nodes  # Already part of a processed component

        queue = deque([start_node])
        component_visited_this_bfs = {start_node}

        while queue:
            curr_x, curr_y = queue.popleft()
            component_nodes.add((curr_x, curr_y))
            visited_overall.add((curr_x, curr_y))  # Mark as globally visited

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:  # N, S, E, W
                next_x, next_y = curr_x + dx, curr_y + dy

                # Check bounds (must be within inner map area for floor components)
                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue

                tile = world_map.get_tile(next_x, next_y)
                if tile and tile.type == "floor":
                    if (next_x, next_y) not in component_visited_this_bfs:
                        component_visited_this_bfs.add((next_x, next_y))
                        queue.append((next_x, next_y))
        return component_nodes

    def ensure_connectivity(
        self,
        world_map: WorldMap,
        player_start_pos: tuple[int, int],
        map_width: int,
        map_height: int,
        protected_coords: Optional[List[tuple[int,int]]] = None
    ) -> None:
        """
        Ensures all "floor" tiles on the map are connected into a single component.
        Respects protected_coords by passing them to path carving.
        Connects any disconnected floor areas to the main component containing
        the player_start_pos.
        Assumes "potential_floor" tiles are resolved before this.
        """
        path_finder = PathFinder()

        # Ensure player_start_pos is valid and floor, otherwise this logic can fail.
        # WorldGenerator should guarantee this.
        start_tile_check = world_map.get_tile(player_start_pos[0], player_start_pos[1])
        if not start_tile_check or start_tile_check.type != "floor":
            # This is a critical precondition. If player_start_pos is not floor,
            # connectivity cannot be meaningfully established from it.
            # For robustness, one might try to find *any* floor tile to start from,
            # or simply return if no floor tiles exist.
            # However, given the generator's flow, this should be an error state.
            # print(f"Warn: P-start {player_start_pos} not floor. Connect may fail.")
            # Fallback: if player_start_pos is not floor, make it floor.
            world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")

        main_component_nodes = set()
        # Initial BFS from player_start_pos to find the main connected component
        main_component_nodes = self._bfs_collect_component(
            world_map, player_start_pos, map_width, map_height, main_component_nodes
        )

        if not main_component_nodes:  # Should contain at least player_start_pos
            # This implies player_start_pos was not floor or something went very wrong.
            # Add player_start_pos to ensure the loop below has a target.
            main_component_nodes.add(player_start_pos)

        all_floor_tiles_coords = []
        for y_coord in range(1, map_height - 1):
            for x_coord in range(1, map_width - 1):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "floor":
                    all_floor_tiles_coords.append((x_coord, y_coord))

        random.shuffle(all_floor_tiles_coords)  # Process in random order

        for x_coord, y_coord in all_floor_tiles_coords:
            if (x_coord, y_coord) not in main_component_nodes:
                # This tile is floor but not part of the main component yet.
                # It belongs to a disconnected component.

                # Temporarily use a new visited set for this component's BFS
                # Avoid re-exploring nodes already in the main component
                current_component_visited_overall = set(main_component_nodes)

                new_component_nodes = self._bfs_collect_component(
                    world_map,
                    (x_coord, y_coord),
                    map_width,
                    map_height,
                    current_component_visited_overall,  # Mark nodes of new component
                )

                if not new_component_nodes:
                    continue  # Should not happen if (x_coord, y_coord) is floor

                # Connect this new component to the main component
                # Pick a random tile from the new component and main component.
                # For simplicity, connect (x,y) to p_start_pos or use random choices.

                # Ensure main_component_nodes is not empty.
                if not main_component_nodes:  # Impossible if p_start_pos handled.
                    # This state indicates a severe issue. Add p_start_pos as fallback.
                    main_component_nodes.add(player_start_pos)
                    if player_start_pos not in new_component_nodes:  # No self-conn.
                        path_finder.carve_bresenham_line(
                            world_map,
                            (x_coord, y_coord),
                            player_start_pos,
                            map_width,
                            map_height,
                            protected_coords=protected_coords
                        )
                elif new_component_nodes:  # Ensure new_component_nodes is not empty.
                    node_from_new = random.choice(list(new_component_nodes))
                    node_from_main = random.choice(list(main_component_nodes))

                    path_finder.carve_bresenham_line(
                        world_map,
                        node_from_new,
                        node_from_main,
                        map_width,
                        map_height,
                        protected_coords=protected_coords
                    )

                # The main_component_nodes set is rebuilt after each connection by
                # re-running _bfs_collect_component from player_start_pos.
                # This ensures that subsequent checks for unvisited floor tiles
                # correctly identify components disconnected from the *updated*
                # main component. While inefficient, it guarantees correctness.
                updated_main_component_nodes = set()
                main_component_nodes = self._bfs_collect_component(
                    world_map,
                    player_start_pos,
                    map_width,
                    map_height,
                    updated_main_component_nodes,
                )

    def check_connectivity(
        self,
        world_map: WorldMap,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> bool:
        """
        Checks if there is a path of "floor" tiles between start_pos and
        end_pos within the inner map area using BFS.
        This method was formerly _is_connected in WorldGenerator.
        """
        if start_pos == end_pos:
            tile = world_map.get_tile(start_pos[0], start_pos[1])
            return tile is not None and tile.type == "floor"

        queue = deque([start_pos])
        visited = {start_pos}

        start_tile = world_map.get_tile(start_pos[0], start_pos[1])
        if not start_tile or start_tile.type != "floor":
            return False  # Cannot start BFS from a non-floor tile

        while queue:
            curr_x, curr_y = queue.popleft()

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:  # N, S, E, W
                next_x, next_y = curr_x + dx, curr_y + dy

                if (next_x, next_y) == end_pos:
                    end_tile = world_map.get_tile(next_x, next_y)
                    return end_tile is not None and end_tile.type == "floor"

                # Check bounds (must be within inner map area)
                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue

                if (next_x, next_y) not in visited:
                    tile = world_map.get_tile(next_x, next_y)
                    if tile and tile.type == "floor":
                        visited.add((next_x, next_y))
                        queue.append((next_x, next_y))
        return False

    def get_reachable_floor_tiles(
        self,
        world_map: WorldMap,
        start_nodes: list[tuple[int, int]],
        map_width: int,
        map_height: int,
    ) -> Set[tuple[int, int]]:
        """
        Performs a BFS starting from one or more start_nodes to find all
        reachable "floor" tiles within the inner map area.

        Args:
            world_map: The WorldMap instance.
            start_nodes: A list of (x,y) coordinates to start the BFS from.
            map_width: The width of the map.
            map_height: The height of the map.

        Returns:
            A set of (x,y) coordinates of all reachable inner floor tiles.
        """
        reachable_tiles = set()
        queue = deque()
        visited = set()

        for start_node in start_nodes:
            if not (
                1 <= start_node[0] < map_width - 1 and 1 <= start_node[1] < map_height - 1
            ):
                continue # Start node must be within the inner map

            start_tile_obj = world_map.get_tile(start_node[0], start_node[1])
            if start_tile_obj and start_tile_obj.type == "floor" and start_node not in visited:
                queue.append(start_node)
                visited.add(start_node)
                reachable_tiles.add(start_node)

        while queue:
            curr_x, curr_y = queue.popleft()

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:  # N, S, E, W
                next_x, next_y = curr_x + dx, curr_y + dy

                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue  # Must be within inner map area

                if (next_x, next_y) not in visited:
                    tile = world_map.get_tile(next_x, next_y)
                    if tile and tile.type == "floor":
                        visited.add((next_x, next_y))
                        queue.append((next_x, next_y))
                        reachable_tiles.add((next_x, next_y))
        return reachable_tiles
