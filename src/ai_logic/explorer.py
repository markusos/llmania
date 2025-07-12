from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

from src.map_algorithms.pathfinding import PathFinder

if TYPE_CHECKING:
    from src.player import Player
    from src.world_map import WorldMap


class Explorer:
    def __init__(
        self,
        player: "Player",
        ai_visible_maps: Dict[int, "WorldMap"],
    ):
        self.player = player
        self.ai_visible_maps = ai_visible_maps
        self.path_finder = PathFinder()
        self.visited_portals: Set[Tuple[int, int, int]] = set()

    def mark_portal_as_visited(self, x: int, y: int, floor_id: int):
        self.visited_portals.add((x, y, floor_id))

    def find_unvisited_portals(
        self, player_pos_xy: Tuple[int, int], player_floor_id: int
    ) -> List[Tuple[int, int, int, str, int]]:
        targets = []
        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            for y, x in ai_map.iter_coords():
                tile = ai_map.get_tile(x, y)
                if (
                    tile
                    and tile.is_explored
                    and tile.is_portal
                    and (x, y, floor_id) not in self.visited_portals
                    and (x, y) != player_pos_xy
                ):
                    dist = (
                        abs(x - player_pos_xy[0])
                        + abs(y - player_pos_xy[1])
                        + abs(floor_id - player_floor_id) * 10
                    )
                    targets.append((x, y, floor_id, "unvisited_portal", dist))
        return targets

    def is_floor_fully_explored(self, floor_id: int) -> bool:
        ai_map = self.ai_visible_maps.get(floor_id)
        if not ai_map:
            return False  # Or True, depending on how we want to treat unknown maps
        for y, x in ai_map.iter_coords():
            tile = ai_map.get_tile(x, y)
            if tile and tile.type != "wall" and not tile.is_explored:
                return False
        return True

    def find_portal_to_unexplored_floor(
        self, player_pos_xy: Tuple[int, int], player_floor_id: int
    ) -> List[Tuple[int, int, int, str, int]]:
        targets = []
        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            for y, x in ai_map.iter_coords():
                tile = ai_map.get_tile(x, y)
                if tile and tile.is_explored and tile.is_portal:
                    portal_dest_floor_id = tile.portal_to_floor_id
                    if portal_dest_floor_id is not None:
                        if not self.is_floor_fully_explored(portal_dest_floor_id):
                            dist = (
                                abs(x - player_pos_xy[0])
                                + abs(y - player_pos_xy[1])
                                + abs(floor_id - player_floor_id) * 10
                            )
                            targets.append(
                                (x, y, floor_id, "portal_to_unexplored", dist)
                            )
        return targets

    def find_exploration_targets(
        self, player_pos_xy: Tuple[int, int], player_floor_id: int
    ) -> Optional[List[Tuple[int, int, int]]]:
        current_ai_map = self.ai_visible_maps.get(player_floor_id)
        if not current_ai_map:
            return None

        # Edge of known area on current floor
        edge_exploration_targets_current_floor: List[Tuple[int, int]] = []
        if current_ai_map:
            for y_edge in range(current_ai_map.height):
                for x_edge in range(current_ai_map.width):
                    tile = current_ai_map.get_tile(x_edge, y_edge)
                    if tile and tile.is_explored and tile.type != "wall":
                        for dx_adj, dy_adj in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                            adj_x, adj_y = x_edge + dx_adj, y_edge + dy_adj
                            adj_tile = current_ai_map.get_tile(adj_x, adj_y)
                            if adj_tile and not adj_tile.is_explored:
                                if (
                                    x_edge,
                                    y_edge,
                                ) not in edge_exploration_targets_current_floor:
                                    edge_exploration_targets_current_floor.append(
                                        (x_edge, y_edge)
                                    )
                                break
        if edge_exploration_targets_current_floor:
            paths_to_edge_frontiers = []
            for coord_xy in edge_exploration_targets_current_floor:
                if coord_xy == player_pos_xy:
                    continue
                path = self.path_finder.find_path_bfs(
                    self.ai_visible_maps,
                    player_pos_xy,
                    player_floor_id,
                    coord_xy,
                    player_floor_id,
                )
                if path:
                    paths_to_edge_frontiers.append(path)
            if paths_to_edge_frontiers:
                paths_to_edge_frontiers.sort(key=len)
                return paths_to_edge_frontiers[0]
        return None
