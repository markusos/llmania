from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from .data_structures import Goal

if TYPE_CHECKING:
    # This avoids circular imports, which is a common issue in complex systems.
    from src.game_engine import GameEngine


class Evaluator(ABC):
    """Abstract base class for an AI behavior evaluator."""

    def __init__(self, name: str, weight: float = 1.0):
        """
        Initializes an evaluator with a name and a weight.
        The weight determines how influential this evaluator is in the AI's
        decision-making process.
        """
        self.name = name
        self.weight = weight

    @abstractmethod
    def evaluate(self, game_engine: "GameEngine") -> List[Goal]:
        """
        Evaluates the current game state and returns a list of goals.
        Each goal should have a score from 0.0 to 1.0, which will be
        multiplied by the evaluator's weight to determine its final priority.

        Args:
            game_engine: The main game engine instance, providing access to
                         the player, map, and other game components.

        Returns:
            A list of Goal objects, each representing a potential objective
            for the AI.
        """
        pass
