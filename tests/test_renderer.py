import curses  # For curses constants and init_pair
import unittest  # unittest first
from unittest.mock import MagicMock, call, patch

from src.message_log import MessageLog
from src.renderer import Renderer


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
        self.is_explored = True
        # Add portal attributes needed by Renderer if path rendering involves portals
        self.is_portal = False
        self.portal_to_floor_id = None
        self.item = None  # For display logic
        self.monster = None  # For display logic

    def get_display_info(self, apply_fog: bool = False):
        if apply_fog and not self.is_explored:
            return " ", "fog"
        # Simplified for mock:
        if self.monster:
            return "M", "monster"
        if self.item:
            return "$", "item"  # Assuming '$' for items
        if self.is_portal:
            return "P", "portal"  # Assuming 'P' for portals
        return self.symbol, self.display_type


class TestRenderer(unittest.TestCase):
    def setUp(self):
        self.mock_stdscr = MagicMock()
        self.initscr_patcher = patch("curses.initscr")
        self.mock_initscr = self.initscr_patcher.start()
        self.mock_initscr.return_value = self.mock_stdscr
        self.addCleanup(self.initscr_patcher.stop)

        self.echo_patcher = patch("curses.echo")
        self.mock_echo = self.echo_patcher.start()
        self.addCleanup(self.echo_patcher.stop)

        self.nocbreak_patcher = patch("curses.nocbreak")
        self.mock_nocbreak = self.nocbreak_patcher.start()
        self.addCleanup(self.nocbreak_patcher.stop)

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

        self.map_width = 10
        self.map_height = 5
        self.player_symbol = "@"

    def test_init_with_stdscr(self):
        renderer = Renderer(
            debug_mode=False,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        self.assertEqual(renderer.stdscr, self.mock_stdscr)
        self.mock_start_color.assert_called_once()
        self.mock_noecho.assert_called_once()
        self.mock_cbreak.assert_called_once()
        self.mock_stdscr.keypad.assert_called_once_with(True)
        self.mock_curs_set.assert_called_once_with(0)
        expected_init_pair_calls = [
            call(1, curses.COLOR_BLACK, curses.COLOR_GREEN),
            call(2, curses.COLOR_BLACK, curses.COLOR_WHITE),
            call(3, curses.COLOR_BLACK, curses.COLOR_GREEN),
            call(4, curses.COLOR_RED, curses.COLOR_GREEN),
            call(5, curses.COLOR_YELLOW, curses.COLOR_GREEN),
            call(6, curses.COLOR_WHITE, curses.COLOR_BLACK),
        ]
        self.mock_init_pair.assert_has_calls(expected_init_pair_calls, any_order=False)
        self.assertEqual(renderer.FLOOR_COLOR_PAIR, 1)
        self.mock_init_pair.assert_any_call(7, curses.COLOR_BLUE, curses.COLOR_GREEN)
        self.assertEqual(renderer.PATH_COLOR_PAIR, 7)

    def test_init_debug_mode_stdscr_none(self):
        self.mock_start_color.reset_mock()
        self.mock_noecho.reset_mock()
        self.mock_cbreak.reset_mock()
        self.mock_curs_set.reset_mock()
        self.mock_init_pair.reset_mock()

        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        self.assertIsNone(renderer.stdscr)
        self.mock_start_color.assert_not_called()
        self.mock_noecho.assert_not_called()
        self.mock_cbreak.assert_not_called()
        self.mock_curs_set.assert_not_called()
        self.mock_init_pair.assert_not_called()
        self.assertEqual(renderer.FLOOR_COLOR_PAIR, 0)
        self.assertEqual(renderer.DEFAULT_TEXT_COLOR_PAIR, 0)

    def test_render_all_debug_render_to_list(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
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
        mock_message_log = MagicMock(spec=MessageLog)
        test_messages = ["Msg1", "Msg2"]
        mock_message_log.get_messages.return_value = test_messages
        mock_message_log.max_messages = 5

        output_buffer = renderer.render_all(
            player_x,
            player_y,
            player_health,
            world_map,
            input_mode,
            current_command_buffer,
            mock_message_log,
            current_floor_id=0,
            debug_render_to_list=True,
        )
        self.assertEqual(
            len(output_buffer), self.map_height + 1 + 1 + 1 + len(test_messages)
        )
        self.assertEqual(output_buffer[0], "..........")
        self.assertEqual(output_buffer[1], f".{self.player_symbol}........")
        self.assertEqual(output_buffer[2], "...#......")

        hp_line_idx = self.map_height
        floor_line_idx = hp_line_idx + 1
        mode_line_idx = floor_line_idx + 1
        msg_start_idx = mode_line_idx + 1

        self.assertEqual(output_buffer[hp_line_idx], f"HP: {player_health}")
        self.assertEqual(output_buffer[floor_line_idx], "Floor: 0")
        self.assertEqual(output_buffer[mode_line_idx], f"MODE: {input_mode.upper()}")
        self.assertEqual(output_buffer[msg_start_idx], "Msg1")
        self.assertEqual(output_buffer[msg_start_idx + 1], "Msg2")
        mock_message_log.get_messages.assert_called_once()

    def test_render_all_debug_render_to_list_command_mode(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
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
        mock_message_log = MagicMock(spec=MessageLog)
        mock_message_log.get_messages.return_value = []
        mock_message_log.max_messages = 5

        output_buffer = renderer.render_all(
            0,
            0,
            100,
            world_map,
            input_mode,
            current_command_buffer,
            mock_message_log,
            current_floor_id=0,
            debug_render_to_list=True,
        )
        expected_len = (
            self.map_height
            + 1
            + 1
            + 1
            + 1
            + len(mock_message_log.get_messages.return_value)
        )
        self.assertEqual(len(output_buffer), expected_len)

        hp_line_idx = self.map_height
        floor_line_idx = hp_line_idx + 1
        mode_line_idx = floor_line_idx + 1
        cmd_buffer_line_idx = mode_line_idx + 1

        self.assertEqual(output_buffer[hp_line_idx], "HP: 100")
        self.assertEqual(output_buffer[floor_line_idx], "Floor: 0")
        self.assertEqual(output_buffer[mode_line_idx], f"MODE: {input_mode.upper()}")
        self.assertEqual(
            output_buffer[cmd_buffer_line_idx], f"> {current_command_buffer}"
        )
        mock_message_log.get_messages.assert_called_once()

    def test_render_all_curses_mode(self):
        original_lines = getattr(curses, "LINES", None)
        original_cols = getattr(curses, "COLS", None)
        try:
            curses.LINES = 20
            curses.COLS = 80
            with patch("curses.color_pair", return_value=0):
                renderer = Renderer(
                    debug_mode=False,
                    map_width=self.map_height,  # Corrected: should be self.map_width for consistency
                    map_height=self.map_height,
                    player_symbol=self.player_symbol,
                )
                # Re-assign map_width for renderer instance if it was wrong in constructor
                renderer.map_width = self.map_width

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
                mock_message_log = MagicMock(spec=MessageLog)
                test_messages = ["Hello"]
                mock_message_log.get_messages.return_value = test_messages
                mock_message_log.max_messages = 5

                renderer.render_all(
                    player_x,
                    player_y,
                    player_health,
                    world_map,
                    input_mode,
                    current_command_buffer,
                    mock_message_log,
                    current_floor_id=0,
                    debug_render_to_list=False,
                )
                self.mock_stdscr.clear.assert_called_once()
                self.mock_stdscr.refresh.assert_called_once()
                self.mock_stdscr.addstr.assert_any_call(
                    1,
                    1,
                    self.player_symbol,
                    curses.color_pair(renderer.PLAYER_COLOR_PAIR),
                )
                self.mock_stdscr.addstr.assert_any_call(
                    0, 0, ".", curses.color_pair(renderer.FLOOR_COLOR_PAIR)
                )
                hp_line_y = self.map_height
                floor_line_y = hp_line_y + 1
                mode_line_y = floor_line_y + 1
                message_start_y = mode_line_y + 1

                self.mock_stdscr.addstr.assert_any_call(
                    hp_line_y,
                    0,
                    f"HP: {player_health}",
                    curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR),
                )
                self.mock_stdscr.addstr.assert_any_call(
                    floor_line_y,
                    0,
                    "Floor: 0",
                    curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR),
                )
                self.mock_stdscr.addstr.assert_any_call(
                    mode_line_y,
                    0,
                    f"MODE: {input_mode.upper()}",
                    curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR),
                )
                self.mock_stdscr.addstr.assert_any_call(
                    message_start_y,
                    0,
                    "Hello",
                    curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR),
                )
                mock_message_log.get_messages.assert_called_once()
        finally:
            if original_lines is not None:
                curses.LINES = original_lines
            elif hasattr(curses, "LINES"):
                delattr(curses, "LINES")
            if original_cols is not None:
                curses.COLS = original_cols
            elif hasattr(curses, "COLS"):
                delattr(curses, "COLS")

    def test_render_all_curses_mode_stdscr_none(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        world_map = MockWorldMap(self.map_width, self.map_height)
        mock_message_log = MagicMock(spec=MessageLog)
        mock_message_log.get_messages.return_value = []
        mock_message_log.max_messages = 5

        try:
            renderer.render_all(
                0,
                0,
                100,
                world_map,
                "movement",
                "",
                mock_message_log,
                current_floor_id=0,
            )
        except Exception as e:
            self.fail(f"render_all crashed with stdscr=None: {e}")

        self.mock_stdscr.clear.assert_not_called()
        self.mock_stdscr.refresh.assert_not_called()
        self.mock_stdscr.addstr.assert_not_called()

    def test_cleanup_curses_with_stdscr(self):
        renderer = Renderer(
            debug_mode=False,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        self.mock_stdscr.keypad.reset_mock()
        self.mock_echo.reset_mock()
        self.mock_nocbreak.reset_mock()
        self.mock_endwin.reset_mock()

        renderer.cleanup_curses()

        self.mock_stdscr.keypad.assert_called_once_with(False)
        self.mock_echo.assert_called_once()
        self.mock_nocbreak.assert_called_once()
        self.mock_endwin.assert_called_once()

    def test_cleanup_curses_stdscr_none(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        with patch("curses.echo") as mock_echo, patch(
            "curses.nocbreak"
        ) as mock_nocbreak:
            try:
                renderer.cleanup_curses()
            except Exception as e:
                self.fail(f"cleanup_curses crashed with stdscr=None: {e}")
            self.mock_stdscr.keypad.assert_not_called()
            mock_echo.assert_not_called()
            mock_nocbreak.assert_not_called()
            self.mock_endwin.assert_not_called()

    def test_render_all_debug_with_ai_path(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        mock_map_tiles = [
            [MockTile(".") for _ in range(self.map_width)]
            for _ in range(self.map_height)
        ]
        world_map = MockWorldMap(self.map_width, self.map_height, tiles=mock_map_tiles)
        player_x, player_y = 0, 0
        ai_path_to_render = [(1, 0, 0), (2, 0, 0), (2, 1, 0)]
        mock_message_log = MagicMock(spec=MessageLog)
        mock_message_log.get_messages.return_value = []
        mock_message_log.max_messages = 5

        output_buffer = renderer.render_all(
            player_x,
            player_y,
            100,
            world_map,
            "movement",
            "",
            mock_message_log,
            current_floor_id=0,
            debug_render_to_list=True,
            ai_path=ai_path_to_render,
        )
        self.assertEqual(output_buffer[0], f"{self.player_symbol}**.......")
        self.assertEqual(output_buffer[1], "..x.......")
        for i in range(2, self.map_height):
            self.assertEqual(output_buffer[i], "..........")
        self.assertIn("HP: 100", output_buffer)
        self.assertIn("MODE: MOVEMENT", output_buffer)

    def test_render_all_debug_ai_path_player_on_path(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        mock_map_tiles = [
            [MockTile(".") for _ in range(self.map_width)]
            for _ in range(self.map_height)
        ]
        world_map = MockWorldMap(self.map_width, self.map_height, tiles=mock_map_tiles)
        player_x, player_y = 1, 0
        ai_path_to_render = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        mock_message_log = MagicMock(spec=MessageLog)
        mock_message_log.get_messages.return_value = []

        output_buffer = renderer.render_all(
            player_x,
            player_y,
            100,
            world_map,
            "movement",
            "",
            mock_message_log,
            current_floor_id=0,
            debug_render_to_list=True,
            ai_path=ai_path_to_render,
        )
        self.assertEqual(output_buffer[0], f"*{self.player_symbol}x.......")

    def test_render_all_debug_ai_path_destination_is_player_loc(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        mock_map_tiles = [
            [MockTile(".") for _ in range(self.map_width)]
            for _ in range(self.map_height)
        ]
        world_map = MockWorldMap(self.map_width, self.map_height, tiles=mock_map_tiles)
        player_x, player_y = 2, 0
        ai_path_to_render = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        mock_message_log = MagicMock(spec=MessageLog)
        mock_message_log.get_messages.return_value = []

        output_buffer = renderer.render_all(
            player_x,
            player_y,
            100,
            world_map,
            "movement",
            "",
            mock_message_log,
            current_floor_id=0,
            debug_render_to_list=True,
            ai_path=ai_path_to_render,
        )
        self.assertEqual(output_buffer[0], f"**{self.player_symbol}.......")

    def test_render_all_debug_displays_floor_id(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        world_map = MockWorldMap(
            self.map_width,
            self.map_height,
            tiles=[
                [MockTile(".") for _ in range(self.map_width)]
                for _ in range(self.map_height)
            ],
        )
        mock_message_log = MagicMock(spec=MessageLog)
        mock_message_log.get_messages.return_value = []

        current_floor_to_test = 5
        output_buffer = renderer.render_all(
            0,
            0,
            100,
            world_map,
            "movement",
            "",
            mock_message_log,
            current_floor_id=current_floor_to_test,
            debug_render_to_list=True,
        )

        hp_line_idx = self.map_height
        floor_line_idx = hp_line_idx + 1
        self.assertEqual(
            output_buffer[floor_line_idx], f"Floor: {current_floor_to_test}"
        )

    def test_render_all_curses_displays_floor_id(self):
        original_lines = getattr(curses, "LINES", None)
        original_cols = getattr(curses, "COLS", None)
        try:
            curses.LINES = 20
            curses.COLS = 80
            with patch("curses.color_pair", return_value=0):
                renderer = Renderer(
                    debug_mode=False,
                    map_width=self.map_width,
                    map_height=self.map_height,
                    player_symbol=self.player_symbol,
                )
                world_map = MockWorldMap(
                    self.map_width,
                    self.map_height,
                    tiles=[
                        [MockTile(".") for _ in range(self.map_width)]
                        for _ in range(self.map_height)
                    ],
                )
                mock_message_log = MagicMock(spec=MessageLog)
                mock_message_log.get_messages.return_value = ["Test msg"]
                mock_message_log.max_messages = 5

                current_floor_to_test = 3
                renderer.render_all(
                    0,
                    0,
                    100,
                    world_map,
                    "movement",
                    "",
                    mock_message_log,
                    current_floor_id=current_floor_to_test,
                    debug_render_to_list=False,
                )

                hp_line_y = self.map_height
                floor_line_y = hp_line_y + 1

                self.mock_stdscr.addstr.assert_any_call(
                    floor_line_y,
                    0,
                    f"Floor: {current_floor_to_test}",
                    curses.color_pair(renderer.DEFAULT_TEXT_COLOR_PAIR),
                )
        finally:
            if original_lines is not None:
                curses.LINES = original_lines
            elif hasattr(curses, "LINES"):
                delattr(curses, "LINES")
            if original_cols is not None:
                curses.COLS = original_cols
            elif hasattr(curses, "COLS"):
                delattr(curses, "COLS")

    def test_render_all_debug_ai_path_empty(self):
        renderer = Renderer(
            debug_mode=True,
            map_width=self.map_width,
            map_height=self.map_height,
            player_symbol=self.player_symbol,
        )
        mock_map_tiles = [
            [MockTile(".") for _ in range(self.map_width)]
            for _ in range(self.map_height)
        ]
        world_map = MockWorldMap(self.map_width, self.map_height, tiles=mock_map_tiles)
        player_x, player_y = 0, 0
        ai_path_to_render = []

        mock_message_log = MagicMock(spec=MessageLog)
        mock_message_log.get_messages.return_value = []

        output_buffer = renderer.render_all(
            player_x,
            player_y,
            100,
            world_map,
            "movement",
            "",
            mock_message_log,
            current_floor_id=0,
            debug_render_to_list=True,
            ai_path=ai_path_to_render,
        )
        self.assertEqual(output_buffer[0], f"{self.player_symbol}.........")
        self.assertEqual(output_buffer[1], "..........")


if __name__ == "__main__":
    unittest.main()
