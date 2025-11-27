from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Set, Tuple

from src.map_algorithms.pathfinding import PathFinder

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class Explorer:
    """
    Handles the AI's exploration behavior, including finding unexplored areas
    and unvisited portals.
    """

    def __init__(self, game_engine: "GameEngine"):
        self.game_engine = game_engine
        self.player = game_engine.player
        self.ai_visible_maps = game_engine.visible_maps
        self.path_finder = PathFinder()
        self.visited_portals: Set[Tuple[int, int, int]] = set()

    def mark_portal_as_visited(self, x: int, y: int, floor_id: int):
        """
        Marks a portal as visited to avoid redundant exploration.
        """
        self.visited_portals.add((x, y, floor_id))

    def find_unvisited_portals(self) -> List[Tuple[int, int, int, str, int]]:
        """
        Finds portals that the AI has not yet traveled through.
        """
        targets = []
        player_pos_xy = (self.player.x, self.player.y)
        player_floor_id = self.player.current_floor_id

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

    def find_exploration_targets(
        self,
    ) -> Optional[List[Tuple[int, int, int]]]:
        """
        Identifies the most promising frontier for exploration.
        """
        player_pos_xy = (self.player.x, self.player.y)
        player_floor_id = self.player.current_floor_id
        current_ai_map = self.ai_visible_maps.get(player_floor_id)
        if not current_ai_map:
            return None

        # Find edge of known area on the current floor
        edge_targets = []
        for y, x in current_ai_map.iter_coords():
            tile = current_ai_map.get_tile(x, y)
            if tile and tile.is_explored and tile.type != "wall":
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    adj_x, adj_y = x + dx, y + dy
                    adj_tile = current_ai_map.get_tile(adj_x, adj_y)
                    if adj_tile and not adj_tile.is_explored:
                        if (x, y) not in edge_targets:
                            edge_targets.append((x, y))
                        break

        if not edge_targets:
            return None

        # Find the shortest path to an edge
        paths_to_frontiers = []
        for target_xy in edge_targets:
            if target_xy == player_pos_xy:
                continue
            path = self.path_finder.find_path_bfs(
                self.ai_visible_maps,
                player_pos_xy,
                player_floor_id,
                target_xy,
                player_floor_id,
            )
            if path:
                paths_to_frontiers.append(path)

        if paths_to_frontiers:
            paths_to_frontiers.sort(key=len)
            return paths_to_frontiers[0]

        return None
