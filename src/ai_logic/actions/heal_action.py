"""
HealAction - Use a healing item when health is low.

This action mirrors the healing logic from SurvivalState and
should_heal_before_combat() in the FSM system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class HealAction(AIAction):
    """
    Use a healing item when health is low.

    Utility Scores:
    - 1.00: health ≤ survival_threshold (critical survival need)
    - 0.98: adjacent monster and health ≤ incoming_damage * 1.5
    - 0.96: adjacent monster, health ≤ 50%, facing danger ≥ 3 monster
    - 0.00: healthy or no healing available
    """

    @property
    def name(self) -> str:
        return "Heal"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available if we have healing items and health is not full."""
        return ctx.has_healing_item and ctx.player_health < ctx.player_max_health

    def calculate_utility(self, ctx: "AIContext") -> float:
        """
        Calculate utility based on health status and combat situation.

        Matches FSM priority:
        - Highest when health below survival threshold
        - High in combat when health is risky
        - Zero otherwise
        """
        if not self.is_available(ctx):
            return 0.0

        # Critical: Health at or below survival threshold
        if ctx.health_ratio <= ctx.survival_threshold:
            return 1.0

        # Pre-combat healing logic (from should_heal_before_combat)
        if ctx.adjacent_monsters and ctx.bestiary:
            # Don't heal if already at high health
            if ctx.health_ratio >= 0.8:
                return 0.0

            # Get max incoming damage from adjacent monsters
            max_incoming_damage = max(
                ctx.bestiary.get_attack_power(m.name) for m in ctx.adjacent_monsters
            )

            # Heal if a single attack could put us in critical danger
            if ctx.player_health <= max_incoming_damage * 1.5:
                return 0.98

            # Heal if we're below 50% and facing dangerous monsters
            if ctx.health_ratio <= 0.5:
                max_danger = max(
                    ctx.bestiary.get_danger_rating(m.name)
                    for m in ctx.adjacent_monsters
                )
                if max_danger >= 3:
                    return 0.96

        return 0.0

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute healing by using the first available healing item."""
        for item in ctx.inventory_items:
            if item.properties.get("type") == "heal":
                message_log.add_message(f"AI: Using {item.name}.")
                return ("use", item.name)
        return None
