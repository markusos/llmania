from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap
    # from src.item import Item


class DropCommand(Command):
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
            self.message_log.add_message("Drop what?")
            return {"game_over": False}

        item_is_equipped = (
            self.player.equipment.slots["main_hand"] is not None
            and self.player.equipment.slots["main_hand"].name.lower() == self.argument.lower()
        ) or (
            self.player.equipment.slots["off_hand"] is not None
            and self.player.equipment.slots["off_hand"].name.lower() == self.argument.lower()
        )

        dropped_item = self.player.drop_item(self.argument)

        if not dropped_item:
            self.message_log.add_message(f"You don't have a {self.argument} to drop.")
            return {"game_over": False}

        if item_is_equipped:
            self.message_log.add_message(f"You unequip the {dropped_item.name}.")

        tile = self.world_map.get_tile(self.player.x, self.player.y)
        if tile and tile.item is None:
            self.world_map.place_item(dropped_item, self.player.x, self.player.y)
            self.message_log.add_message(f"You drop the {dropped_item.name}.")
        else:
            self.player.take_item(dropped_item)  # Player takes it back
            self.message_log.add_message(
                f"You can't drop {dropped_item.name} here, space occupied."
            )
        return {"game_over": False}
