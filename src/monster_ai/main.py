from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional, Tuple

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

    def is_player_in_line_of_sight(self) -> bool:
        distance = self.monster.distance_to(self.player.x, self.player.y)
        return distance <= self.monster.line_of_sight

    def is_player_in_attack_range(self) -> bool:
        distance = self.monster.distance_to(self.player.x, self.player.y)
        return distance <= self.monster.attack_range

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
