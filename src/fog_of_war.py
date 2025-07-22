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

        self._clear_monster_visibility(current_visible_map)

        self._update_player_fov(
            player_x, player_y, current_real_map, current_visible_map
        )

    def _clear_monster_visibility(self, visible_map: WorldMap):
        """Clears monster visibility from the visible map."""
        for y in range(visible_map.height):
            for x in range(visible_map.width):
                tile = visible_map.get_tile(x, y)
                if tile:
                    tile.monster = None

    def _update_player_fov(
        self,
        player_x: int,
        player_y: int,
        real_map: WorldMap,
        visible_map: WorldMap,
    ):
        """Updates the player's field of view."""
        for dy_offset in range(-1, 2):
            for dx_offset in range(-1, 2):
                map_x, map_y = player_x + dx_offset, player_y + dy_offset

                if not (0 <= map_x < real_map.width and 0 <= map_y < real_map.height):
                    continue

                self._reveal_tile(map_x, map_y, real_map, visible_map)

    def _reveal_tile(
        self, x: int, y: int, real_map: WorldMap, visible_map: WorldMap
    ) -> None:
        """Reveals a single tile on the visible map."""
        real_tile = real_map.get_tile(x, y)
        if not real_tile:
            return

        visible_tile = visible_map.get_tile(x, y)
        if not visible_tile:
            return

        visible_tile.type = real_tile.type
        visible_tile.item = real_tile.item
        visible_tile.is_portal = real_tile.is_portal
        visible_tile.portal_to_floor_id = real_tile.portal_to_floor_id
        visible_tile.is_explored = True
        visible_tile.monster = real_tile.monster
