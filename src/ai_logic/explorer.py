from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

from src.map_algorithms.pathfinding import PathFinder

if TYPE_CHECKING:
    from src.world_map import WorldMap

    from .ai_player_view import AIPlayerView


class Explorer:
    def __init__(
        self,
        player_view: "AIPlayerView",
        ai_visible_maps: Dict[int, "WorldMap"],
    ):
        self.player_view = player_view
        self.ai_visible_maps = ai_visible_maps
        self.path_finder = PathFinder()
        self.visited_portals: Set[Tuple[int, int, int]] = set()

    def mark_portal_as_visited(self, x: int, y: int, floor_id: int):
        """Mark a portal as visited, including both ends of the portal."""
        self.visited_portals.add((x, y, floor_id))
        # Also mark the destination portal as visited to prevent ping-pong
        ai_map = self.ai_visible_maps.get(floor_id)
        if ai_map:
            tile = ai_map.get_tile(x, y)
            if tile and tile.is_portal and tile.portal_to_floor_id is not None:
                # The destination portal is at the same (x, y) on the other floor
                self.visited_portals.add((x, y, tile.portal_to_floor_id))

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

    def get_floor_exploration_ratio(self, floor_id: int) -> float:
        """Return the ratio of explored non-wall tiles on a floor (0.0 to 1.0)."""
        ai_map = self.ai_visible_maps.get(floor_id)
        if not ai_map:
            return 0.0
        explored_count = 0
        total_count = 0
        for y, x in ai_map.iter_coords():
            tile = ai_map.get_tile(x, y)
            if tile and tile.type != "wall":
                total_count += 1
                if tile.is_explored:
                    explored_count += 1
        if total_count == 0:
            return 1.0
        return explored_count / total_count

    def find_portal_to_unexplored_floor(
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
                    and not (x == player_pos_xy[0] and y == player_pos_xy[1])
                    and (x, y, floor_id) not in self.visited_portals
                ):
                    portal_dest_floor_id = tile.portal_to_floor_id
                    if (
                        portal_dest_floor_id is not None
                        and not self.is_floor_fully_explored(portal_dest_floor_id)
                    ):
                        dist = (
                            abs(x - player_pos_xy[0])
                            + abs(y - player_pos_xy[1])
                            + abs(floor_id - player_floor_id) * 10
                        )
                        targets.append((x, y, floor_id, "portal_to_unexplored", dist))
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
                    require_explored=True,
                )
                if path:
                    paths_to_edge_frontiers.append(path)
            if paths_to_edge_frontiers:
                paths_to_edge_frontiers.sort(key=len)
                return paths_to_edge_frontiers[0]

        # Current floor fully explored - find a portal to an unexplored floor
        portals_to_unexplored = self.find_portal_to_unexplored_floor(
            player_pos_xy, player_floor_id
        )
        if portals_to_unexplored:
            # Sort by distance and get closest portal
            portals_to_unexplored.sort(key=lambda t: t[4])  # Sort by dist
            for portal_x, portal_y, portal_floor, _, _ in portals_to_unexplored:
                path = self.path_finder.find_path_bfs(
                    self.ai_visible_maps,
                    player_pos_xy,
                    player_floor_id,
                    (portal_x, portal_y),
                    portal_floor,
                    require_explored=True,
                )
                if path:
                    return path

        # Also try unvisited portals as a fallback
        unvisited_portals = self.find_unvisited_portals(player_pos_xy, player_floor_id)
        if unvisited_portals:
            unvisited_portals.sort(key=lambda t: t[4])  # Sort by dist
            for portal_x, portal_y, portal_floor, _, _ in unvisited_portals:
                path = self.path_finder.find_path_bfs(
                    self.ai_visible_maps,
                    player_pos_xy,
                    player_floor_id,
                    (portal_x, portal_y),
                    portal_floor,
                    require_explored=True,
                )
                if path:
                    return path

        return None
