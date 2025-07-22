from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.message_log import MessageLog
    from src.player import Player
    from src.renderer import Renderer
    from src.world_map import WorldMap


class DebugManager:
    """Handles debug-related functionalities, such as printing maps and game state.
    This class centralizes all debugging logic, making it easy to enable or
    disable debug features and to add new debugging capabilities.
    Args:
        player (Player): The player character.
        world_maps (dict[int, WorldMap]): A dictionary of all world maps.
        renderer (Renderer): The renderer for displaying the game.
        message_log (MessageLog): The message log for displaying game messages.
        winning_pos (tuple[int, int, int]): The winning position.
    """

    def __init__(
        self,
        player: Player,
        world_maps: dict[int, WorldMap],
        renderer: Renderer,
        message_log: MessageLog,
        winning_pos: tuple[int, int, int],
    ):
        self.player = player
        self.world_maps = world_maps
        self.renderer = renderer
        self.message_log = message_log
        self.winning_pos = winning_pos

    def setup_debug_mode(self) -> None:
        """
        Sets up the debug mode.
        """
        print("--- Starting Game in Debug Mode ---")
        print(f"\nPlayer initial position: ({self.player.x}, {self.player.y})")
        print(f"Player initial health: {self.player.health}")
        print(f"Winning position: {self.winning_pos}")
        self.print_full_map_debug()

    def print_full_map_debug(self) -> None:
        """
        Prints the full map layout for debugging purposes.
        """
        print("\n--- World Map Layout ---")
        for floor_id, world_map in sorted(self.world_maps.items()):
            print(f"\n--- Floor {floor_id} ---")
            map_render = world_map.get_map_as_string(self.renderer, self.message_log)
            if map_render:
                for row in map_render:
                    print(row)

            portal_info = []
            for y in range(world_map.height):
                for x in range(world_map.width):
                    tile = world_map.get_tile(x, y)
                    if tile and tile.is_portal:
                        portal_info.append(
                            f"Portal at ({x}, {y}) -> Floor {tile.portal_to_floor_id}"
                        )
            if portal_info:
                print("Portals:")
                for info in portal_info:
                    print(f"- {info}")
