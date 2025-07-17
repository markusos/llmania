from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap


class Command(ABC):
    """
    Abstract base class for all game commands.
    """

    def __init__(
        self,
        player: "Player",
        world_map: "WorldMap",
        message_log: "MessageLog",
        winning_position: tuple[int, int, int],
        argument: Optional[str] = None,
        world_maps: Optional[Dict[int, "WorldMap"]] = None,
        game_engine: Optional["GameEngine"] = None,
        entity: Optional[Union["Player", "Monster"]] = None,
    ):
        self.player = player
        self.world_map = world_map
        self.message_log = message_log
        self.winning_position = winning_position
        self.argument = argument
        self.world_maps = world_maps
        self.game_engine = game_engine
        self.entity = entity if entity is not None else player

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Executes the command.
        """
        pass

    def _get_monsters_in_range(
        self, x: int, y: int, range: int
    ) -> list[tuple["Monster", int, int]]:
        """
        Finds all monsters within a given range of the given coordinates.
        """
        monsters_in_range = []
        for monster in self.world_map.get_monsters():
            distance = monster.distance_to(x, y)
            if distance <= range:
                monsters_in_range.append((monster, monster.x, monster.y))
        return monsters_in_range
