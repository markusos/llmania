from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap


class MoveCommand(Command):
    def __init__(
        self,
        player: "Player",
        world_map: "WorldMap",  # Current floor's map
        message_log: "MessageLog",
        winning_position: tuple[int, int, int],  # (x,y,floor_id)
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

        # world_map is the map of the player's current floor.
        if self.world_map.is_valid_move(new_x, new_y):
            target_tile = self.world_map.get_tile(new_x, new_y)

            if (
                target_tile
                and target_tile.is_portal
                and target_tile.portal_to_floor_id is not None
            ):
                # Portal traversal
                # Player's (x,y) effectively stays the same relative to the portal,
                # but they are now on a new floor.
                # The move action places them "on" the portal tile.
                self.player.x = new_x
                self.player.y = new_y
                new_floor_id = target_tile.portal_to_floor_id
                self.player.current_floor_id = new_floor_id
                self.message_log.add_message(
                    f"You step through the portal to floor {new_floor_id}!"
                )
                # GameEngine handles fog of war for the new floor.
                # CommandProcessor provides the correct map for the next command.
            elif target_tile and target_tile.monster:
                # Bump into monster
                msg = f"You bump into a {target_tile.monster.name}!"
                self.message_log.add_message(msg)
            else:
                # Standard move on the current floor
                self.player.move(dx, dy)  # Updates player.x, player.y
                self.message_log.add_message(f"You move {self.argument}.")

                # Check for winning condition only if not a portal step
                # Winning position includes floor_id.
                if (
                    self.player.x,
                    self.player.y,
                    self.player.current_floor_id,
                ) == self.winning_position:
                    # Ensure we are checking the correct map for the win tile item.
                    # This should be the map of the winning_position's floor.
                    # self.world_map is current floor's map.
                    # If win_pos floor_id matches player.current_floor_id, it's fine.
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
                        # Taking amulet is a separate command, this just notes location.
        else:
            self.message_log.add_message("You can't move there.")

        return {"game_over": current_game_over_state}
