from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Set, Tuple

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
        self.visited_portals: Set[Tuple[int, int, int]] = set()

    def find_closest_unexplored_tile(
        self,
    ) -> Optional[Tuple[int, int, int]]:
        """
        Finds the closest unexplored tile on the current floor.
        """
        player_pos_xy = (self.player.x, self.player.y)
        player_floor_id = self.player.current_floor_id
        current_ai_map = self.ai_visible_maps.get(player_floor_id)

        if not current_ai_map:
            return None

        closest_tile = None
        min_dist = float("inf")

        for y in range(current_ai_map.height):
            for x in range(current_ai_map.width):
                tile = current_ai_map.get_tile(x, y)
                if tile and not tile.is_explored:
                    dist = abs(x - player_pos_xy[0]) + abs(y - player_pos_xy[1])
                    if dist < min_dist:
                        min_dist = dist
                        closest_tile = (x, y, player_floor_id)
        return closest_tile

    def find_closest_unvisited_portal(
        self,
    ) -> Optional[Tuple[int, int, int]]:
        """
        Finds the closest portal that has not been visited.
        """
        player_pos_xy = (self.player.x, self.player.y)
        player_floor_id = self.player.current_floor_id

        closest_portal = None
        min_dist = float("inf")

        for floor_id, ai_map in self.ai_visible_maps.items():
            if not ai_map:
                continue
            for y in range(ai_map.height):
                for x in range(ai_map.width):
                    tile = ai_map.get_tile(x, y)
                    if (
                        tile
                        and tile.is_portal
                        and (x, y, floor_id) not in self.visited_portals
                    ):
                        dist = (
                            abs(x - player_pos_xy[0])
                            + abs(y - player_pos_xy[1])
                            + abs(floor_id - player_floor_id) * 10
                        )  # Penalize distance on other floors
                        if dist < min_dist:
                            min_dist = dist
                            closest_portal = (x, y, floor_id)
        return closest_portal
