# Type hinting imports
from typing import TYPE_CHECKING, Optional

from src.inventory_manager import InventoryManager # Import InventoryManager

if TYPE_CHECKING:
    from src.monster import Monster  # For type hinting in _get_adjacent_monsters
    from src.player import Player
    from src.world_map import WorldMap


class CommandProcessor:
    def __init__(self):
        self.inventory_manager = InventoryManager() # Initialize InventoryManager

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

    def _process_move(
        self,
        argument: str | None,
        player: "Player",
        world_map: "WorldMap",
        message_log: list[str],
        win_pos: tuple[int, int],
    ) -> bool:
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
            message_log.append(f"Unknown direction: {argument}")
            return current_game_over_state  # No change in game state

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
        return current_game_over_state

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
            current_game_over_state = self._process_move(
                argument, player, world_map, message_log, win_pos
            )
        elif verb == "take":
            current_game_over_state = self._process_take(
                argument, player, world_map, message_log, win_pos
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
            current_game_over_state = self._process_look(
                player, world_map, message_log
            )
        elif verb == "quit":
            current_game_over_state = self._process_quit(message_log)
        # Default case if verb not recognized (parser should ideally prevent this)
        # else:
        #     message_log.append(f"Unknown command action: {verb}")

        return {"game_over": current_game_over_state}
