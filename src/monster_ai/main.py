from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder
from src.monster_ai.states.attacking_state import AttackingState
from src.monster_ai.states.idle_state import IdleState

if TYPE_CHECKING:
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap

    from .states.base_state import AIState


class MonsterAILogic:
    def __init__(
        self,
        monster: "Monster",
        player: "Player",
        world_map: "WorldMap",
        random_generator: "random.Random",
    ):
        self.monster = monster
        self.player = player
        self.world_map = world_map
        self.random = random_generator
        self.path_finder = PathFinder()
        self.state: "AIState" = IdleState(self)

    def _get_state(self, state_name: str) -> "AIState":
        if state_name == "IdleState":
            return IdleState(self)
        elif state_name == "AttackingState":
            return AttackingState(self)
        else:
            raise ValueError(f"Unknown state name: {state_name}")

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        next_state_name = self.state.handle_transitions()
        if next_state_name != self.state.__class__.__name__:
            self.state = self._get_state(next_state_name)
        return self.state.get_next_action()

    def _get_line_tiles(
        self, x1: int, y1: int, x2: int, y2: int
    ) -> List[Tuple[int, int]]:
        """
        Get all tiles along a line from (x1, y1) to (x2, y2) using Bresenham's
        line algorithm. Returns list of (x, y) coordinates excluding the start point.
        """
        tiles = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        if dx > dy:
            err = dx // 2
            while x != x2:
                x += sx
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                tiles.append((x, y))
        else:
            err = dy // 2
            while y != y2:
                y += sy
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                tiles.append((x, y))

        return tiles

    def _has_clear_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """
        Check if there is a clear line of sight between two points.
        Returns True if no walls block the view, False otherwise.
        """
        line_tiles = self._get_line_tiles(x1, y1, x2, y2)

        # Check all tiles except the final destination
        for x, y in line_tiles[:-1] if line_tiles else []:
            tile = self.world_map.get_tile(x, y)
            if tile is None or tile.type == "wall":
                return False

        return True

    def is_player_in_line_of_sight(self) -> bool:
        """
        Check if the player is within the monster's line of sight range
        AND there are no walls blocking the view.
        """
        distance = self.monster.distance_to(self.player.x, self.player.y)
        if distance > self.monster.line_of_sight:
            return False

        return self._has_clear_line_of_sight(
            self.monster.x, self.monster.y, self.player.x, self.player.y
        )

    def is_player_in_attack_range(self) -> bool:
        """
        Check if the player is within the monster's attack range
        AND there are no walls blocking the attack (for ranged attacks).
        """
        distance = self.monster.distance_to(self.player.x, self.player.y)
        if distance > self.monster.attack_range:
            return False

        # For melee attacks (range 1), no LOS check needed beyond adjacency
        if self.monster.attack_range <= 1:
            return True

        # For ranged attacks, ensure clear line of sight
        return self._has_clear_line_of_sight(
            self.monster.x, self.monster.y, self.player.x, self.player.y
        )

    def move_towards_player(self) -> Optional[Tuple[str, Optional[str]]]:
        path = self.path_finder.a_star_search(
            self.world_map,
            (self.monster.x, self.monster.y),
            (self.player.x, self.player.y),
            self.world_map.width,
            self.world_map.height,
        )
        if path and len(path) > 1:
            next_x, next_y = path[1]
            dx = next_x - self.monster.x
            dy = next_y - self.monster.y
            if dx == 0 and dy == -1:
                return "move", "north"
            if dx == 0 and dy == 1:
                return "move", "south"
            if dx == -1 and dy == 0:
                return "move", "west"
            if dx == 1 and dy == 0:
                return "move", "east"
        return None
