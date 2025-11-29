"""
ExploreAction - Explore unexplored areas of the map.

This action uses the Explorer to find exploration frontiers
and paths to them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class ExploreAction(AIAction):
    """
    Explore unexplored areas of the map.

    Utility Score: 0.30 (constant when unexplored tiles exist)
    """

    @property
    def name(self) -> str:
        return "Explore"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available when there are unexplored tiles reachable."""
        if not ctx.explorer:
            return False

        exploration_path = ctx.explorer.find_exploration_targets(
            ctx.player_pos, ctx.player_floor_id
        )
        return exploration_path is not None and len(exploration_path) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """
        Calculate utility for exploration.

        Higher utility (0.50) when exploring leads to a different floor (via portal).
        Standard utility (0.35) for same-floor exploration.
        """
        if not self.is_available(ctx):
            return 0.0

        if not ctx.explorer:
            return 0.35

        exploration_path = ctx.explorer.find_exploration_targets(
            ctx.player_pos, ctx.player_floor_id
        )

        if not exploration_path:
            return 0.0

        # Check if the exploration path involves going to a different floor
        # This indicates cross-floor exploration via portal
        target_floor = (
            exploration_path[-1][2] if exploration_path else ctx.player_floor_id
        )
        if target_floor != ctx.player_floor_id:
            return 0.50  # Higher priority for cross-floor exploration

        return 0.35  # Standard exploration priority

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Execute by pathing to the nearest exploration frontier."""
        if not ctx.explorer:
            return None

        exploration_path = ctx.explorer.find_exploration_targets(
            ctx.player_pos, ctx.player_floor_id
        )

        if not exploration_path:
            return None

        ai_logic.current_path = exploration_path
        target_coord = exploration_path[-1]
        message_log.add_message(
            f"AI: Pathing to explore at ({target_coord[0]},{target_coord[1]}) "
            f"on floor {target_coord[2]}."
        )

        return self._follow_current_path(ctx, ai_logic, message_log)

    def _follow_current_path(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Follow the current path if it exists."""
        if not ai_logic.current_path:
            return None

        current_pos_xyz = ctx.player_pos_3d

        # Skip current position if we're already there
        if ai_logic.current_path[0] == current_pos_xyz:
            ai_logic.current_path.pop(0)

        if not ai_logic.current_path:
            ai_logic.current_path = None
            return None

        next_step_xyz = ai_logic.current_path[0]
        move_command = ai_logic._coordinates_to_move_command(
            (current_pos_xyz[0], current_pos_xyz[1]),
            (next_step_xyz[0], next_step_xyz[1]),
        )

        if move_command:
            log_msg = (
                f"AI: Following path. Moving {move_command[1]} to "
                f"({next_step_xyz[0]},{next_step_xyz[1]}) on floor "
                f"{next_step_xyz[2]}."
            )
            message_log.add_message(log_msg)
            ai_logic.last_move_command = move_command
            return move_command

        return None
