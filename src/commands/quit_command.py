from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap


class QuitCommand(Command):
    def __init__(
        self,
        player: "Player",
        world_map: "WorldMap",
        message_log: "MessageLog",
        winning_position: tuple[int, int, int],
        argument: Optional[str] = None,
        world_maps: Optional[Dict[int, "WorldMap"]] = None,
        game_engine: Optional["GameEngine"] = None,
    ):
        super().__init__(
            player,
            world_map,
            message_log,
            winning_position,
            argument,
            world_maps,
            game_engine,
        )

    def execute(self) -> Dict[str, Any]:
        self.message_log.add_message("Quitting game.")
        if self.game_engine:
            self.game_engine.game_state = self.game_engine.game_state.QUIT
        return {"game_over": True}
