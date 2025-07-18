from typing import TYPE_CHECKING, Any, Dict, Optional, Union

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
        from src.monster import Monster
        from src.player import Player

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
            if isinstance(self.entity, Player):
                self.message_log.add_message(f"Unknown direction: {self.argument}")
            return {"game_over": current_game_over_state}

        new_x, new_y = self.entity.x + dx, self.entity.y + dy

        if isinstance(self.entity, Player):
            floor_before_move = self.player.current_floor_id

        if self.world_map.is_valid_move(new_x, new_y):
            target_tile = self.world_map.get_tile(new_x, new_y)

            if (
                isinstance(self.entity, Player)
                and target_tile
                and target_tile.is_portal
                and target_tile.portal_to_floor_id is not None
            ):
                self.player.x = new_x
                self.player.y = new_y
                new_floor_id = target_tile.portal_to_floor_id
                self.player.current_floor_id = new_floor_id
                self.message_log.add_message(
                    f"You step through the portal to floor {new_floor_id}!"
                )
                if self.game_engine and self.game_engine.ai_logic:
                    self.game_engine.ai_logic.explorer.mark_portal_as_visited(
                        new_x, new_y, floor_before_move
                    )
            elif (
                target_tile
                and target_tile.monster
                and isinstance(self.entity, Player)
            ):
                msg = f"You bump into a {target_tile.monster.name}!"
                self.message_log.add_message(msg)
            elif (
                target_tile
                and target_tile.monster
                and isinstance(self.entity, Monster)
            ):
                pass  # Monster bumps into monster, do nothing
            elif (
                target_tile
                and target_tile.player
                and isinstance(self.entity, Monster)
            ):
                pass  # Monster bumps into player, do nothing
            else:
                if isinstance(self.entity, Monster):
                    self.world_map.remove_monster(self.entity.x, self.entity.y)
                    self.world_map.place_monster(self.entity, new_x, new_y)
                    self.entity.x = new_x
                    self.entity.y = new_y
                elif isinstance(self.entity, Player):
                    self.entity.move(dx, dy)
                    self.message_log.add_message(f"You move {self.argument}.")

                    if (
                        self.player.x,
                        self.player.y,
                        self.player.current_floor_id,
                    ) == self.winning_position:
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
            if isinstance(self.entity, Player):
                self.message_log.add_message("You can't move there.")

        return {"game_over": current_game_over_state}
