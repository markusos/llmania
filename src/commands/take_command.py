from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap
    # from src.item import Item


class TakeCommand(Command):
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
        # self.world_map refers to the current floor's map
        tile = self.world_map.get_tile(self.player.x, self.player.y)
        if not (tile and tile.item):
            item_name_msg = self.argument if self.argument else "item"
            self.message_log.add_message(f"There is no {item_name_msg} here to take.")
            return {"game_over": False}

        item_to_take = tile.item
        if self.argument and item_to_take.name.lower() != self.argument.lower():
            self.message_log.add_message(f"There is no {self.argument} here to take.")
            return {"game_over": False}

        if item_to_take.properties.get("type") == "quest":
            removed_item = self.world_map.remove_item(self.player.x, self.player.y)
            if removed_item:
                self.player.take_item(removed_item)
                if removed_item.name == "Amulet of Yendor":
                    self.message_log.add_message(
                        "You picked up the Amulet of Yendor! You win!"
                    )
                else:
                    self.message_log.add_message(
                        f"You picked up the {removed_item.name}! You win!"
                    )
                return {"game_over": True}
            else:
                self.message_log.add_message(
                    f"Error: Failed to remove quest item {item_to_take.name} from map."
                )
                return {"game_over": False}

        removed_item = self.world_map.remove_item(self.player.x, self.player.y)
        if removed_item:
            self.player.take_item(removed_item)
            self.message_log.add_message(f"You take the {removed_item.name}.")
            return {"game_over": False}

        self.message_log.add_message(f"Could not remove {item_to_take.name} from map.")
        return {"game_over": False}
