from abc import ABC, abstractmethod
from typing import Optional

from src.world_map import WorldMap


class BuilderBase(ABC):
    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed
        self.world_map = WorldMap(width, height)

    @abstractmethod
    def build(self) -> WorldMap:
        raise NotImplementedError
