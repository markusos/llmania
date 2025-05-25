import curses  # For curses constants and init_pair
import unittest
from unittest.mock import MagicMock, call, patch

# Assuming src is in PYTHONPATH or tests are run in a way that src can be imported
from src.renderer import Renderer


# Dummy/mock classes for dependencies if needed
class MockWorldMap:
    def __init__(self, width, height, tiles=None):
        self.width = width
        self.height = height
        self.grid = (
            tiles if tiles else [[None for _ in range(width)] for _ in range(height)]
        )

    def get_tile(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.grid[y][x]
        return None


class MockTile:
    def __init__(self, symbol, display_type="floor"):
        self.symbol = symbol
        self.display_type = display_type

    def get_display_info(self):
        return self.symbol, self.display_type


class TestRenderer(unittest.TestCase):
    def setUp(self):
        # Mock stdscr for most tests
        self.mock_stdscr = MagicMock()

        # Patch curses functions that are called directly
        self.start_color_patcher = patch("curses.start_color")
        self.mock_start_color = self.start_color_patcher.start()
        self.addCleanup(self.start_color_patcher.stop)

        self.noecho_patcher = patch("curses.noecho")
        self.mock_noecho = self.noecho_patcher.start()
        self.addCleanup(self.noecho_patcher.stop)

        self.cbreak_patcher = patch("curses.cbreak")
        self.mock_cbreak = self.cbreak_patcher.start()
        self.addCleanup(self.cbreak_patcher.stop)

        self.curs_set_patcher = patch("curses.curs_set")
        self.mock_curs_set = self.curs_set_patcher.start()
        self.addCleanup(self.curs_set_patcher.stop)

        self.init_pair_patcher = patch("curses.init_pair")
        self.mock_init_pair = self.init_pair_patcher.start()
        self.addCleanup(self.init_pair_patcher.stop)

        self.endwin_patcher = patch("curses.endwin")
        self.mock_endwin = self.endwin_patcher.start()
        self.addCleanup(self.endwin_patcher.stop)

        # Common parameters for Renderer
        self.map_width = 10
        self.map_height = 5
        self.player_symbol = "@"

    def test_init_with_stdscr(self):
        renderer = Renderer(
            self.mock_stdscr, self.map_width, self.map_height, self.player_symbol
        )

        self.mock_start_color.assert_called_once()
        self.mock_noecho.assert_called_once()
        self.mock_cbreak.assert_called_once()
        self.mock_stdscr.keypad.assert_called_once_with(True)
        self.mock_curs_set.assert_called_once_with(0)

        expected_init_pair_calls = [
            call(1, curses.COLOR_BLACK, curses.COLOR_GREEN),  # Floor
            call(2, curses.COLOR_BLACK, curses.COLOR_WHITE),  # Wall
            call(3, curses.COLOR_BLACK, curses.COLOR_GREEN),  # Player
            call(4, curses.COLOR_BLACK, curses.COLOR_GREEN),  # Monster
            call(5, curses.COLOR_BLACK, curses.COLOR_GREEN),  # Item
            call(6, curses.COLOR_WHITE, curses.COLOR_BLACK),  # Default text
        ]
        self.mock_init_pair.assert_has_calls(expected_init_pair_calls, any_order=False)
        self.assertEqual(renderer.FLOOR_COLOR_PAIR, 1)

    def test_init_debug_mode_stdscr_none(self):
        # Reset mocks as they might have been called by other tests
        self.mock_start_color.reset_mock()
        self.mock_noecho.reset_mock()
        self.mock_cbreak.reset_mock()
        self.mock_curs_set.reset_mock()
        self.mock_init_pair.reset_mock()

        renderer = Renderer(None, self.map_width, self.map_height, self.player_symbol)

        self.mock_start_color.assert_not_called()
        self.mock_noecho.assert_not_called()
        self.mock_cbreak.assert_not_called()
        # self.mock_stdscr.keypad is not applicable here as stdscr is None
        self.mock_curs_set.assert_not_called()
        self.mock_init_pair.assert_not_called()

        # Check default color pair values in debug mode
        self.assertEqual(renderer.FLOOR_COLOR_PAIR, 0)
        self.assertEqual(renderer.DEFAULT_TEXT_COLOR_PAIR, 0)

    def test_render_all_debug_render_to_list(self):
        renderer = Renderer(
            None, self.map_width, self.map_height, self.player_symbol
        )  # stdscr is None for this test

        mock_map_tiles = [
            [MockTile(".") for _ in range(self.map_width)]
            for _ in range(self.map_height)
        ]
        mock_map_tiles[2][3] = MockTile("#", "wall")
        world_map = MockWorldMap(self.map_width, self.map_height, tiles=mock_map_tiles)

        player_x, player_y = 1, 1
        player_health = 100
        input_mode = "movement"
        current_command_buffer = ""
        message_log = ["Msg1", "Msg2"]

        output_buffer = renderer.render_all(
            player_x,
            player_y,
            player_health,
            world_map,
            input_mode,
            current_command_buffer,
            message_log,
            debug_render_to_list=True,
        )

        self.assertEqual(
            len(output_buffer), self.map_height + 1 + 1 + len(message_log)
        )  # map + HP + mode + messages
        self.assertEqual(output_buffer[0], "..........")
        self.assertEqual(
            output_buffer[1], f".{self.player_symbol}........"
        )  # Player at 1,1
        self.assertEqual(output_buffer[2], "...#......")  # Wall at 2,3
        self.assertEqual(output_buffer[self.map_height], f"HP: {player_health}")
        self.assertEqual(
            output_buffer[self.map_height + 1], f"MODE: {input_mode.upper()}"
        )
        self.assertEqual(output_buffer[self.map_height + 2], "Msg1")
        self.assertEqual(output_buffer[self.map_height + 3], "Msg2")

    def test_render_all_debug_render_to_list_command_mode(self):
        renderer = Renderer(None, self.map_width, self.map_height, self.player_symbol)
        world_map = MockWorldMap(
            self.map_width,
            self.map_height,
            tiles=[
                [MockTile(".") for _ in range(self.map_width)]
                for _ in range(self.map_height)
            ],
        )

        input_mode = "command"
        current_command_buffer = "test cmd"
        message_log = []

        output_buffer = renderer.render_all(
            0,
            0,
            100,
            world_map,
            input_mode,
            current_command_buffer,
            message_log,
            debug_render_to_list=True,
        )
        # map + HP + mode + command_buffer + messages
        self.assertEqual(
            len(output_buffer), self.map_height + 1 + 1 + 1 + len(message_log)
        )
        self.assertEqual(
            output_buffer[self.map_height + 1], f"MODE: {input_mode.upper()}"
        )
        self.assertEqual(
            output_buffer[self.map_height + 2], f"> {current_command_buffer}"
        )

    @patch("curses.LINES", 20)  # Mock curses.LINES
    @patch("curses.COLS", 80)  # Mock curses.COLS
    def test_render_all_curses_mode(self, mock_cols, mock_lines):
        renderer = Renderer(
            self.mock_stdscr, self.map_width, self.map_height, self.player_symbol
        )
        world_map = MockWorldMap(
            self.map_width,
            self.map_height,
            tiles=[
                [MockTile(".") for _ in range(self.map_width)]
                for _ in range(self.map_height)
            ],
        )

        player_x, player_y = 1, 1
        player_health = 90
        input_mode = "movement"
        current_command_buffer = ""
        message_log = ["Hello"]

        renderer.render_all(
            player_x,
            player_y,
            player_health,
            world_map,
            input_mode,
            current_command_buffer,
            message_log,
            debug_render_to_list=False,
        )

        self.mock_stdscr.clear.assert_called_once()
        self.mock_stdscr.refresh.assert_called_once()

        # Check a few addstr calls - example: player
        # Note: y_map_idx, current_screen_x, char_to_draw, color_attribute
        # Player at (1,1)
        self.mock_stdscr.addstr.assert_any_call(
            1, 1, self.player_symbol, curses.color_pair(renderer.PLAYER_COLOR_PAIR)
        )
        # A floor tile at (0,0)
        self.mock_stdscr.addstr.assert_any_call(
            0, 0, ".", curses.color_pair(renderer.FLOOR_COLOR_PAIR)
        )

        # UI elements - positions depend on map_height and mocked curses.LINES
        # map_height = 5, UI_LINES_BUFFER = 4, max_y_curses_rows = min(5, 20-4=16) = 5
        # hp_line_y = 5
        # mode_line_y = 6
        # message_start_y = 7
        self.mock_stdscr.addstr.assert_any_call(
            5,
            0,
            f"HP: {player_health}",
            curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR),
        )
        self.mock_stdscr.addstr.assert_any_call(
            6,
            0,
            f"MODE: {input_mode.upper()}",
            curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR),
        )
        self.mock_stdscr.addstr.assert_any_call(
            7, 0, "Hello", curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR)
        )

    def test_render_all_curses_mode_stdscr_none(self):
        renderer = Renderer(
            None, self.map_width, self.map_height, self.player_symbol
        )  # stdscr is None
        world_map = MockWorldMap(self.map_width, self.map_height)

        # Call render_all with debug_render_to_list=False (which is default)
        # It should not attempt any curses operations and not crash
        try:
            renderer.render_all(0, 0, 100, world_map, "movement", "", [])
        except Exception as e:
            self.fail(f"render_all crashed with stdscr=None: {e}")

        # Ensure no curses screen operations were called if stdscr is None
        self.mock_stdscr.clear.assert_not_called()
        self.mock_stdscr.refresh.assert_not_called()
        self.mock_stdscr.addstr.assert_not_called()

    def test_cleanup_curses_with_stdscr(self):
        renderer = Renderer(
            self.mock_stdscr, self.map_width, self.map_height, self.player_symbol
        )
        renderer.cleanup_curses()

        self.mock_stdscr.keypad.assert_called_with(False) # This is from the first call.

        # Patch global curses functions for this specific test's call to cleanup_curses
        with patch("curses.echo") as mock_echo, \
             patch('curses.nocbreak') as mock_nocbreak, \
             patch('curses.endwin') as mock_endwin_local: # Patch endwin locally for this test
            
            renderer.cleanup_curses() # Call it INSIDE the with block

            mock_echo.assert_called_once()
            mock_nocbreak.assert_called_once()
            mock_endwin_local.assert_called_once() # Assert the local mock_endwin

    def test_cleanup_curses_stdscr_none(self):
        renderer = Renderer(None, self.map_width, self.map_height, self.player_symbol)

        with patch("curses.echo") as mock_echo, patch(
            "curses.nocbreak"
        ) as mock_nocbreak:
            try:
                renderer.cleanup_curses()
            except Exception as e:
                self.fail(f"cleanup_curses crashed with stdscr=None: {e}")

            self.mock_stdscr.keypad.assert_not_called()  # stdscr is None
            mock_echo.assert_not_called()
            mock_nocbreak.assert_not_called()
            self.mock_endwin.assert_not_called()


if __name__ == "__main__":
    unittest.main()
