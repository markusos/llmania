"""
Base class for AI actions in the Utility-Based AI system.

Actions are stateless calculators that:
1. Check if they can execute given current context
2. Calculate a utility score (0.0 to 1.0)
3. Execute and return a command tuple
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class AIAction(ABC):
    """
    Base class for all AI actions.

    Actions are stateless calculators that:
    1. Check if they can execute given current context
    2. Calculate a utility score (0.0 to 1.0)
    3. Execute and return a command tuple

    IMPORTANT: Actions must NOT modify AIContext. They receive
    a mutable AILogic reference only in execute() for side effects
    like clearing paths or logging messages.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for debugging/logging."""
        pass

    @abstractmethod
    def is_available(self, ctx: "AIContext") -> bool:
        """
        Return True if this action can be executed in current state.

        This is a fast check - do expensive calculations in calculate_utility.
        """
        pass

    @abstractmethod
    def calculate_utility(self, ctx: "AIContext") -> float:
        """
        Return utility score between 0.0 and 1.0.

        Higher scores = more desirable actions.
        Return 0.0 if action should not be taken.

        MUST be deterministic given the same context.
        """
        pass

    @abstractmethod
    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """
        Execute the action and return command tuple.

        May modify ai_logic state (e.g., clear current_path).
        Must log actions via message_log.

        Returns: ("command", "argument") or ("command", None) or None
        """
        pass
