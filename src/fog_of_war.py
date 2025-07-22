from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap


class FogOfWar:
    """Manages the fog of war, determining which parts of the map are visible.
    This class handles the logic for updating the player's field of view and
    revealing the map as the player explores.
    Args:
        player (Player): The player character.
        world_maps (dict[int, WorldMap]): A dictionary of all real-world maps.
        visible_maps (dict[int, WorldMap]): A dictionary of maps representing
                                            what the player can see.
        message_log (MessageLog): The message log for displaying game messages.
    """

    def __init__(
        self,
        player: Player,
        world_maps: dict[int, WorldMap],
        visible_maps: dict[int, WorldMap],
        message_log: MessageLog,
    ):
        self.player = player
        self.world_maps = world_maps
        self.visible_maps = visible_maps
        self.message_log = message_log

    def update_visibility(self) -> None:
        """
        Updates the fog of war visibility based on the player's position.
        """
        player_x, player_y = self.player.x, self.player.y
        current_floor_id = self.player.current_floor_id

        current_real_map = self.world_maps.get(current_floor_id)
        current_visible_map = self.visible_maps.get(current_floor_id)

        if not current_real_map or not current_visible_map:
            self.message_log.add_message(
                f"Error: Invalid floor ID {current_floor_id} for visibility."
            )
            return

        # At the beginning of the update, clear all monster visibility on the
        # visible map. This ensures that monsters that move out of sight are no
        # longer drawn.
        for y in range(current_visible_map.height):
            for x in range(current_visible_map.width):
                tile = current_visible_map.get_tile(x, y)
                if tile:
                    tile.monster = None

        # This is for revealing the map, items, and portals
        for dy_offset in range(-1, 2):
            for dx_offset in range(-1, 2):
                map_x, map_y = player_x + dx_offset, player_y + dy_offset

                if not (
                    0 <= map_x < current_real_map.width
                    and 0 <= map_y < current_real_map.height
                ):
                    continue

                real_tile = current_real_map.get_tile(map_x, map_y)
                if real_tile:
                    visible_tile = current_visible_map.get_tile(map_x, map_y)
                    if visible_tile:
                        visible_tile.type = real_tile.type
                        # Don't update monster here, handle it separately
                        visible_tile.item = real_tile.item
                        visible_tile.is_portal = real_tile.is_portal
                        visible_tile.portal_to_floor_id = real_tile.portal_to_floor_id
                        visible_tile.is_explored = True

        # Now, specifically handle monster visibility on currently visible tiles.
        for y in range(player_y - 1, player_y + 2):
            for x in range(player_x - 1, player_x + 2):
                if not (
                    0 <= x < current_real_map.width and 0 <= y < current_real_map.height
                ):
                    continue

                real_tile = current_real_map.get_tile(x, y)
                if real_tile and real_tile.monster:
                    visible_tile = current_visible_map.get_tile(x, y)
                    if visible_tile:
                        visible_tile.monster = real_tile.monster
