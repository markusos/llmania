from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap


def move(
    entity: Union["Player", "Monster"],
    world_map: "WorldMap",
    message_log: "MessageLog",
    winning_position: tuple[int, int, int],
    argument: Optional[str] = None,
    world_maps: Optional[Dict[int, "WorldMap"]] = None,
    game_engine: Optional["GameEngine"] = None,
) -> Dict[str, Any]:
    from src.monster import Monster
    from src.player import Player

    current_game_over_state = False
    dx, dy = 0, 0
    if argument == "north":
        dy = -1
    elif argument == "south":
        dy = 1
    elif argument == "east":
        dx = 1
    elif argument == "west":
        dx = -1
    else:
        if isinstance(entity, Player):
            message_log.add_message(f"Unknown direction: {argument}")
        return {"game_over": current_game_over_state}

    new_x, new_y = entity.x + dx, entity.y + dy

    if isinstance(entity, Player):
        floor_before_move = entity.current_floor_id

    if world_map.is_valid_move(new_x, new_y):
        target_tile = world_map.get_tile(new_x, new_y)

        if (
            isinstance(entity, Player)
            and target_tile
            and target_tile.is_portal
            and target_tile.portal_to_floor_id is not None
        ):
            entity.x = new_x
            entity.y = new_y
            new_floor_id = target_tile.portal_to_floor_id
            entity.current_floor_id = new_floor_id
            message_log.add_message(
                f"You step through the portal to floor {new_floor_id}!"
            )
            if game_engine and game_engine.ai_logic:
                game_engine.ai_logic.explorer.mark_portal_as_visited(
                    new_x, new_y, floor_before_move
                )
        elif (
            target_tile
            and target_tile.monster
            and isinstance(entity, Player)
        ):
            msg = f"You bump into a {target_tile.monster.name}!"
            message_log.add_message(msg)
        elif (
            target_tile
            and target_tile.monster
            and isinstance(entity, Monster)
        ):
            pass  # Monster bumps into monster, do nothing
        elif (
            target_tile
            and target_tile.player
            and isinstance(entity, Monster)
        ):
            pass  # Monster bumps into player, do nothing
        else:
            if isinstance(entity, Monster):
                world_map.remove_monster(entity.x, entity.y)
                world_map.place_monster(entity, new_x, new_y)
                entity.x = new_x
                entity.y = new_y
            elif isinstance(entity, Player):
                entity.move(dx, dy)
                message_log.add_message(f"You move {argument}.")

                if (
                    entity.x,
                    entity.y,
                    entity.current_floor_id,
                ) == winning_position:
                    win_tile = world_map.get_tile(
                        winning_position[0], winning_position[1]
                    )
                    if (
                        win_tile
                        and win_tile.item
                        and win_tile.item.properties.get("type") == "quest"
                    ):
                        message_log.add_message(
                            "You reached the Amulet of Yendor's location!"
                        )
    else:
        if isinstance(entity, Player):
            message_log.add_message("You can't move there.")

    return {"game_over": current_game_over_state}
