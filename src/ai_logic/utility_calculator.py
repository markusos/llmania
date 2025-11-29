"""
UtilityCalculator - Selects and executes the highest-utility available action.

This is the core decision-making component of the Utility-Based AI system.
It evaluates all available actions, calculates their utility scores,
and selects the best one to execute.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from src.ai_logic.actions.base_action import AIAction
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class UtilityCalculator:
    """
    Selects and executes the highest-utility available action.

    This class maintains a list of all possible actions and provides
    methods to select and execute the best one based on the current
    game state (AIContext).
    """

    def __init__(self, actions: List["AIAction"]):
        """
        Initialize with a list of all available actions.

        Args:
            actions: List of AIAction instances to consider for selection.
        """
        self.actions = actions

    def select_action(self, ctx: "AIContext") -> Optional["AIAction"]:
        """
        Return the highest-utility available action.

        Filters actions by availability, then selects the one with
        the highest utility score. If utilities tie, actions are
        sorted by name for determinism.

        Args:
            ctx: The current game state context.

        Returns:
            The best AIAction to execute, or None if no actions available.
        """
        available = [
            (action, action.calculate_utility(ctx))
            for action in self.actions
            if action.is_available(ctx)
        ]

        if not available:
            return None

        # Sort by utility descending, then by name for determinism
        available.sort(key=lambda x: (-x[1], x[0].name))

        # Return the action with highest utility (if utility > 0)
        best_action, best_utility = available[0]
        if best_utility <= 0:
            return None

        return best_action

    def get_action_scores(self, ctx: "AIContext") -> List[Tuple[str, float, bool]]:
        """
        Return (name, utility, available) for all actions.

        Useful for debugging and logging decision-making.

        Args:
            ctx: The current game state context.

        Returns:
            List of tuples containing action name, utility score, and availability.
        """
        return [
            (action.name, action.calculate_utility(ctx), action.is_available(ctx))
            for action in self.actions
        ]

    def execute_best_action(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """
        Select and execute the best action.

        Combines select_action and execute into a single method for convenience.
        If the best action returns None (e.g., path not found), tries the next
        best action until one succeeds or all are exhausted.

        Args:
            ctx: The current game state context.
            ai_logic: The AILogic instance for action side effects.
            message_log: The message log for action logging.

        Returns:
            The command tuple from the executed action, or None.
        """
        # Get all available actions sorted by utility
        available = [
            (action, action.calculate_utility(ctx))
            for action in self.actions
            if action.is_available(ctx)
        ]

        if not available:
            return None

        # Sort by utility descending, then by name for determinism
        available.sort(key=lambda x: (-x[1], x[0].name))

        # Try each action in order until one succeeds
        for action, utility in available:
            if utility <= 0:
                break
            result = action.execute(ctx, ai_logic, message_log)
            if result is not None:
                return result

        return None


def create_default_utility_calculator() -> UtilityCalculator:
    """
    Create a UtilityCalculator with all default actions.

    This factory function creates a calculator with the standard
    set of actions used by the AI.

    Returns:
        A UtilityCalculator instance with all default actions.
    """
    from src.ai_logic.actions import (
        AttackAction,
        EquipAction,
        ExploreAction,
        FleeAction,
        HealAction,
        PathToArmorAction,
        PathToHealthAction,
        PathToLootAction,
        PathToPortalAction,
        PathToQuestAction,
        PathToWeaponAction,
        PickupItemAction,
        RandomMoveAction,
        UseCombatItemAction,
    )

    actions = [
        HealAction(),
        FleeAction(),
        UseCombatItemAction(),
        AttackAction(),
        PickupItemAction(),
        EquipAction(),
        PathToHealthAction(),
        PathToWeaponAction(),
        PathToArmorAction(),
        PathToQuestAction(),
        PathToPortalAction(),
        PathToLootAction(),
        ExploreAction(),
        RandomMoveAction(),
    ]

    return UtilityCalculator(actions)
