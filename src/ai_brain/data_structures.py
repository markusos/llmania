from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    pass


@dataclass
class Action:
    """Represents a potential action the AI can take."""

    command: Tuple[str, Optional[str]]
    # The score will be calculated by the AIBrain based on evaluator inputs
    score: float = 0.0
    # The name of the evaluator that suggested this action
    evaluator_name: str = ""


@dataclass
class Goal:
    """Represents a high-level goal for the AI."""

    name: str
    # A score indicating the importance of this goal, determined by an evaluator
    score: float
    # Any additional data the action planner might need
    context: Dict[str, Any] = field(default_factory=dict)
