"""
PickupItemAction - Take an item from the current tile.

This action mirrors the pickup logic from common_actions.pickup_item().
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class PickupItemAction(AIAction):
    """
    Take an item from the current tile.

    Utility Scores:
    - 0.99: Quest item on current tile (winning the game takes priority!)
    - 0.80: Regular item on current tile
    """

    @property
    def name(self) -> str:
        return "PickupItem"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available if there's an item on the current tile."""
        return ctx.current_tile_has_item and ctx.current_tile_item_name is not None

    def calculate_utility(self, ctx: "AIContext") -> float:
        """
        Calculate utility for picking up items.

        Quest items get very high priority (0.99) since picking them up
        can win the game - this should override fleeing behavior.
        """
        if not self.is_available(ctx):
            return 0.0

        # Quest items get top priority - picking them up can win the game!
        if ctx.current_tile_has_quest_item():
            return 0.99

        return 0.80

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute pickup by taking the item on current tile."""
        if ctx.current_tile_item_name:
            message_log.add_message(
                f"AI: Found item {ctx.current_tile_item_name} on current tile, "
                "taking it."
            )
            ai_logic.current_path = None
            return ("take", ctx.current_tile_item_name)
        return None
