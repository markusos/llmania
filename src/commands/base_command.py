from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from src.message_log import MessageLog
    from src.monster import Monster  # Added for _get_adjacent_monsters type hint
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
        winning_position: tuple[int, int],
        argument: Optional[str] = None,
    ):
        self.player = player
        self.world_map = world_map
        self.message_log = message_log
        self.winning_position = winning_position
        self.argument = argument

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Executes the command.

        Returns:
            A dictionary containing game state updates,
            specifically {"game_over": bool} and potentially others.
        """
        pass

    def _get_adjacent_monsters(
        self, x: int, y: int
    ) -> list[tuple["Monster", int, int]]:
        """
        Finds all monsters in tiles adjacent (N, S, E, W) to the given coordinates.
        """
        # Monster is imported locally in TYPE_CHECKING block or here if needed
        # at runtime.
        # from src.monster import Monster # Not needed here if only for type hint

        adjacent_monsters = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # N, S, W, E
            adj_x, adj_y = x + dx, y + dy
            tile = self.world_map.get_tile(adj_x, adj_y)
            if tile and tile.monster:
                adjacent_monsters.append((tile.monster, adj_x, adj_y))
        return adjacent_monsters
