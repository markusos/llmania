from collections import deque
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

from src.map_algorithms.pathfinding import PathFinder
from src.world_map import WorldMap

if TYPE_CHECKING:
    from random import Random


class MapConnectivityManager:
    def __init__(self, random_generator: "Random"):
        self.random = random_generator

    def _bfs_collect_component(
        self,
        world_map: WorldMap,
        start_node: tuple[int, int],
        map_width: int,
        map_height: int,
        visited_overall: set[tuple[int, int]],
    ) -> set[tuple[int, int]]:
        component_nodes = set()
        if start_node in visited_overall:
            return component_nodes

        queue = deque([start_node])
        component_visited_this_bfs = {start_node}

        while queue:
            curr_x, curr_y = queue.popleft()
            component_nodes.add((curr_x, curr_y))
            visited_overall.add((curr_x, curr_y))

            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                next_x, next_y = curr_x + dx, curr_y + dy
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
        protected_coords: Optional[List[tuple[int, int]]] = None,
    ) -> None:
        path_finder = PathFinder()
        start_tile_check = world_map.get_tile(player_start_pos[0], player_start_pos[1])
        if not start_tile_check or start_tile_check.type != "floor":
            world_map.set_tile_type(player_start_pos[0], player_start_pos[1], "floor")

        main_component_nodes = set()
        main_component_nodes = self._bfs_collect_component(
            world_map, player_start_pos, map_width, map_height, main_component_nodes
        )
        if not main_component_nodes:
            main_component_nodes.add(player_start_pos)

        all_floor_tiles_coords = []
        for y_coord in range(1, map_height - 1):
            for x_coord in range(1, map_width - 1):
                tile = world_map.get_tile(x_coord, y_coord)
                if tile and tile.type == "floor":
                    all_floor_tiles_coords.append((x_coord, y_coord))
        self.random.shuffle(all_floor_tiles_coords)

        for x_coord, y_coord in all_floor_tiles_coords:
            if (x_coord, y_coord) not in main_component_nodes:
                current_component_visited_overall = set(main_component_nodes)
                new_component_nodes = self._bfs_collect_component(
                    world_map,
                    (x_coord, y_coord),
                    map_width,
                    map_height,
                    current_component_visited_overall,
                )
                if not new_component_nodes:
                    continue
                if not main_component_nodes:
                    main_component_nodes.add(player_start_pos)
                    if player_start_pos not in new_component_nodes:
                        path_finder.carve_bresenham_line(
                            world_map,
                            (x_coord, y_coord),
                            player_start_pos,
                            map_width,
                            map_height,
                            protected_coords=protected_coords,
                        )
                elif new_component_nodes:
                    node_from_new = self.random.choice(list(new_component_nodes))
                    node_from_main = self.random.choice(list(main_component_nodes))
                    path_finder.carve_bresenham_line(
                        world_map,
                        node_from_new,
                        node_from_main,
                        map_width,
                        map_height,
                        protected_coords=protected_coords,
                    )
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
        if start_pos == end_pos:
            tile = world_map.get_tile(start_pos[0], start_pos[1])
            return tile is not None and tile.type == "floor"

        queue = deque([start_pos])
        visited = {start_pos}
        start_tile = world_map.get_tile(start_pos[0], start_pos[1])
        if not start_tile or start_tile.type != "floor":
            return False

        while queue:
            curr_x, curr_y = queue.popleft()
            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                next_x, next_y = curr_x + dx, curr_y + dy
                if (next_x, next_y) == end_pos:
                    end_tile = world_map.get_tile(next_x, next_y)
                    return end_tile is not None and end_tile.type == "floor"
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
        reachable_tiles = set()
        queue = deque()
        visited = set()

        for start_node in start_nodes:
            if not (
                1 <= start_node[0] < map_width - 1
                and 1 <= start_node[1] < map_height - 1
            ):
                continue
            start_tile_obj = world_map.get_tile(start_node[0], start_node[1])
            if (
                start_tile_obj
                and start_tile_obj.type == "floor"
                and start_node not in visited
            ):
                queue.append(start_node)
                visited.add(start_node)
                reachable_tiles.add(start_node)

        while queue:
            curr_x, curr_y = queue.popleft()
            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                next_x, next_y = curr_x + dx, curr_y + dy
                if not (1 <= next_x < map_width - 1 and 1 <= next_y < map_height - 1):
                    continue
                if (next_x, next_y) not in visited:
                    tile = world_map.get_tile(next_x, next_y)
                    if tile and tile.type == "floor":
                        visited.add((next_x, next_y))
                        queue.append((next_x, next_y))
                        reachable_tiles.add((next_x, next_y))
        return reachable_tiles

    def path_exists_between(
        self,
        world_map: WorldMap,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        map_width: int,
        map_height: int,
    ) -> bool:
        """
        Checks if a path exists between start_pos and end_pos using A* search.
        """
        pathfinder = PathFinder()
        path = pathfinder.a_star_search(
            world_map, start_pos, end_pos, map_width, map_height
        )
        return path is not None and len(path) > 0
