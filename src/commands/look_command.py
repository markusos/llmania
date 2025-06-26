from typing import TYPE_CHECKING, Any, Dict

from .base_command import Command

if TYPE_CHECKING:
    pass  # For type hint from _get_adjacent_monsters
    # from src.item import Item # For type hint from tile.item


class LookCommand(Command):
    def execute(self) -> Dict[str, Any]:
        self.message_log.add_message(f"You are at ({self.player.x}, {self.player.y}).")

        current_tile = self.world_map.get_tile(self.player.x, self.player.y)
        item_seen_on_tile = False
        monster_on_tile = False  # Initialized
        if current_tile:
            if current_tile.item:
                self.message_log.add_message(
                    f"You see a {current_tile.item.name} here."
                )
                item_seen_on_tile = True
            if current_tile.monster:
                self.message_log.add_message(
                    f"There is a {current_tile.monster.name} here!"
                )
                monster_on_tile = True

        # _get_adjacent_monsters is inherited from Command base class
        adj_monsters = self._get_adjacent_monsters(self.player.x, self.player.y)
        adj_monster_seen = False
        if adj_monsters:
            for monster, mx, my in adj_monsters:  # monster here is Monster instance
                self.message_log.add_message(
                    f"You see a {monster.name} at ({mx}, {my})."
                )
                adj_monster_seen = True

        is_area_clear = (
            not item_seen_on_tile and not adj_monster_seen and not monster_on_tile
        )
        if is_area_clear:
            self.message_log.add_message("The area is clear.")
        return {"game_over": False}  # Looking around does not end the game
