from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from src.actions.move import move as move_action

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap


class MoveCommand(Command):
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
        super().__init__(
            player,
            world_map,
            message_log,
            winning_position,
            argument,
            world_maps,
            game_engine,
            entity,
        )

    def execute(self) -> Dict[str, Any]:
        return move_action(
            entity=self.entity,
            world_map=self.world_map,
            message_log=self.message_log,
            winning_position=self.winning_position,
            argument=self.argument,
            world_maps=self.world_maps,
            game_engine=self.game_engine,
        )
