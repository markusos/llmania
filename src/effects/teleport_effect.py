from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .base_effect import Effect

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.player import Player


class TeleportEffect(Effect):
    def apply(self, player: "Player", game_engine: "GameEngine") -> str:
        current_map = game_engine.world_maps[player.current_floor_id]
        walkable_tiles = [
            (x, y)
            for y in range(current_map.height)
            for x in range(current_map.width)
            if current_map.get_tile(x, y) and current_map.get_tile(x, y).type == "floor"
        ]
        if walkable_tiles:
            new_x, new_y = random.choice(walkable_tiles)
            current_map.remove_player(player.x, player.y)
            player.x, player.y = new_x, new_y
            current_map.place_player(player, new_x, new_y)
            game_engine._update_fog_of_war_visibility()
            return "You were teleported to a new location."
        return "The scroll fizzles, but nothing happens."
