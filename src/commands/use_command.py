from typing import TYPE_CHECKING, Any, Dict

from .base_command import Command

if TYPE_CHECKING:
    pass


class UseCommand(Command):
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
