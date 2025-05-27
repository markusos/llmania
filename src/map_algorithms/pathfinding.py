from collections import deque
from src.world_map import WorldMap # For type hinting
# No random needed here unless we add path randomization features later

class PathFinder:
    """
    Provides pathfinding and path-carving functionalities on the map.
    """

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
        if not (1 <= start_pos[0] < map_width - 1 and 1 <= start_pos[1] < map_height - 1):
            return start_pos # Start position must be within the inner map
        
        start_tile = world_map.get_tile(start_pos[0], start_pos[1])
        if not start_tile or start_tile.type != "floor":
            return start_pos # Cannot start BFS from a non-floor or invalid tile

        queue = deque([(start_pos, 0)])  # (position, distance)
        visited = {start_pos}
        
        furthest_tile = start_pos
        max_distance = 0

        while queue:
            (curr_x, curr_y), dist = queue.popleft()

            if dist > max_distance:
                max_distance = dist
                furthest_tile = (curr_x, curr_y)

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]: # N, S, E, W
                next_x, next_y = curr_x + dx, curr_y + dy

                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue # Must be within inner map area

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
    ) -> None:
        """
        Carves a path of "floor" tiles between start_pos and end_pos using a
        Bresenham-like line algorithm. Ensures the path stays within map bounds.
        This method was formerly _carve_path in WorldGenerator.
        """
        path_points = []
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

        for px, py in set(path_points):
            if 0 <= px < map_width and 0 <= py < map_height:
                world_map.set_tile_type(px, py, "floor")
