from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap
    # from src.item import Item


class InventoryCommand(Command):
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
        if not self.player.inventory:
            self.message_log.add_message("Your inventory is empty.")
        else:
            inventory_display = []
            for item_obj in self.player.inventory:
                display_name = item_obj.name
                if item_obj in self.player.equipment.values():
                    display_name += " (equipped)"
                inventory_display.append(display_name)
            self.message_log.add_message(f"Inventory: {', '.join(inventory_display)}")
        return {"game_over": False}  # Viewing inventory does not end the game
