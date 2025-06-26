from typing import TYPE_CHECKING, Any, Dict

from .base_command import Command

if TYPE_CHECKING:
    # from src.world_map import WorldMap # Not strictly needed
    pass
    # from src.item import Item # Item class might be used if checking item properties


class InventoryCommand(Command):
    def execute(self) -> Dict[str, Any]:
        if not self.player.inventory:
            self.message_log.add_message("Your inventory is empty.")
        else:
            inventory_display = []
            for item_obj in self.player.inventory:
                display_name = item_obj.name
                if self.player.equipped_weapon == item_obj:
                    display_name += " (equipped)"
                inventory_display.append(display_name)
            self.message_log.add_message(f"Inventory: {', '.join(inventory_display)}")
        return {"game_over": False}  # Viewing inventory does not end the game
