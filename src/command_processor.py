# Type hinting imports
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.monster import Monster  # For type hinting in _get_adjacent_monsters
    from src.player import Player
    from src.world_map import WorldMap


class CommandProcessor:
    """
    Handles the processing of parsed commands from the player,
    interacting with the game world (Player, WorldMap, etc.)
    and updating the message log.
    """

    def __init__(self):
        """Initializes the CommandProcessor."""
        # Currently no specific initialization needed beyond instantiation.
        pass

    def _get_adjacent_monsters(
        self, x: int, y: int, world_map: "WorldMap"
    ) -> list[tuple["Monster", int, int]]:
        """
        Finds all monsters in tiles adjacent (N, S, E, W) to the given coordinates.

        Args:
            x: The x-coordinate to check around.
            y: The y-coordinate to check around.
            world_map: The WorldMap instance to check for monsters.

        Returns:
            A list of tuples, where each tuple contains (Monster, monster_x, monster_y).
        """
        adjacent_monsters = []
        # Define cardinal directions for adjacency check
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # North, South, West, East
            adj_x, adj_y = x + dx, y + dy
            tile = world_map.get_tile(adj_x, adj_y)
            # If tile exists and has a monster, add it to the list
            if tile and tile.monster:
                adjacent_monsters.append((tile.monster, adj_x, adj_y))
        return adjacent_monsters

    def _process_move(
        self,
        argument: str | None,
        player: "Player",
        world_map: "WorldMap",
        message_log: list[str],
        winning_position: tuple[int, int],
    ) -> bool:
        """
        Processes a 'move' command.

        Args:
            argument: The direction of movement (e.g., "north", "south").
            player: The Player instance.
            world_map: The WorldMap instance.
            message_log: A list to append messages for the player.
            winning_position: The (x,y) tuple for the winning location.

        Returns:
            bool: True if the game is over as a result of this command, False otherwise.
        """
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
            message_log.add_message(f"Unknown direction: {argument}")
            return current_game_over_state  # No change in game state

        new_x, new_y = player.x + dx, player.y + dy
        if world_map.is_valid_move(new_x, new_y):
            target_tile = world_map.get_tile(new_x, new_y)
            if target_tile and target_tile.monster:
                msg = f"You bump into a {target_tile.monster.name}!"
                message_log.add_message(msg)
            else:
                player.move(dx, dy)
                message_log.add_message(f"You move {argument}.")
                if (player.x, player.y) == winning_position:
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
                        )  # Note: This doesn't end game, taking item does
        else:
            message_log.add_message("You can't move there.")
        return current_game_over_state

    def process_command(
        self,
        parsed_command_tuple: tuple[str, str | None] | None,
        player: "Player",
        world_map: "WorldMap",
        message_log: list[str],
        winning_position: tuple[int, int],
    ) -> dict:
        """
        Processes a parsed command tuple (verb, argument).

        Args:
            parsed_command_tuple: A tuple containing the command verb and its argument.
                                 Example: ("move", "north"), ("take", "potion").
            player: The Player instance.
            world_map: The WorldMap instance.
            message_log: A list to append messages for the player.
            winning_position: The (x,y) tuple for the winning location.

        Returns:
            dict: A dictionary containing game state updates, specifically {"game_over": bool}.
        """
        current_game_over_state = (
            False  # Local variable to track game_over status for this command
        )

        if parsed_command_tuple is None:
            message_log.add_message("Unknown command.")
            return {"game_over": current_game_over_state}

        verb, argument = parsed_command_tuple

        # Dispatch to the appropriate _process_* method based on the verb
        if verb == "move":
            current_game_over_state = self._process_move(
                argument, player, world_map, message_log, winning_position
            )
        elif verb == "take":
            current_game_over_state = self._process_take(
                argument, player, world_map, message_log, winning_position
            )
        elif verb == "drop":
            current_game_over_state = self._process_drop(
                argument, player, world_map, message_log
            )
        elif verb == "use":
            current_game_over_state = self._process_use(argument, player, message_log)
        elif verb == "attack":
            current_game_over_state = self._process_attack(
                argument, player, world_map, message_log
            )
        elif verb == "inventory":
            current_game_over_state = self._process_inventory(player, message_log)
        elif verb == "look":
            current_game_over_state = self._process_look(player, world_map, message_log)
        elif verb == "quit":
            current_game_over_state = self._process_quit(message_log)
        # Default case if verb not recognized (parser should ideally prevent this)
        # else:
        #     message_log.append(f"Unknown command action: {verb}")

        return {"game_over": current_game_over_state}

    def _process_take(  # noqa: C901 TODO: Refactor for complexity (C901: too complex)
        self,
        argument: Optional[str],
        player: "Player",
        world_map: "WorldMap",
        message_log: list[str],
        winning_position: tuple[int, int],
    ) -> bool:
        """
        Processes a 'take' command.

        Args:
            argument: The name of the item to take. If None, implies taking any item.
            player: The Player instance.
            world_map: The WorldMap instance.
            message_log: A list to append messages for the player.
            winning_position: The (x,y) tuple for the winning location.

        Returns:
            bool: True if the game is over as a result of this command, False otherwise.
        """
        # argument here is the item name player is trying to take
        tile = world_map.get_tile(player.x, player.y)
        if not (tile and tile.item):
            item_name_msg = argument if argument else "item"
            message_log.add_message(f"There is no {item_name_msg} here to take.")
            return False

        item_to_take = tile.item
        # Check if item name matches (case-insensitive) or if any item can be taken
        if argument and item_to_take.name.lower() != argument.lower():
            message_log.add_message(f"There is no {argument} here to take.")
            return False

        # Check if the item itself is the quest item that triggers a win
        if item_to_take.properties.get("type") == "quest":
            # Player picks up the quest item (e.g., Amulet)
            # The world_map.remove_item and player.take_item will be called later
            # if this block doesn't return True immediately.
            # For a win, we want to announce victory and end the game.

            # Ensure the item is actually removed from the map and added to player inventory
            # before declaring victory, to maintain consistent state.
            removed_item = world_map.remove_item(player.x, player.y)
            if removed_item:  # Should be the quest item
                player.take_item(removed_item)
                # Now append win message and return True for game_over
                if removed_item.name == "Amulet of Yendor":  # Specific name for win msg
                    message_log.add_message(
                        "You picked up the Amulet of Yendor! You win!"
                    )
                else:  # Fallback for other quest items
                    message_log.add_message(
                        f"You picked up the {removed_item.name}! You win!"
                    )
                return True  # Game over - win
            else:
                # This case should ideally not be reached if item_to_take was valid
                message_log.add_message(
                    f"Error: Tried to take quest item {item_to_take.name}, but it couldn't be removed from map."
                )
                return False  # Continue game, error occurred

        # Generic item take (not a quest item, or quest item logic failed to remove)
        removed_item = world_map.remove_item(player.x, player.y)
        if removed_item:  # Ensure item was actually removed by map
            player.take_item(removed_item)
            message_log.add_message(f"You take the {removed_item.name}.")
            return False  # Game not over

        # Should not happen if tile.item was initially present and matched
        # (and was not a successfully processed quest item)
        message_log.add_message(f"Could not remove {item_to_take.name} from map.")
        return False

    def _process_drop(
        self,
        argument: Optional[str],
        player: "Player",
        world_map: "WorldMap",
        message_log: list[str],
    ) -> bool:
        """
        Processes a 'drop' command.

        Args:
            argument: The name of the item to drop.
            player: The Player instance.
            world_map: The WorldMap instance.
            message_log: A list to append messages for the player.

        Returns:
            bool: True if the game is over as a result of this command, False otherwise.
        """
        if argument is None:
            message_log.add_message(
                "Drop what?"
            )  # Parser should ideally prevent this with required arg
            return False

        # Store whether the item to be dropped is currently equipped
        item_is_equipped_weapon = False
        if player.equipped_weapon and argument:  # argument is item_name
            if player.equipped_weapon.name.lower() == argument.lower():
                item_is_equipped_weapon = True

        # Player class handles if item exists in inventory
        dropped_item = player.drop_item(argument)

        if not dropped_item:
            message_log.add_message(f"You don't have a {argument} to drop.")
            return False

        if item_is_equipped_weapon:  # This check needs dropped_item to be not None
            message_log.add_message(f"You unequip the {dropped_item.name}.")

        tile = world_map.get_tile(player.x, player.y)
        if tile and tile.item is None:  # Space available on current tile
            world_map.place_item(dropped_item, player.x, player.y)
            message_log.add_message(f"You drop the {dropped_item.name}.")
        else:  # No space, item goes back to player's inventory
            player.take_item(dropped_item)  # Player takes it back
            # If it was unequipped, it's re-equipped implicitly by taking it back if it's a weapon
            # However, the original intent was to drop it, so we don't re-equip here.
            # The message about unequipping stands if that occurred.
            message_log.add_message(
                f"You can't drop {dropped_item.name} here, space occupied."
            )
        return False

    def _process_use(
        self, argument: Optional[str], player: "Player", message_log: list[str]
    ) -> bool:
        """
        Processes a 'use' command.

        Args:
            argument: The name of the item to use.
            player: The Player instance.
            message_log: A list to append messages for the player.

        Returns:
            bool: True if the game is over as a result of this command, False otherwise.
        """
        if argument is None:
            message_log.add_message("Use what?")  # Parser should ideally prevent this
            return False

        use_message = player.use_item(
            argument
        )  # Player.use_item handles internal logic and messages
        message_log.add_message(use_message)

        # Check if using the item resulted in player's death (e.g., a cursed item)
        # Player.use_item message for cursed items might be like:
        # "The Cursed Ring drains your life! You take X damage."
        # or "The Cursed Amulet drains your life to nothing!"
        # We rely on player.health to determine if it was fatal.
        if "cursed!" in use_message.lower() and player.health <= 0:
            # The specific message "You have succumbed to a cursed item! Game Over."
            # might be redundant if player.use_item already provides a clear "death" message.
            # However, ensuring a "Game Over" message is present if player health is <=0
            # after using a cursed item is good.
            # For now, we assume player.use_item's message is sufficient for the cause,
            # and we just ensure the game over state is triggered.
            # If player.use_item's message isn't clear about death, uncommenting the line below
            # or a similar one might be useful.
            # message_log.add_message("You have succumbed to a cursed item! Game Over.")
            return True  # Game over
        return False

    def _select_attack_target(
        self,
        argument: Optional[str],
        adj_monsters: list[tuple["Monster", int, int]],
        message_log: list[str],
    ) -> Optional[tuple["Monster", int, int]]:
        """
        Selects a target monster from adjacent monsters based on argument or proximity.

        Args:
            argument: The name of the monster to target. If None, targets if only one is adjacent.
            adj_monsters: A list of adjacent monsters (Monster, x, y).
            message_log: A list to append messages for the player.

        Returns:
            A tuple (Monster, x, y) if a target is selected, otherwise None.
        """
        if not adj_monsters:
            message_log.add_message("There is no monster nearby to attack.")
            return None

        target_monster = None
        target_m_x, target_m_y = 0, 0  # Initialize with placeholder values

        if argument:  # Monster name specified by player
            # Find the monster by name (case-insensitive)
            found_monster_tuple = next(
                (
                    m_tuple
                    for m_tuple in adj_monsters
                    if m_tuple[0].name.lower() == argument.lower()
                ),
                None,
            )
            if not found_monster_tuple:
                message_log.add_message(f"No monster named '{argument}' nearby.")
                return None
            target_monster, target_m_x, target_m_y = found_monster_tuple
        elif len(adj_monsters) == 1:  # No name specified, only one monster nearby
            target_monster, target_m_x, target_m_y = adj_monsters[0]
        else:  # No name specified, multiple monsters nearby
            monster_names = sorted([m_tuple[0].name for m_tuple in adj_monsters])
            message_log.add_message(
                f"Multiple monsters nearby: {', '.join(monster_names)}. Which one?"
            )
            return None

        # This check should ideally be redundant if the logic above is correct.
        if not target_monster:
            message_log.add_message(
                "Error: Could not select a target monster."
            )  # Should not happen
            return None

        return target_monster, target_m_x, target_m_y

    def _process_attack(  # noqa: C901 TODO: Refactor for complexity (C901: too complex)
        self,
        argument: Optional[str],
        player: "Player",
        world_map: "WorldMap",
        message_log: list[str],
    ) -> bool:
        """
        Processes an 'attack' command.

        Args:
            argument: The name of the monster to attack. If None, auto-targets if one is nearby.
            player: The Player instance.
            world_map: The WorldMap instance.
            message_log: A list to append messages for the player.

        Returns:
            bool: True if the game is over as a result of this command, False otherwise.
        """
        adj_monsters = self._get_adjacent_monsters(player.x, player.y, world_map)

        target_info = self._select_attack_target(argument, adj_monsters, message_log)
        if target_info is None:
            return False  # Game not over, target selection failed or no target, message already logged

        target_monster, target_m_x, target_m_y = target_info

        # Player attacks the selected monster
        attack_res = player.attack_monster(target_monster)
        message_log.add_message(
            f"You attack the {target_monster.name} "
            f"for {attack_res['damage_dealt']} damage."
        )

        if attack_res["monster_defeated"]:
            message_log.add_message(f"You defeated the {target_monster.name}!")
            world_map.remove_monster(target_m_x, target_m_y)
            return False  # Monster defeated, game not over

        # Monster attacks back if not defeated
        monster_attack_res = target_monster.attack(player)
        message_log.add_message(
            f"The {target_monster.name} attacks you for "
            f"{monster_attack_res['damage_dealt_to_player']} damage."
        )

        if monster_attack_res["player_is_defeated"]:
            message_log.add_message("You have been defeated. Game Over.")
            return True  # Player defeated, game over

        return False  # Default: game not over unless player was defeated

    def _process_inventory(self, player: "Player", message_log: list[str]) -> bool:
        """
        Processes an 'inventory' command. Displays the player's inventory.

        Args:
            player: The Player instance.
            message_log: A list to append messages for the player.

        Returns:
            bool: Always False, as this command does not end the game.
        """
        if not player.inventory:
            message_log.add_message("Your inventory is empty.")
        else:
            item_names = [item.name for item in player.inventory]
            # Consider adding equipped status for weapons, e.g., "Iron Sword (equipped)"
            inventory_display = []
            for item in player.inventory:
                display_name = item.name
                if player.equipped_weapon == item:
                    display_name += " (equipped)"
                inventory_display.append(display_name)
            message_log.add_message(f"Inventory: {', '.join(inventory_display)}")
        return False

    def _process_look(
        self, player: "Player", world_map: "WorldMap", message_log: list[str]
    ) -> bool:
        """
        Processes a 'look' command. Describes the player's current location and surroundings.

        Args:
            player: The Player instance.
            world_map: The WorldMap instance.
            message_log: A list to append messages for the player.

        Returns:
            bool: Always False, as this command does not end the game.
        """
        message_log.add_message(f"You are at ({player.x}, {player.y}).")

        current_tile = world_map.get_tile(player.x, player.y)
        item_seen_on_tile = False
        monster_on_tile = False
        if current_tile:
            if current_tile.item:
                message_log.add_message(f"You see a {current_tile.item.name} here.")
                item_seen_on_tile = True
            if current_tile.monster:  # Monster ON player's tile
                message_log.add_message(f"There is a {current_tile.monster.name} here!")
                # This implies player can't move here; 'look' should report it.
                monster_on_tile = True

        adj_monsters = self._get_adjacent_monsters(player.x, player.y, world_map)
        adj_monster_seen = False
        if adj_monsters:
            for monster, mx, my in adj_monsters:
                message_log.add_message(f"You see a {monster.name} at ({mx}, {my}).")
                adj_monster_seen = True

        # "The area is clear" if nothing on tile and no adjacent monsters.
        is_area_clear = (
            not item_seen_on_tile and not adj_monster_seen and not monster_on_tile
        )
        if is_area_clear:
            message_log.add_message("The area is clear.")
        return False

    def _process_quit(self, message_log: list[str]) -> bool:
        """
        Processes a 'quit' command.

        Args:
            message_log: A list to append messages for the player.

        Returns:
            bool: True, as this command ends the game.
        """
        message_log.add_message("Quitting game.")
        return True  # Game over
