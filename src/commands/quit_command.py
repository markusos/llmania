from typing import TYPE_CHECKING, Any, Dict

from .base_command import Command

if TYPE_CHECKING:
    # from src.player import Player # Not strictly needed
    # from src.world_map import WorldMap # Not strictly needed
    pass


class QuitCommand(Command):
    def execute(self) -> Dict[str, Any]:
        self.message_log.add_message("Quitting game.")
        return {"game_over": True}  # Quitting the game ends the game
