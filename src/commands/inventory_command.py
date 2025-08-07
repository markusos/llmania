from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap


class InventoryCommand(Command):
    def __init__(
        self,
        player: "Player",
        world_map: "WorldMap",
        message_log: "MessageLog",
        winning_position: tuple[int, int, int],
        argument: Optional[str] = None,
        world_maps: Optional[Dict[int, "WorldMap"]] = None,
        game_engine: Optional["GameEngine"] = None,
    ):
        super().__init__(
            player,
            world_map,
            message_log,
            winning_position,
            argument,
            world_maps,
            game_engine,
        )

    def execute(self) -> Dict[str, Any]:
        if not self.game_engine:
            return {"game_over": False}

        # Toggle inventory mode
        if self.game_engine.input_mode == "inventory":
            self.game_engine.input_mode = "normal"
            if self.game_engine.renderer:
                self.game_engine.renderer.render_all(
                    player_x=self.player.x,
                    player_y=self.player.y,
                    player_health=self.player.health,
                    world_map_to_render=self.world_map,
                    input_mode=self.game_engine.input_mode,
                    current_command_buffer=self.game_engine.command_buffer,
                    message_log=self.message_log,
                    current_floor_id=self.player.current_floor_id,
                )
        else:
            self.game_engine.input_mode = "inventory"
            # The renderer will handle drawing the inventory screen
            # based on the new input_mode.
        return {"game_over": False}
