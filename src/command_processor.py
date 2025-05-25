# Type hinting imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.monster import Monster  # For type hinting in _get_adjacent_monsters
    from src.player import Player
    from src.world_map import WorldMap


class CommandProcessor:
    def __init__(self):
        # No complex initialization needed for now
        pass

    def _get_adjacent_monsters(
        self, x: int, y: int, world_map: "WorldMap"
    ) -> list[tuple["Monster", int, int]]:
        # Logic will be moved here from GameEngine
        adjacent_monsters = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            adj_x, adj_y = x + dx, y + dy
            tile = world_map.get_tile(adj_x, adj_y)
            if tile and tile.monster:
                adjacent_monsters.append((tile.monster, adj_x, adj_y))
        return adjacent_monsters

    def process_command(
        self,
        parsed_command_tuple: tuple[str, str | None] | None,
        player: "Player",
        world_map: "WorldMap",
        message_log: list[str],
        win_pos: tuple[int, int],
    ) -> dict:
        current_game_over_state = (
            False  # Local variable to track game_over status for this command
        )

        if parsed_command_tuple is None:
            message_log.append("Unknown command.")
            return {"game_over": current_game_over_state}

        verb, argument = parsed_command_tuple
        if verb == "move":
            dx, dy = 0, 0
            if argument == "north":
                dy = -1
            elif argument == "south":
                dy = 1
            elif argument == "east":
                dx = 1
            elif argument == "west":
                dx = -1

            new_x, new_y = player.x + dx, player.y + dy
            if world_map.is_valid_move(new_x, new_y):
                target_tile = world_map.get_tile(new_x, new_y)
                if target_tile and target_tile.monster:
                    msg = f"You bump into a {target_tile.monster.name}!"
                    message_log.append(msg)
                else:
                    player.move(dx, dy)
                    message_log.append(f"You move {argument}.")
                    if (player.x, player.y) == win_pos:
                        win_tile = world_map.get_tile(win_pos[0], win_pos[1])
                        if (
                            win_tile
                            and win_tile.item
                            and win_tile.item.properties.get("type") == "quest"
                        ):
                            message_log.append(
                                "You reached the Amulet of Yendor's location!"
                            )  # Note: This doesn't end game, taking item does
            else:
                message_log.append("You can't move there.")

        elif verb == "take":
            tile = world_map.get_tile(player.x, player.y)
            can_take = (
                tile
                and tile.item
                and (argument is None or tile.item.name.lower() == argument.lower())
            )
            if can_take:
                item_taken = world_map.remove_item(player.x, player.y)
                if item_taken:
                    player.take_item(item_taken)
                    message_log.append(f"You take the {item_taken.name}.")
                    is_quest_win = (
                        player.x,
                        player.y,
                    ) == win_pos and item_taken.properties.get("type") == "quest"
                    if is_quest_win:
                        message_log.append(
                            "You picked up the Amulet of Yendor! You win!"
                        )
                        current_game_over_state = True
                else:
                    message_log.append("Error: Tried to take item but failed.")
            else:
                no_item_msg = (
                    f"There is no {argument} here to take."
                    if argument
                    else "Nothing here to take or item name mismatch."
                )
                message_log.append(no_item_msg)

        elif verb == "drop":
            if argument is None:
                message_log.append("What do you want to drop?")
                return {"game_over": current_game_over_state}  # Return early
            dropped_item = player.drop_item(argument)
            if dropped_item:
                current_tile = world_map.get_tile(player.x, player.y)
                if current_tile and current_tile.item is None:
                    world_map.place_item(dropped_item, player.x, player.y)
                    message_log.append(f"You drop the {dropped_item.name}.")
                else:
                    player.take_item(dropped_item)  # Player picks it back up
                    msg = f"You can't drop {dropped_item.name} here, space occupied."
                    message_log.append(msg)
            else:
                message_log.append(f"You don't have a {argument} to drop.")

        elif verb == "use":
            if argument is None:
                message_log.append("What do you want to use?")
                return {"game_over": current_game_over_state}  # Return early
            message = player.use_item(argument)
            message_log.append(message)
            # Check if using an item caused player death (e.g. cursed item)
            if player.health <= 0:
                message_log.append("You have succumbed to a cursed item! Game Over.")
                current_game_over_state = True

        elif verb == "attack":
            adj_monsters_coords = self._get_adjacent_monsters(
                player.x,
                player.y,
                world_map,  # Pass world_map
            )
            target_monster, target_x, target_y = None, -1, -1
            if argument:
                named_targets = [
                    (m, mx, my)
                    for m, mx, my in adj_monsters_coords
                    if m.name.lower() == argument.lower()
                ]
                if len(named_targets) == 1:
                    target_monster, target_x, target_y = named_targets[0]
                elif len(named_targets) > 1:
                    message_log.append(f"Multiple {argument}s found. Which one?")
                else:
                    msg = f"There is no monster named {argument} nearby."
                    message_log.append(msg)
            else:
                if not adj_monsters_coords:
                    message_log.append("There is no monster nearby to attack.")
                elif len(adj_monsters_coords) == 1:
                    target_monster, target_x, target_y = adj_monsters_coords[0]
                else:
                    names = ", ".join(
                        sorted(list(set(m.name for m, _, _ in adj_monsters_coords)))
                    )
                    message_log.append(f"Multiple monsters nearby: {names}. Which one?")

            if target_monster and target_x != -1 and target_y != -1:
                # Player's Attack
                attack_results = player.attack_monster(target_monster)
                message_log.append(
                    f"You attack the {attack_results['monster_name']} "
                    f"for {attack_results['damage_dealt']} damage."
                )

                if attack_results["monster_defeated"]:
                    world_map.remove_monster(target_x, target_y)
                    message_log.append(
                        f"You defeated the {attack_results['monster_name']}!"
                    )
                else:
                    # Monster's Counter-Attack
                    monster_attack_results = target_monster.attack(
                        player
                    )  # player is the 'Player' instance
                    message_log.append(
                        f"The {target_monster.name} attacks you for "
                        f"{monster_attack_results['damage_dealt_to_player']} damage."
                    )
                    if monster_attack_results["player_is_defeated"]:
                        message_log.append("You have been defeated. Game Over.")
                        current_game_over_state = True

        elif verb == "inventory":
            if player.inventory:
                item_names = ", ".join([item.name for item in player.inventory])
                message_log.append(f"Inventory: {item_names}")
            else:
                message_log.append("Your inventory is empty.")

        elif verb == "look":
            tile = world_map.get_tile(player.x, player.y)
            message_log.append(f"You are at ({player.x}, {player.y}).")
            if tile:
                if tile.item:
                    message_log.append(f"You see a {tile.item.name} here.")
                if tile.monster:
                    message_log.append(f"There is a {tile.monster.name} here!")

                adj_monsters = self._get_adjacent_monsters(
                    player.x, player.y, world_map
                )  # Pass world_map
                if adj_monsters:
                    for m, x_coord, y_coord in adj_monsters:
                        message_log.append(
                            f"You see a {m.name} at ({x_coord}, {y_coord})."
                        )
                elif (
                    not tile.item and not tile.monster and not adj_monsters
                ):  # Check if all are false
                    message_log.append("The area is clear.")
            else:  # Should not happen if player is on a valid tile
                message_log.append("You are in a void... somehow.")

        elif verb == "quit":
            message_log.append("Quitting game.")
            current_game_over_state = True

        # Default case if verb not recognized (parser should ideally prevent this)
        # else:
        #     message_log.append(f"Unknown command action: {verb}")

        return {"game_over": current_game_over_state}
