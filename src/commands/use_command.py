from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap


class UseCommand(Command):
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
        if self.argument is None:
            self.message_log.add_message("Use what?")
            return {"game_over": False}

        use_message = self.player.use_item(self.argument)
        self.message_log.add_message(use_message)

        # Check if using the item resulted in player's death
        if "cursed!" in use_message.lower() and self.player.health <= 0:
            # Game over message might be part of use_message or player.die()
            # For now, simply returning True for game_over is sufficient
            return {"game_over": True}
        return {"game_over": False}
