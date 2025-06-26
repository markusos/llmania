from typing import TYPE_CHECKING, Any, Dict

from .base_command import Command

if TYPE_CHECKING:
    pass
    # from src.item import Item # Item class might be used


class DropCommand(Command):
    def execute(self) -> Dict[str, Any]:
        if self.argument is None:
            self.message_log.add_message("Drop what?")
            return {"game_over": False}

        item_is_equipped_weapon = False
        if self.player.equipped_weapon and self.argument:
            if self.player.equipped_weapon.name.lower() == self.argument.lower():
                item_is_equipped_weapon = True

        dropped_item = self.player.drop_item(self.argument)

        if not dropped_item:
            self.message_log.add_message(f"You don't have a {self.argument} to drop.")
            return {"game_over": False}

        if item_is_equipped_weapon:
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
