from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.effects.healing_effect import HealingEffect
from src.items.consumable_item import ConsumableItem

from ..data_structures import Goal
from ..evaluator import Evaluator
from ..target_finder import TargetFinder

if TYPE_CHECKING:
    from src.game_engine import GameEngine


class SurvivalEvaluator(Evaluator):
    """
    This evaluator is responsible for the AI's survival. It will generate goals
    to use healing items or move towards them when health is low.
    """

    def __init__(self, weight: float = 2.5):  # Highest priority
        super().__init__(name="SurvivalEvaluator", weight=weight)
        self.target_finder: TargetFinder | None = None

    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        if self.target_finder is None:
            self.target_finder = TargetFinder(game_engine)

        goals: List[Goal] = []
        player = game_engine.player

        health_threshold = player.get_max_health() * 0.75
        if player.health >= health_threshold:
            return []

        health_percentage = player.health / player.get_max_health()
        urgency = 1.0 - health_percentage

        # Option 1: Use a healing item if available
        healing_items_in_inventory = [
            item
            for item in player.inventory.items
            if isinstance(item, ConsumableItem)
            and any(isinstance(e, HealingEffect) for e in item.effects)
        ]

        if healing_items_in_inventory:
            best_healing_item = max(
                healing_items_in_inventory,
                key=lambda item: max(
                    e.heal_amount for e in item.effects if isinstance(e, HealingEffect)
                ),
            )
            goals.append(
                Goal(
                    name="use_healing_item",
                    score=1.0,  # Always highest priority
                    context={"item": best_healing_item},
                )
            )
            return goals

        # Option 2: Find a healing item on the map
        healing_items_on_map = self.target_finder.find_health_potions()
        if healing_items_on_map:
            closest_potion = min(healing_items_on_map, key=lambda t: t[4])
            target_x, target_y, target_floor, _, dist = closest_potion
            score = urgency / (dist + 1)
            goals.append(
                Goal(
                    name="move_to_health_potion",
                    score=score,
                    context={"target_position": (target_x, target_y, target_floor)},
                )
            )

        return goals
