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
    from src.game_engine import GameEngine  # Added for game_engine reference
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
        world_maps: Dict[int, "WorldMap"],
        message_log: "MessageLog",
        winning_full_pos: tuple[int, int, int],
        game_engine: "GameEngine",
    ) -> Dict[str, Any]:
        """
        Processes a parsed command tuple.

        Args:
            parsed_command_tuple: Command verb and argument, e.g., ("move", "north").
            player: The Player instance.
            world_maps: All WorldMap instances, keyed by floor_id.
            message_log: The MessageLog instance.
            winning_full_pos: (x,y,floor_id) for the Amulet.
            game_engine: GameEngine instance for complex state changes (e.g. floor).

        Returns:
            Command execution results, typically {"game_over": bool}.
        """
        if parsed_command_tuple is None:
            message_log.add_message("Unknown command.")
            return {"game_over": False}

        verb, argument = parsed_command_tuple
        command_class = self._commands.get(verb.lower())

        if command_class:
            current_map = world_maps.get(player.current_floor_id)
            if not current_map:
                message_log.add_message(
                    f"Error: Floor {player.current_floor_id} not found."
                )
                return {"game_over": True}  # Critical error

            command_instance = command_class(
                player=player,
                world_map=current_map,  # Current floor's map
                message_log=message_log,
                winning_position=winning_full_pos,
                argument=argument,
                world_maps=world_maps,  # All maps for context
                game_engine=game_engine,
            )
            return command_instance.execute()
        else:
            message_log.add_message(f"Unknown command action: {verb}")
            return {"game_over": False}
