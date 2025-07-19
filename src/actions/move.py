from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap


class MoveAction:
    def __init__(
        self,
        entity: Union[Player, Monster],
        world_map: WorldMap,
        message_log: MessageLog,
        winning_position: tuple[int, int, int],
        argument: Optional[str] = None,
        world_maps: Optional[Dict[int, WorldMap]] = None,
        game_engine: Optional[GameEngine] = None,
    ):
        self.entity = entity
        self.world_map = world_map
        self.message_log = message_log
        self.winning_position = winning_position
        self.argument = argument
        self.world_maps = world_maps
        self.game_engine = game_engine

    def execute(self) -> Dict[str, Any]:
        from src.monster import Monster
        from src.player import Player

        if isinstance(self.entity, Player):
            return self._handle_player_move()
        elif isinstance(self.entity, Monster):
            return self._handle_monster_move()
        return {"game_over": False}

    def _handle_player_move(self) -> Dict[str, Any]:

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

        new_x, new_y = self.entity.x + dx, self.entity.y + dy

        floor_before_move = self.entity.current_floor_id

        if self.world_map.is_valid_move(new_x, new_y):
            target_tile = self.world_map.get_tile(new_x, new_y)

            if (
                target_tile
                and target_tile.is_portal
                and target_tile.portal_to_floor_id is not None
            ):
                self.entity.x = new_x
                self.entity.y = new_y
                new_floor_id = target_tile.portal_to_floor_id
                self.entity.current_floor_id = new_floor_id
                self.message_log.add_message(
                    f"You step through the portal to floor {new_floor_id}!"
                )
                if self.game_engine and self.game_engine.ai_logic:
                    self.game_engine.ai_logic.explorer.mark_portal_as_visited(
                        new_x, new_y, floor_before_move
                    )
            elif target_tile and target_tile.monster:
                msg = f"You bump into a {target_tile.monster.name}!"
                self.message_log.add_message(msg)
            else:
                self.world_map.remove_player(self.entity.x, self.entity.y)
                self.entity.move(dx, dy)
                self.world_map.place_player(self.entity, self.entity.x, self.entity.y)
                self.message_log.add_message(f"You move {self.argument}.")

                if (
                    self.entity.x,
                    self.entity.y,
                    self.entity.current_floor_id,
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
            self.message_log.add_message("You can't move there.")

        return {"game_over": current_game_over_state}

    def _handle_monster_move(self) -> Dict[str, Any]:

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

        new_x, new_y = self.entity.x + dx, self.entity.y + dy

        if self.world_map.is_valid_move(new_x, new_y):
            target_tile = self.world_map.get_tile(new_x, new_y)

            if target_tile and target_tile.monster:
                pass  # Monster bumps into monster, do nothing
            elif target_tile and target_tile.player:
                pass  # Monster bumps into player, do nothing
            else:
                self.world_map.remove_monster(self.entity.x, self.entity.y)
                self.world_map.place_monster(self.entity, new_x, new_y)

        return {"game_over": current_game_over_state}


def move(
    entity: Union["Player", "Monster"],
    world_map: "WorldMap",
    message_log: "MessageLog",
    winning_position: tuple[int, int, int],
    argument: Optional[str] = None,
    world_maps: Optional[Dict[int, "WorldMap"]] = None,
    game_engine: Optional["GameEngine"] = None,
) -> Dict[str, Any]:
    action = MoveAction(
        entity,
        world_map,
        message_log,
        winning_position,
        argument,
        world_maps,
        game_engine,
    )
    return action.execute()
