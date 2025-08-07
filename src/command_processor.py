from typing import TYPE_CHECKING, Any, Dict, Optional, Type, TypeAlias

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
from src.monster import Monster

# Define type aliases for better readability
WorldMaps: TypeAlias = Dict[int, "WorldMap"]


if TYPE_CHECKING:
    from src.game_engine import GameEngine  # Added for game_engine reference
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap

# Constants
DEFAULT_WINNING_POSITION = (0, 0, 0)


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
        parsed_command_tuple: Optional[tuple[str, Optional[str]]],
        player: "Player",
        world_maps: WorldMaps,
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

    def _initialize_command_instance(
        self,
        command_class: Type[Command],
        player: "Player",
        world_map: "WorldMap",
        message_log: "MessageLog",
        winning_position: tuple[int, int, int],
        argument: Optional[str],
        entity: Any = None,
        world_maps: Optional[WorldMaps] = None,
        game_engine: Optional["GameEngine"] = None,
    ) -> Command:
        """
        Helper method to initialize a command instance.

        Args:
            command_class: The command class to instantiate.
            player: The Player instance.
            world_map: The current WorldMap instance.
            message_log: The MessageLog instance.
            winning_position: The winning position tuple.
            argument: The argument for the command.
            entity: Optional entity (e.g., monster).
            world_maps: Optional dictionary of all WorldMaps.
            game_engine: Optional GameEngine instance.

        Returns:
            An instance of the command class.
        """
        return command_class(
            player=player,
            world_map=world_map,
            message_log=message_log,
            winning_position=winning_position,
            argument=argument,
            entity=entity,
            world_maps=world_maps,
            game_engine=game_engine,
        )

    def process_monster_command(
        self,
        parsed_command_tuple: Optional[tuple[str, Optional[str]]],
        monster: "Monster",
        player: "Player",
        world_maps: WorldMaps,
        message_log: "MessageLog",
    ) -> Dict[str, Any]:
        """
        Processes a parsed command tuple for a monster.

        Args:
            parsed_command_tuple: Command verb and argument, e.g., ("move", "north").
            monster: The Monster instance.
            player: The Player instance.
            world_maps: All WorldMap instances, keyed by floor_id.
            message_log: The MessageLog instance.

        Returns:
            Command execution results, typically an empty dictionary or specific
            results.
        """
        if parsed_command_tuple is None:
            message_log.add_message("Monster command is None.")
            return {}

        verb, argument = parsed_command_tuple
        command_class = self._commands.get(verb.lower())

        if command_class:
            current_map = world_maps.get(player.current_floor_id)
            if not current_map:
                message_log.add_message(
                    f"Error: Floor {player.current_floor_id} not found for monster."
                )
                return {}

            command_instance = self._initialize_command_instance(
                command_class=command_class,
                player=player,
                world_map=current_map,
                message_log=message_log,
                winning_position=DEFAULT_WINNING_POSITION,
                argument=argument,
                entity=monster,
            )
            return command_instance.execute()
        else:
            message_log.add_message(f"Unknown monster command action: {verb}")
            return {}
