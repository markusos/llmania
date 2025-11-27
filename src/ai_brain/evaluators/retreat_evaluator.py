from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..data_structures import Goal
from ..evaluator import Evaluator
from ..target_finder import TargetFinder

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class RetreatEvaluator(Evaluator):
    """
    This evaluator encourages the AI to retreat from dangerous situations.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="RetreatEvaluator", weight=weight)
        self.target_finder: TargetFinder | None = None
        self.last_health: int = -1
        self.took_damage_last_turn = False

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        if self.target_finder is None:
            self.target_finder = TargetFinder(game_engine)

        goals: List[Goal] = []
        player = game_engine.player
        health_ratio = player.health / player.get_max_health()

        if self.last_health == -1:
            self.last_health = player.health

        self.took_damage_last_turn = player.health < self.last_health
        self.last_health = player.health

        retreat_threshold = 0.6  # Retreat if health is below 60%
        monster_nearby_and_low_health = False

        monsters = self.target_finder.find_monsters()
        if monsters:
            closest_monster_data = min(monsters, key=lambda m: m[4])
            dist = closest_monster_data[4]
            if dist <= 5 and health_ratio < retreat_threshold:
                monster_nearby_and_low_health = True

        # If we took damage last turn, or a monster is nearby and we're low on health
        if self.took_damage_last_turn or monster_nearby_and_low_health:
            safe_spot = self._find_safe_spot(game_engine)
            if safe_spot:
                score = (1.0 - health_ratio)  # The lower the health, the higher the score
                goals.append(
                    Goal(
                        name="retreat",
                        score=score,
                        context={"target_position": safe_spot},
                    )
                )
        return goals

    def _find_safe_spot(self, game_engine: "GameEngine") -> tuple[int, int, int] | None:
        """
        Finds a safe spot to retreat to, away from any monsters.
        A safe spot is a walkable tile that is not "close" to any known monster.
        """
        player = game_engine.player
        visible_map = game_engine.visible_maps[player.current_floor_id]
        monsters = self.target_finder.find_monsters()

        def is_safe(x: int, y: int, min_dist: int) -> bool:
            if (x, y) == (player.x, player.y):
                return False
            if not visible_map.is_valid_move(x, y):
                return False
            if monsters:
                for monster_x, monster_y, _, _, _ in monsters:
                    if abs(x - monster_x) + abs(y - monster_y) < min_dist:
                        return False
            return True

        safe_spots = []
        for y in range(visible_map.height):
            for x in range(visible_map.width):
                if is_safe(x, y, 10):
                    dist_to_player = abs(x - player.x) + abs(y - player.y)
                    safe_spots.append(((x, y, player.current_floor_id), dist_to_player))

        if not safe_spots:
            for y in range(visible_map.height):
                for x in range(visible_map.width):
                    if is_safe(x, y, 2):
                        dist_to_player = abs(x - player.x) + abs(y - player.y)
                        safe_spots.append(((x, y, player.current_floor_id), dist_to_player))

        if not safe_spots:
            return None

        safe_spots.sort(key=lambda s: s[1])
        return safe_spots[0][0]
