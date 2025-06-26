# Type hinting imports
from typing import TYPE_CHECKING, Any, Dict, Type

# Local imports for command classes
from src.commands import (
    AttackCommand,
    Command,
    DropCommand,
    InventoryCommand,
    LookCommand,
    MoveCommand,
    QuitCommand,
    TakeCommand,
    UseCommand,
)

if TYPE_CHECKING:
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap


class CommandProcessor:
    """
    Handles the processing of parsed commands from the player by dispatching
    to appropriate command objects.
    """

    def __init__(self):
        """Initializes the CommandProcessor and registers available commands."""
        self._commands: Dict[str, Type[Command]] = {
            "move": MoveCommand,
            "take": TakeCommand,
            "drop": DropCommand,
            "use": UseCommand,
            "attack": AttackCommand,
            "inventory": InventoryCommand,
            "look": LookCommand,
            "quit": QuitCommand,
        }

    def process_command(
        self,
        parsed_command_tuple: tuple[str, str | None] | None,
        player: "Player",
        world_map: "WorldMap",
        message_log: "MessageLog",  # Changed from list[str] to MessageLog
        winning_position: tuple[int, int],
    ) -> Dict[str, Any]:  # Return type changed to match Command.execute()
        """
        Processes a parsed command tuple (verb, argument) using the Command pattern.

        Args:
            parsed_command_tuple: A tuple containing the command verb and its argument.
                                 Example: ("move", "north"), ("take", "potion").
            player: The Player instance.
            world_map: The WorldMap instance.
            message_log: The MessageLog instance.
            winning_position: The (x,y) tuple for the winning location.

        Returns:
            dict: A dictionary containing game state updates from the executed command,
                  typically {"game_over": bool}.
        """
        if parsed_command_tuple is None:
            message_log.add_message("Unknown command.")
            return {"game_over": False}

        verb, argument = parsed_command_tuple
        command_class = self._commands.get(verb.lower())

        if command_class:
            # Instantiate the command with all necessary context
            command_instance = command_class(
                player=player,
                world_map=world_map,
                message_log=message_log,
                winning_position=winning_position,
                argument=argument,
            )
            return command_instance.execute()
        else:
            message_log.add_message(f"Unknown command action: {verb}")
            return {"game_over": False}
