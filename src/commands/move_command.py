from typing import TYPE_CHECKING, Any, Dict

from .base_command import Command

if TYPE_CHECKING:
    pass


class MoveCommand(Command):
    def execute(self) -> Dict[str, Any]:
        current_game_over_state = False
        dx, dy = 0, 0
        if self.argument == "north":
            dy = -1
        elif self.argument == "south":
            dy = 1
        elif self.argument == "east":
            dx = 1
        elif self.argument == "west":
            dx = -1
        else:
            self.message_log.add_message(f"Unknown direction: {self.argument}")
            return {"game_over": current_game_over_state}

        new_x, new_y = self.player.x + dx, self.player.y + dy
        if self.world_map.is_valid_move(new_x, new_y):
            target_tile = self.world_map.get_tile(new_x, new_y)
            if target_tile and target_tile.monster:
                msg = f"You bump into a {target_tile.monster.name}!"
                self.message_log.add_message(msg)
            else:
                self.player.move(dx, dy)
                self.message_log.add_message(f"You move {self.argument}.")
                if (self.player.x, self.player.y) == self.winning_position:
                    win_tile = self.world_map.get_tile(
                        self.winning_position[0], self.winning_position[1]
                    )
                    if (
                        win_tile
                        and win_tile.item
                        and win_tile.item.properties.get("type") == "quest"
                    ):
                        self.message_log.add_message(
                            "You reached the Amulet of Yendor's location!"
                        )
        else:
            self.message_log.add_message("You can't move there.")
        return {"game_over": current_game_over_state}
