from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.world_map import WorldMap

if TYPE_CHECKING:
    from random import Random


class BuilderBase(ABC):
    def __init__(self, width: int, height: int, random_generator: "Random"):
        self.width = width
        self.height = height
        self.random = random_generator
        self.world_map = WorldMap(width, height)

    @abstractmethod
    def build(self):
        raise NotImplementedError
