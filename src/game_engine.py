import random

from src.ai_logic import AILogic
from src.command_processor import CommandProcessor
from src.debug_manager import DebugManager
from src.fog_of_war import FogOfWar
from src.game_manager import GameManager
from src.input_handler import InputHandler
from src.message_log import MessageLog
from src.monster_ai.main import MonsterAILogic
from src.parser import Parser
from src.player import Player
from src.renderer import Renderer
from src.world_generator import WorldGenerator
from src.world_map import WorldMap


class GameEngine:
    def __init__(
        self,
        map_width: int = 20,
        map_height: int = 10,
        debug_mode: bool = False,
        ai_active: bool = False,
        ai_sleep_duration: float = 0.5,
        seed: int | None = None,
        verbose: int = 0,
        world_maps: dict[int, WorldMap] | None = None,
        player_start_pos: tuple[int, int, int] | None = None,
        winning_pos: tuple[int, int, int] | None = None,
    ):
        self.world_generator = WorldGenerator()
        self.parser = Parser()
        self.debug_mode = debug_mode
        self.ai_active = ai_active
        self.ai_sleep_duration = ai_sleep_duration
        self.verbose = verbose
        self.random = random.Random(seed)
        self._debug_commands: list[tuple[str, str | None]] | None = None

        self.visible_maps: dict[int, WorldMap] = {}

        if world_maps:
            self.world_maps = world_maps
            player_start_full_pos = player_start_pos or (
                map_width // 2,
                map_height // 2,
                0,
            )
            self.winning_full_pos = winning_pos or (0, 0, -1)
        else:
            (
                self.world_maps,
                player_start_full_pos,
                self.winning_full_pos,
                _floor_details_list,
            ) = self.world_generator.generate_world(
                map_width, map_height, random_generator=self.random
            )

        for floor_id, w_map in self.world_maps.items():
            self.visible_maps[floor_id] = WorldMap(
                width=w_map.width, height=w_map.height
            )

        first_floor_id = min(self.world_maps.keys()) if self.world_maps else 0
        render_map_width = (
            self.world_maps[first_floor_id].width if self.world_maps else map_width
        )
        render_map_height = (
            self.world_maps[first_floor_id].height if self.world_maps else map_height
        )

        player_symbol = "@"
        self.renderer = Renderer(
            debug_mode=self.debug_mode,
            map_width=render_map_width,
            map_height=render_map_height,
            player_symbol=player_symbol,
        )

        self.input_handler = InputHandler(self.renderer.stdscr, self.parser)
        self.command_processor = CommandProcessor()

        self.player = Player(
            x=player_start_full_pos[0],
            y=player_start_full_pos[1],
            current_floor_id=player_start_full_pos[2],
            health=20,
        )
        self.message_log = MessageLog(max_messages=5)

        ai_logic = None
        if self.ai_active:
            ai_logic = AILogic(
                player=self.player,
                real_world_maps=self.world_maps,
                ai_visible_maps=self.visible_maps,
                message_log=self.message_log,
                random_generator=self.random,
                verbose=self.verbose,
            )

        self.fog_of_war = FogOfWar(
            player=self.player,
            world_maps=self.world_maps,
            visible_maps=self.visible_maps,
            message_log=self.message_log,
        )

        if self.debug_mode:
            self.debug_manager = DebugManager(
                player=self.player,
                world_maps=self.world_maps,
                renderer=self.renderer,
                message_log=self.message_log,
                winning_pos=self.winning_full_pos,
            )

        self.game_manager = GameManager(
            player=self.player,
            world_maps=self.world_maps,
            message_log=self.message_log,
            renderer=self.renderer,
            input_handler=self.input_handler,
            command_processor=self.command_processor,
            ai_logic=ai_logic,
            debug_mode=self.debug_mode,
        )

        self._initialize_monster_ai()
        self.fog_of_war.update_visibility()
        self.world_maps[self.player.current_floor_id].place_player(
            self.player, self.player.x, self.player.y
        )

    def _initialize_monster_ai(self):
        for floor_id, world_map in self.world_maps.items():
            for monster in world_map.get_monsters():
                monster.ai = MonsterAILogic(
                    monster=monster,
                    player=self.player,
                    world_map=world_map,
                    random_generator=self.random,
                )

    def run(self):
        if self.debug_mode:
            self.debug_manager.setup_debug_mode()

        try:
            self.game_manager.run(self.fog_of_war)
            self.game_manager._handle_game_over()
        finally:
            if not self.debug_mode:
                self.renderer.cleanup_curses()
