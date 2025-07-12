from collections import deque
from typing import Dict, List, Optional, Tuple  # Added Dict, List, Optional, Tuple

from src.world_map import WorldMap  # For type hinting

# No random needed here unless we add path randomization features later


class PathFinder:
    """
    Provides pathfinding and path-carving functionalities on the map.
    """

    def a_star_search(
        self,
        world_map: WorldMap,  # Single map for single-floor A*
        start_pos_xy: Tuple[int, int],
        goal_pos_xy: Tuple[int, int],
        map_width: int,  # Width of the single map
        map_height: int,  # Height of the single map
    ) -> Optional[List[Tuple[int, int]]]:  # Path is List[(x,y)]
        """
        Performs A* pathfinding from start to goal on a single floor.
        Returns a list of (x,y) tuples or None.
        """
        import heapq  # Local import if not already at top level

        open_set: List[Tuple[float, Tuple[int, int]]] = []
        heapq.heappush(open_set, (0, start_pos_xy))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

        g_score: Dict[Tuple[int, int], float] = {start_pos_xy: 0}

        # Heuristic function (Manhattan distance)
        heuristic = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
        f_score: Dict[Tuple[int, int], float] = {
            start_pos_xy: heuristic(start_pos_xy, goal_pos_xy)
        }

        while open_set:
            _, current_xy = heapq.heappop(open_set)

            if current_xy == goal_pos_xy:
                path: List[Tuple[int, int]] = []
                temp = current_xy
                while temp in came_from:
                    path.append(temp)
                    temp = came_from[temp]
                path.append(start_pos_xy)
                return path[::-1]

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                neighbor_xy = (current_xy[0] + dx, current_xy[1] + dy)

                if not (
                    0 <= neighbor_xy[0] < map_width and 0 <= neighbor_xy[1] < map_height
                ):
                    continue

                tile = world_map.get_tile(neighbor_xy[0], neighbor_xy[1])
                if not tile or tile.type == "wall":  # Treat None or wall as unwalkable
                    # Allow pathing to monster only if it's the goal node
                    if tile and tile.monster and neighbor_xy != goal_pos_xy:
                        continue
                    elif not (
                        tile and tile.monster and neighbor_xy == goal_pos_xy
                    ):  # if not monster at goal
                        if not tile or tile.type == "wall":  # and simple wall or None
                            continue

                tentative_g_score = g_score.get(current_xy, float("inf")) + 1

                if tentative_g_score < g_score.get(neighbor_xy, float("inf")):
                    came_from[neighbor_xy] = current_xy
                    g_score[neighbor_xy] = tentative_g_score
                    f_score[neighbor_xy] = tentative_g_score + heuristic(
                        neighbor_xy, goal_pos_xy
                    )
                    if neighbor_xy not in [item[1] for item in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor_xy], neighbor_xy))
        return None  # No path found

    def find_path_bfs(
        self,
        world_maps: Dict[int, WorldMap],
        start_pos_xy: Tuple[int, int],
        start_floor_id: int,
        goal_pos_xy: Tuple[int, int],
        goal_floor_id: int,
    ) -> Optional[List[Tuple[int, int, int]]]:
        """
        Finds a path from (start_pos_xy, start_floor_id) to
        (goal_pos_xy, goal_floor_id) using Breadth-First Search across multiple floors.
        Only considers walkable tiles (not "wall" and no monsters, unless goal).
        Portals are used to transition between floors.

        Args:
            world_maps: A dictionary mapping floor_id to WorldMap objects.
            start_pos_xy: The starting (x, y) coordinates.
            start_floor_id: The starting floor ID.
            goal_pos_xy: The target (x, y) coordinates.
            goal_floor_id: The target floor ID.

        Returns:
            A list of (x, y, floor_id) tuples representing the path,
            or None if no path is found. Includes start and goal positions.
        """
        start_node = (start_pos_xy[0], start_pos_xy[1], start_floor_id)
        goal_node = (goal_pos_xy[0], goal_pos_xy[1], goal_floor_id)

        # queue stores (current_pos_xyz, current_path_xyz_list)
        queue = deque([(start_node, [start_node])])
        # visited stores (x,y,floor_id) tuples
        visited = {start_node}

        while queue:
            (curr_x, curr_y, curr_floor_id), path = queue.popleft()

            if (curr_x, curr_y, curr_floor_id) == goal_node:
                return path

            current_map = world_maps.get(curr_floor_id)
            if not current_map:
                continue  # Should not happen if world_maps is consistent

            # Explore neighbors on the current floor (N, S, W, E)
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                next_x, next_y = curr_x + dx, curr_y + dy
                next_node_on_floor = (next_x, next_y, curr_floor_id)

                if current_map.is_valid_move(next_x, next_y):
                    target_tile = current_map.get_tile(next_x, next_y)
                    if target_tile and target_tile.monster:
                        # Allow pathing to monster only if it's the goal node
                        if next_node_on_floor != goal_node:
                            continue  # Don't path through other monsters

                    if next_node_on_floor not in visited:
                        visited.add(next_node_on_floor)
                        new_path = list(path)
                        new_path.append(next_node_on_floor)
                        queue.append((next_node_on_floor, new_path))

            # Check for portals on the current tile (curr_x, curr_y, curr_floor_id)
            current_tile = current_map.get_tile(curr_x, curr_y)
            if (
                current_tile
                and current_tile.is_portal
                and current_tile.portal_to_floor_id is not None
            ):
                portal_to_floor = current_tile.portal_to_floor_id
                # Portal leads to the same (x,y) on the destination floor
                next_node_via_portal = (curr_x, curr_y, portal_to_floor)

                # Check if destination map for portal exists
                if portal_to_floor not in world_maps:
                    continue

                # Check if the destination tile of the portal is valid to land on
                # (e.g., not a wall, no monster unless it's the goal)
                # This assumes portals are two-way and lead to valid landing spots.
                # If a portal leads directly into a wall on the other side,
                # pathfinding should not use it.
                dest_map_for_portal = world_maps[portal_to_floor]
                dest_tile_of_portal = dest_map_for_portal.get_tile(curr_x, curr_y)

                can_use_portal = False
                if dest_tile_of_portal:
                    if dest_tile_of_portal.type != "wall":
                        if dest_tile_of_portal.monster:
                            # Allow landing on monster only if it's the goal node
                            if next_node_via_portal == goal_node:
                                can_use_portal = True
                            # else: portal blocked by monster
                        else:  # No monster on destination tile
                            can_use_portal = True
                # else: portal leads to invalid tile type or out of bounds on dest map

                if can_use_portal and next_node_via_portal not in visited:
                    visited.add(next_node_via_portal)
                    new_path_portal = list(path)  # Path up to current tile
                    new_path_portal.append(next_node_via_portal)  # Add landing spot
                    queue.append((next_node_via_portal, new_path_portal))

        return None  # No path found

    def find_furthest_point(
        self,
        world_map: WorldMap,
        start_pos: tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> tuple[int, int]:
        """
        Performs a BFS from start_pos to find the furthest reachable "floor" tile
        within the inner map area.
        This method was formerly _find_furthest_reachable_tile in WorldGenerator.
        """
        if not (
            1 <= start_pos[0] < map_width - 1 and 1 <= start_pos[1] < map_height - 1
        ):
            return start_pos  # Start position must be within the inner map

        start_tile = world_map.get_tile(start_pos[0], start_pos[1])
        if not start_tile or start_tile.type != "floor":
            return start_pos  # Cannot start BFS from a non-floor or invalid tile

        queue = deque([(start_pos, 0)])  # (position, distance)
        visited = {start_pos}

        furthest_tile = start_pos
        max_distance = 0

        while queue:
            (curr_x, curr_y), dist = queue.popleft()

            if dist > max_distance:
                max_distance = dist
                furthest_tile = (curr_x, curr_y)

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:  # N, S, E, W
                next_x, next_y = curr_x + dx, curr_y + dy

                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue  # Must be within inner map area

                if (next_x, next_y) not in visited:
                    tile = world_map.get_tile(next_x, next_y)
                    if tile and tile.type == "floor":
                        visited.add((next_x, next_y))
                        queue.append(((next_x, next_y), dist + 1))

        return furthest_tile

    def carve_bresenham_line(
        self,
        world_map: WorldMap,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        map_width: int,
        map_height: int,
        protected_coords: Optional[List[tuple[int, int]]] = None,
    ) -> None:
        """
        Carves a path of "floor" tiles between start_pos and end_pos using a
        Bresenham-like line algorithm. Ensures the path stays within map bounds.
        If protected_coords are provided, tiles at these coordinates will not be changed.
        This method was formerly _carve_path in WorldGenerator.
        """
        path_points = []
        effective_protected_coords = (
            set(protected_coords) if protected_coords else set()
        )
        curr_x, curr_y = start_pos
        dx = end_pos[0] - curr_x
        dy = end_pos[1] - curr_y
        steps = max(abs(dx), abs(dy))

        if steps == 0:
            if 0 <= curr_x < map_width and 0 <= curr_y < map_height:
                path_points.append(start_pos)
        else:
            x_increment = dx / steps
            y_increment = dy / steps
            for i in range(steps + 1):
                px = round(curr_x + i * x_increment)
                py = round(curr_y + i * y_increment)
                if 0 <= px < map_width and 0 <= py < map_height:
                    path_points.append((px, py))

        for px, py in set(
            path_points
        ):  # Use set to avoid redundant checks/sets on same point
            if 0 <= px < map_width and 0 <= py < map_height:
                if (px, py) not in effective_protected_coords:
                    world_map.set_tile_type(px, py, "floor")
