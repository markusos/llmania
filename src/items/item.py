from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class Item(ABC):
    """
    Abstract base class for items.
    """

    def __init__(self, name: str, description: str, properties: dict):
        self.name = name
        self.description = description
        self.properties = properties

    @abstractmethod
    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        raise NotImplementedError()
