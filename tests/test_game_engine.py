import curses
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from src.game_engine import GameEngine
from src.game_state import GameState
from src.message_log import MessageLog
from src.world_map import WorldMap


class TestGameEngine(unittest.TestCase):
    @patch("src.game_engine.WorldGenerator")
    @patch("src.game_engine.InputHandler")
    @patch("src.game_engine.Renderer")
    @patch("src.game_engine.CommandProcessor")
    @patch("src.game_engine.Parser")
    @patch("src.game_engine.Player")
    def setUp(
        self,
        MockPlayer,
        MockParser,
        MockCommandProcessor,
        MockRenderer,
        MockInputHandler,
        MockWorldGenerator,
    ):
        self.stdout_original = sys.stdout
        sys.stdout = open(os.devnull, "w")

        self.MockPlayer = MockPlayer
        self.MockParser = MockParser
        self.MockCommandProcessor = MockCommandProcessor
        self.MockRenderer = MockRenderer
        self.MockInputHandler = MockInputHandler
        self.MockWorldGenerator = MockWorldGenerator

        self.mock_stdscr = MagicMock()

        self.mock_world_gen_instance = self.MockWorldGenerator.return_value
        self.mock_world_map_instance = WorldMap(20, 10)

        self.player_start_coords_f0 = (1, 1)
        self.player_start_full_pos_f0 = (1, 1, 0)
        self.poi_coords_f0 = (5, 5)
        self.winning_full_pos_f0 = (5, 5, 0)

        # Mock for generate_world (now called by GameEngine.__init__)
        self.mock_world_gen_instance.generate_world.return_value = (
            {0: self.mock_world_map_instance},
            self.player_start_full_pos_f0,
            self.winning_full_pos_f0,
            [],
        )

        self.mock_player_instance = self.MockPlayer.return_value
        self.mock_player_instance.x = self.player_start_coords_f0[0]
        self.mock_player_instance.y = self.player_start_coords_f0[1]
        self.mock_player_instance.current_floor_id = 0
        self.mock_player_instance.health = 100
        self.mock_player_instance.invisibility_turns = 0

        self.mock_parser_instance = self.MockParser.return_value
        self.mock_input_handler_instance = self.MockInputHandler.return_value
        self.mock_input_handler_instance.get_input_mode.return_value = "movement"
        self.mock_input_handler_instance.get_command_buffer.return_value = ""
        self.mock_renderer_instance = self.MockRenderer.return_value
        self.mock_renderer_instance.cleanup_curses = MagicMock(spec=lambda: None)
        self.mock_renderer_instance.stdscr = self.mock_stdscr  # Mock stdscr
        self.mock_command_processor_instance = self.MockCommandProcessor.return_value
        self.game_engine = GameEngine(map_width=20, map_height=10, debug_mode=False)
        self.player = self.game_engine.player
        self.game_engine.world_generator = self.mock_world_gen_instance
        self.game_engine.parser = self.MockParser.return_value
        self.game_engine.player = self.MockPlayer.return_value
        self.game_engine.input_handler = self.MockInputHandler.return_value
        self.game_engine.renderer = self.MockRenderer.return_value
        self.game_engine.command_processor = self.MockCommandProcessor.return_value

        self.game_engine.world_maps = {0: self.mock_world_map_instance}
        mock_visible_map_f0 = MagicMock(spec=WorldMap)
        mock_visible_map_f0.width = self.mock_world_map_instance.width
        mock_visible_map_f0.height = self.mock_world_map_instance.height
        self.game_engine.visible_maps = {0: mock_visible_map_f0}
        self.game_engine.winning_full_pos = (
            self.poi_coords_f0[0],
            self.poi_coords_f0[1],
            0,
        )

        if not self.game_engine.debug_mode:
            self.game_engine.renderer.stdscr = self.mock_stdscr

    def tearDown(self):
        # Restore stdout
        sys.stdout.close()
        sys.stdout = self.stdout_original

    def test_game_engine_initialization(self):
        self.mock_world_gen_instance.generate_world.assert_called_once()
        # Further argument checks can be done here if needed, e.g., by
        # inspecting `call_args`.
        self.MockPlayer.assert_called_once_with(
            x=self.player_start_full_pos_f0[0],
            y=self.player_start_full_pos_f0[1],
            current_floor_id=self.player_start_full_pos_f0[2],
            health=20,
        )
        self.assertEqual(self.game_engine.player.x, self.player_start_coords_f0[0])
        self.assertEqual(self.game_engine.player.y, self.player_start_coords_f0[1])
        self.assertEqual(self.game_engine.player.current_floor_id, 0)
        self.assertIsNotNone(self.game_engine.parser)
        self.assertIsNotNone(self.game_engine.input_handler)
        self.assertIsNotNone(self.game_engine.renderer)
        self.assertIsNotNone(self.game_engine.command_processor)
        self.assertEqual(self.game_engine.game_manager.game_state, GameState.PLAYING)
        self.assertIsInstance(self.game_engine.message_log, MessageLog)
        self.assertEqual(self.game_engine.debug_mode, False)

    @patch("curses.napms")
    def test_run_loop_single_command_then_quit(self, mock_napms):
        self.mock_input_handler_instance.handle_input_and_get_command.side_effect = [
            ("move", "north"),
            ("quit", None),
        ]

        def process_cmd_side_effect(
            parsed_cmd_tuple,
            player,
            world_maps_dict,
            msg_log,
            win_pos_arg,
            game_engine=None,
        ):
            if parsed_cmd_tuple == ("quit", None):
                self.game_engine.game_manager.game_state = GameState.QUIT
            return {"game_over": False}

        self.mock_command_processor_instance.process_command.side_effect = (
            process_cmd_side_effect
        )
        self.game_engine.run()
        self.assertEqual(
            self.mock_input_handler_instance.handle_input_and_get_command.call_count, 2
        )
        self.mock_command_processor_instance.process_command.assert_any_call(
            ("move", "north"),
            self.game_engine.player,
            self.game_engine.world_maps,
            self.game_engine.message_log,
            (0, 0, -1),
            game_engine=self.game_engine.game_manager,
        )
        self.mock_command_processor_instance.process_command.assert_any_call(
            ("quit", None),
            self.game_engine.player,
            self.game_engine.world_maps,
            self.game_engine.message_log,
            (0, 0, -1),
            game_engine=self.game_engine.game_manager,
        )
        self.assertEqual(
            self.mock_command_processor_instance.process_command.call_count, 2
        )
        self.assertEqual(self.game_engine.game_manager.game_state, GameState.QUIT)
        if not self.game_engine.debug_mode:
            self.mock_renderer_instance.cleanup_curses.assert_called_once()
        else:
            mock_napms.assert_not_called()
            self.mock_renderer_instance.cleanup_curses.assert_not_called()

    def test_run_loop_game_over_from_command(self):
        self.mock_input_handler_instance.handle_input_and_get_command.side_effect = [
            ("attack", "dragon"),
            ("quit", None),  # To exit the loop
        ]
        self.mock_command_processor_instance.process_command.return_value = {
            "game_over": True
        }
        self.game_engine.debug_mode = False

        with patch("curses.napms") as mock_napms:
            self.game_engine.run()
            mock_napms.assert_called_once_with(2000)

        self.assertEqual(
            self.mock_input_handler_instance.handle_input_and_get_command.call_count, 2
        )
        self.mock_command_processor_instance.process_command.assert_called_once()
        self.assertEqual(self.game_engine.game_manager.game_state, GameState.QUIT)
        self.mock_renderer_instance.cleanup_curses.assert_called_once()

    def test_game_ends_when_player_dies(self):
        # Arrange
        self.game_engine.debug_mode = True
        self.game_engine.game_manager.debug_mode = True
        self.game_engine.game_manager._debug_commands = [("some_command", None)]

        def process_command_side_effect(*args, **kwargs):
            # Simulate player health dropping to 0 after a command
            self.game_engine.player.health = 0
            return {"game_over": False}

        self.mock_command_processor_instance.process_command.side_effect = (
            process_command_side_effect
        )

        # Act
        self.game_engine.run()

        # Assert
        self.assertEqual(
            self.game_engine.game_manager.game_state, GameState.GAME_OVER
        )
        self.assertIn(
            "You have been defeated. Game Over.",
            [msg for msg in self.game_engine.message_log.messages],
        )

    def test_game_ends_when_player_wins(self):
        # Arrange
        self.game_engine.debug_mode = True
        self.game_engine.game_manager.debug_mode = True
        self.game_engine.game_manager._debug_commands = [("move", "east")]

        def process_command_side_effect(*args, **kwargs):
            # Simulate player reaching the winning position
            self.game_engine.player.x = self.game_engine.winning_full_pos[0]
            self.game_engine.player.y = self.game_engine.winning_full_pos[1]
            self.game_engine.player.current_floor_id = (
                self.game_engine.winning_full_pos[2]
            )
            return {"game_over": True}

        self.mock_command_processor_instance.process_command.side_effect = (
            process_command_side_effect
        )

        # Act
        self.game_engine.run()

        # Assert
        self.assertEqual(
            self.game_engine.game_manager.game_state, GameState.GAME_OVER
        )

    def test_run_loop_debug_mode_no_curses_cleanup(self):
        with patch("src.game_engine.WorldGenerator") as MockWG_debug, patch(
            "src.game_engine.InputHandler"
        ), patch("src.game_engine.Renderer") as MockRenderer_debug, patch(
            "src.game_engine.CommandProcessor"
        ) as MockCP_debug, patch(
            "src.game_engine.Parser"
        ), patch(
            "src.game_engine.Player"
        ):
            mock_renderer_instance = MockRenderer_debug.return_value
            mock_renderer_instance.cleanup_curses = MagicMock()
            mock_wg_inst_debug = MockWG_debug.return_value
            mock_wm_inst_debug = MagicMock(spec=WorldMap)
            mock_wm_inst_debug.width = 10
            mock_wm_inst_debug.height = 5
            mock_wg_inst_debug.generate_world.return_value = (
                {0: mock_wm_inst_debug},
                (0, 0, 0),
                (1, 1, 0),
                [],
            )

            debug_engine = GameEngine(map_width=10, map_height=5, debug_mode=True)
            debug_engine.game_manager._debug_commands = [("quit", None)]

            def process_command_side_effect(*args, **kwargs):
                debug_engine.game_manager.game_state = GameState.QUIT
                return {"game_over": True}

            mock_cp_inst_debug = MockCP_debug.return_value
            mock_cp_inst_debug.process_command.side_effect = process_command_side_effect

            debug_engine.run()

            self.assertEqual(debug_engine.game_manager.game_state, GameState.GAME_OVER)
            renderer = debug_engine.renderer
            assert renderer is not None
            renderer.cleanup_curses.assert_not_called()  # type: ignore

    def test_run_loop_handles_no_command_from_input(self):
        self.mock_input_handler_instance.handle_input_and_get_command.side_effect = [
            None,
            ("quit", None),
        ]

        def process_command_side_effect(cmd_tuple, *args, **kwargs):
            if cmd_tuple == ("quit", None):
                self.game_engine.game_manager.game_state = GameState.QUIT
            return {"game_over": False}

        self.mock_command_processor_instance.process_command.side_effect = (
            process_command_side_effect
        )

        self.game_engine.debug_mode = False

        with patch("curses.napms") as mock_napms:
            self.game_engine.run()
            mock_napms.assert_not_called()

        self.assertEqual(
            self.mock_input_handler_instance.handle_input_and_get_command.call_count, 2
        )
        self.mock_command_processor_instance.process_command.assert_called_once_with(
            ("quit", None),
            self.game_engine.player,
            self.game_engine.world_maps,
            self.game_engine.message_log,
            (0, 0, -1),
            game_engine=self.game_engine.game_manager,
        )
        self.assertEqual(self.game_engine.game_manager.game_state, GameState.QUIT)
        if not self.game_engine.debug_mode:
            self.mock_renderer_instance.cleanup_curses.assert_called_once()
        else:
            self.mock_renderer_instance.cleanup_curses.assert_not_called()

    def test_game_engine_with_seed_is_deterministic(self):
        # First game engine
        game1 = GameEngine(map_width=20, map_height=10, seed=12345, debug_mode=True)

        # Second game engine with the same seed
        game2 = GameEngine(map_width=20, map_height=10, seed=12345, debug_mode=True)

        # Compare player start positions
        self.assertEqual(game1.player.x, game2.player.x)
        self.assertEqual(game1.player.y, game2.player.y)
        self.assertEqual(game1.player.current_floor_id, game2.player.current_floor_id)

        # Compare winning positions
        self.assertEqual(game1.winning_full_pos, game2.winning_full_pos)

        # Compare number of floors
        self.assertEqual(len(game1.world_maps), len(game2.world_maps))

        # Compare map layouts tile by tile
        for floor_id in game1.world_maps:
            map1 = game1.world_maps[floor_id]
            map2 = game2.world_maps[floor_id]
            for y in range(map1.height):
                for x in range(map1.width):
                    tile1 = map1.get_tile(x, y)
                    tile2 = map2.get_tile(x, y)
                    assert tile1 is not None
                    assert tile2 is not None
                    self.assertEqual(tile1.type, tile2.type)
                    self.assertEqual(tile1.is_portal, tile2.is_portal)
                    self.assertEqual(tile1.portal_to_floor_id, tile2.portal_to_floor_id)


if __name__ == "__main__":
    unittest.main()
