from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from src.game_engine import GameEngine  # Added
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
        world_map: "WorldMap",  # Represents the current floor's map
        message_log: "MessageLog",
        winning_position: tuple[int, int, int],  # Now (x, y, floor_id)
        argument: Optional[str] = None,
        world_maps: Optional[Dict[int, "WorldMap"]] = None,  # All floor maps
        game_engine: Optional["GameEngine"] = None,  # Reference to game engine
    ):
        self.player = player
        self.world_map = world_map  # Current floor's map
        self.message_log = message_log
        self.winning_position = winning_position  # (x,y,floor_id)
        self.argument = argument
        self.world_maps = world_maps  # All maps, needed for cross-floor actions
        self.game_engine = (
            game_engine  # For complex state changes like floor transition
        )

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
