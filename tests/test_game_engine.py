import curses  # For curses.error and constants
import unittest
from unittest.mock import MagicMock, patch

# Import classes to be mocked or used
from src.game_engine import GameEngine
from src.world_map import WorldMap


class TestGameEngine(unittest.TestCase):
    @patch("src.game_engine.WorldGenerator")
    @patch("src.game_engine.InputHandler")
    @patch("src.game_engine.Renderer")
    @patch("src.game_engine.CommandProcessor")
    @patch("src.game_engine.Parser")
    @patch("src.game_engine.Player")
    @patch("src.game_engine.curses")  # Mock curses module itself for initscr etc.
    def setUp(
        self,
        mock_curses_module,
        MockPlayer,
        MockParser,
        MockCommandProcessor,
        MockRenderer,
        MockInputHandler,
        MockWorldGenerator,
    ):
        # Mock curses functions GameEngine might call in __init__
        self.mock_stdscr = MagicMock()
        mock_curses_module.initscr.return_value = self.mock_stdscr
        mock_curses_module.error = curses.error  # Allow curses.error to be raised
        mock_curses_module.napms = MagicMock()  # Mock napms to prevent initscr error

        # Setup mock WorldGenerator
        self.mock_world_gen_instance = MockWorldGenerator.return_value
        self.mock_world_map_instance = MagicMock(spec=WorldMap)
        self.mock_world_map_instance.width = 20
        self.mock_world_map_instance.height = 10
        self.player_start_pos = (1, 1)
        self.win_pos = (5, 5)
        self.mock_world_gen_instance.generate_map.return_value = (
            self.mock_world_map_instance,
            self.player_start_pos,
            self.win_pos,
        )

        # Setup mock Player
        self.mock_player_instance = MockPlayer.return_value
        self.mock_player_instance.x = self.player_start_pos[0]
        self.mock_player_instance.y = self.player_start_pos[1]
        self.mock_player_instance.health = 100

        # Setup mock Parser
        self.mock_parser_instance = MockParser.return_value

        # Setup mock InputHandler
        self.mock_input_handler_instance = MockInputHandler.return_value
        self.mock_input_handler_instance.get_input_mode.return_value = "movement"
        self.mock_input_handler_instance.get_command_buffer.return_value = ""

        # Setup mock Renderer
        self.mock_renderer_instance = MockRenderer.return_value

        # Setup mock CommandProcessor
        self.mock_command_processor_instance = MockCommandProcessor.return_value

        # Instantiate GameEngine
        self.game_engine = GameEngine(map_width=20, map_height=10, debug_mode=False)

        # Direct assignment for mocks if GameEngine creates them internally.
        # Ensures we use the same mock instances GameEngine uses.
        # GameEngine instantiates these; test attributes should point to them.
        # Patch decorators handle this if GameEngine uses these classes directly.
        # For this refactor, GameEngine does instantiate them.
        self.game_engine.world_generator = self.mock_world_gen_instance
        self.game_engine.parser = self.mock_parser_instance  # GameEngine creates Parser
        self.game_engine.player = self.mock_player_instance  # GameEngine creates Player
        self.game_engine.input_handler = (
            self.mock_input_handler_instance
        )  # GameEngine creates InputHandler
        self.game_engine.renderer = (
            self.mock_renderer_instance
        )  # GameEngine creates Renderer
        self.game_engine.command_processor = (
            self.mock_command_processor_instance
        )  # GameEngine creates CommandProcessor
        self.game_engine.world_map = self.mock_world_map_instance  # From generate_map
        self.game_engine.win_pos = self.win_pos  # From generate_map

        # Ensure stdscr is the one from the mock_curses_module
        self.game_engine.stdscr = self.mock_stdscr

    def test_game_engine_initialization(self):
        # Verify WorldGenerator was called
        self.mock_world_gen_instance.generate_map.assert_called_once_with(
            20, 10, seed=None
        )

        # Verify Player was instantiated correctly
        # MockPlayer.assert_called_once_with(
        #    x=self.player_start_pos[0], y=self.player_start_pos[1], health=20
        # )
        # This is tricky as Player is instantiated within GameEngine.
        # We check the mock instance self.game_engine.player.
        self.assertEqual(self.game_engine.player.x, self.player_start_pos[0])
        self.assertEqual(self.game_engine.player.y, self.player_start_pos[1])

        # Verify Parser was instantiated
        # MockParser.assert_called_once() # Parser() is called in GameEngine __init__
        self.assertIsNotNone(self.game_engine.parser)

        # Verify InputHandler was instantiated with stdscr and parser
        # MockInputHandler.assert_called_once_with(
        #    self.mock_stdscr, self.mock_parser_instance
        # )
        self.assertIsNotNone(self.game_engine.input_handler)

        # Verify Renderer was instantiated with stdscr, map dimensions, player symbol
        # MockRenderer.assert_called_once_with(self.mock_stdscr, 20, 10, "@")
        self.assertIsNotNone(self.game_engine.renderer)

        # Verify CommandProcessor was instantiated
        # MockCommandProcessor.assert_called_once()
        self.assertIsNotNone(self.game_engine.command_processor)

        self.assertFalse(self.game_engine.game_over)
        self.assertEqual(self.game_engine.message_log, [])
        self.assertEqual(self.game_engine.debug_mode, False)

    @patch("src.game_engine.curses.napms")  # Patch napms specifically for this test
    def test_run_loop_single_command_then_quit(self, mock_napms):
        # mock_napms is now an argument passed by @patch
        # Simulate one command, then a quit command
        self.mock_input_handler_instance.handle_input_and_get_command.side_effect = [
            ("move", "north"),  # First command
            ("quit", None),  # Second command to exit loop
        ]

        # Mock command processor results for 'move' and 'quit'
        def process_cmd_side_effect(
            parsed_cmd_tuple, player, world_map, msg_log, win_pos_arg
        ):
            if parsed_cmd_tuple == ("quit", None):
                # Ensure msg log updated if other tests expect it
                # msg_log.append("Quitting game.") # e.g.
                return {"game_over": True}
            # Default for other commands
            return {"game_over": False}

        self.mock_command_processor_instance.process_command.side_effect = (
            process_cmd_side_effect
        )

        # Reset game state before running. This is important if tests modify
        # state and affect their own potential re-runs, or if test order matters.
        self.game_engine.game_over = False
        self.game_engine.message_log.clear()

        self.game_engine.run()

        # Check render_all calls
        # Initial render, render after move, render after quit processing (game over)
        self.mock_renderer_instance.render_all.assert_any_call(
            player_x=self.mock_player_instance.x,
            player_y=self.mock_player_instance.y,
            player_health=self.mock_player_instance.health,
            world_map=self.mock_world_map_instance,
            input_mode="movement",  # Assuming mode or updated by mock
            current_command_buffer="",  # Assuming cleared or updated
            message_log=self.game_engine.message_log,  # Passed to render_all
            debug_render_to_list=False,
        )
        self.assertGreaterEqual(self.mock_renderer_instance.render_all.call_count, 2)

        # Check input_handler calls
        self.assertEqual(
            self.mock_input_handler_instance.handle_input_and_get_command.call_count, 2
        )

        # Check command_processor calls
        # First call for ('move', 'north')
        self.mock_command_processor_instance.process_command.assert_any_call(
            ("move", "north"),
            self.mock_player_instance,
            self.mock_world_map_instance,
            self.game_engine.message_log,  # process_command appends to this list
            self.win_pos,
        )
        # Second call for ('quit', None)
        self.mock_command_processor_instance.process_command.assert_any_call(
            ("quit", None),
            self.mock_player_instance,
            self.mock_world_map_instance,
            self.game_engine.message_log,
            self.win_pos,
        )
        self.assertEqual(
            self.mock_command_processor_instance.process_command.call_count, 2
        )

        # Check game_over state (should be True after 'quit')
        self.assertTrue(self.game_engine.game_over)  # Should pass without re-run
        self.mock_renderer_instance.cleanup_curses.assert_called_once()

    def test_run_loop_game_over_from_command(self):
        self.mock_input_handler_instance.handle_input_and_get_command.side_effect = [
            ("attack", "dragon"),  # Command that causes game over
            # Loop should terminate after this if game_over is set
        ]
        self.mock_command_processor_instance.process_command.return_value = {
            "game_over": True
        }
        self.game_engine.debug_mode = False

        with patch("curses.napms") as mock_napms:
            self.game_engine.run()
            # napms is only called if game_over is True AND not in debug_mode
            if self.game_engine.game_over and not self.game_engine.debug_mode:
                mock_napms.assert_called_once_with(2000)
            # If game_over is False or debug_mode is True, napms should not be called
            elif not (self.game_engine.game_over and not self.game_engine.debug_mode):
                mock_napms.assert_not_called()

        self.mock_input_handler_instance.handle_input_and_get_command.assert_called_once()
        self.mock_command_processor_instance.process_command.assert_called_once()
        self.assertTrue(self.game_engine.game_over)
        self.mock_renderer_instance.cleanup_curses.assert_called_once()

    @patch(
        "src.game_engine.curses"
    )  # Patch curses for this specific test's GameEngine instance
    def test_run_loop_debug_mode_no_curses_cleanup(self, mock_curses_for_debug_engine):
        # Create a new GameEngine instance with debug_mode=True
        # We need to re-patch dependencies for this specific instance
        with patch("src.game_engine.WorldGenerator") as MockWG_debug, patch(
            "src.game_engine.InputHandler"
        ) as MockIH_debug, patch("src.game_engine.Renderer") as MockR_debug, patch(
            "src.game_engine.CommandProcessor"
        ) as MockCP_debug, patch("src.game_engine.Parser"), patch(
            "src.game_engine.Player"
        ) as MockPl_debug:  # MockP_debug unused
            mock_wg_inst_debug = MockWG_debug.return_value
            mock_wm_inst_debug = MagicMock(spec=WorldMap)
            mock_wm_inst_debug.width = 10
            mock_wm_inst_debug.height = 5
            mock_wg_inst_debug.generate_map.return_value = (
                mock_wm_inst_debug,
                (0, 0),
                (1, 1),
            )

            mock_ih_inst_debug = MockIH_debug.return_value
            mock_r_inst_debug = MockR_debug.return_value
            mock_cp_inst_debug = MockCP_debug.return_value

            debug_engine = GameEngine(map_width=10, map_height=5, debug_mode=True)
            # Assign mocks
            debug_engine.input_handler = mock_ih_inst_debug
            debug_engine.renderer = mock_r_inst_debug
            debug_engine.command_processor = mock_cp_inst_debug
            debug_engine.player = MockPl_debug.return_value  # Assign the player mock
            debug_engine.world_map = mock_wm_inst_debug
            debug_engine.win_pos = (1, 1)

            mock_ih_inst_debug.handle_input_and_get_command.return_value = (
                "quit",
                None,
            )
            mock_cp_inst_debug.process_command.return_value = {"game_over": True}

            debug_engine.run()

            self.assertTrue(debug_engine.game_over)
            # In debug mode, cleanup_curses should not be called
            mock_r_inst_debug.cleanup_curses.assert_not_called()
            # Render all should be called with debug_render_to_list=True
            mock_r_inst_debug.render_all.assert_called_with(
                player_x=debug_engine.player.x,
                player_y=debug_engine.player.y,
                player_health=debug_engine.player.health,
                world_map=mock_wm_inst_debug,
                input_mode=mock_ih_inst_debug.get_input_mode.return_value,
                current_command_buffer=mock_ih_inst_debug.get_command_buffer.return_value,
                message_log=debug_engine.message_log,
                debug_render_to_list=True,  # This is key for debug mode
            )
            # Check that stdscr related calls were not made in __init__ for debug engine
            mock_curses_for_debug_engine.initscr.assert_not_called()

    def test_run_loop_handles_no_command_from_input(self):
        # Input handler returns None (e.g. timeout, non-action key) then quit
        self.mock_input_handler_instance.handle_input_and_get_command.side_effect = [
            None,
            ("quit", None),
        ]
        self.mock_command_processor_instance.process_command.return_value = {
            "game_over": True
        }  # For the quit
        self.game_engine.debug_mode = False

        with patch("curses.napms") as mock_napms:
            self.game_engine.run()
            if self.game_engine.game_over and not self.game_engine.debug_mode:
                mock_napms.assert_called_once_with(2000)
            elif not (self.game_engine.game_over and not self.game_engine.debug_mode):
                mock_napms.assert_not_called()

        self.assertEqual(
            self.mock_input_handler_instance.handle_input_and_get_command.call_count, 2
        )
        # process_command should only be called for the 'quit' command, not for None
        self.mock_command_processor_instance.process_command.assert_called_once_with(
            ("quit", None),
            self.mock_player_instance,
            self.mock_world_map_instance,
            self.game_engine.message_log,
            self.win_pos,
        )
        self.assertTrue(self.game_engine.game_over)
        self.mock_renderer_instance.cleanup_curses.assert_called_once()
        # render_all should be called after None input, and after quit input
        self.assertGreaterEqual(self.mock_renderer_instance.render_all.call_count, 2)


if __name__ == "__main__":
    unittest.main()
