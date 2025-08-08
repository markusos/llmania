from unittest.mock import MagicMock, patch

import pytest

from src.input_mode import InputMode
from src.message_log import MessageLog
from src.renderer import Renderer
from src.tile import Tile
from src.world_map import WorldMap


class MockTile(Tile):
    def __init__(
        self,
        tile_type="floor",
        is_explored=True,
        item=None,
        monster=None,
        is_portal=False,
        portal_to_floor_id=None,
    ):
        super().__init__(tile_type)
        (
            self.type,
            self.is_explored,
            self.item,
            self.monster,
            self.is_portal,
            self.portal_to_floor_id,
        ) = tile_type, is_explored, item, monster, is_portal, portal_to_floor_id
        if is_portal and portal_to_floor_id is None:
            self.portal_to_floor_id = 0

    def get_display_info(self, apply_fog=False):
        if apply_fog and not self.is_explored:
            return " ", "fog"
        if self.monster:
            return "M", "monster"
        if self.item:
            return "$", "item"
        if self.is_portal:
            return "▢", "portal"
        return (
            ("#", "wall")
            if self.type == "wall"
            else (".", "floor")
            if self.type == "floor"
            else ("?", "unknown")
        )


class MockWorldMap(WorldMap):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.grid = [[MockTile("floor") for _ in range(width)] for _ in range(height)]

    def get_tile(self, x, y):
        return self.grid[y][x] if 0 <= x < self.width and 0 <= y < self.height else None


@pytest.fixture
def setup_renderer():
    renderer = Renderer(debug_mode=True, map_width=10, map_height=5, player_symbol="@")
    world_map = MockWorldMap(10, 5)
    player_pos = (5, 2)
    player_health = 100
    message_log = MessageLog()
    current_floor_id = 0
    input_mode = InputMode.MOVEMENT
    current_command_buffer = ""
    return (
        renderer,
        world_map,
        player_pos,
        player_health,
        message_log,
        current_floor_id,
        input_mode,
        current_command_buffer,
    )


def test_render_all_basic_structure(setup_renderer):
    (
        renderer,
        world_map,
        player_pos,
        player_health,
        message_log,
        current_floor_id,
        input_mode,
        current_command_buffer,
    ) = setup_renderer
    message_log.add_message("Msg1")
    message_log.add_message("Msg2")

    output = renderer.render_all(
        player_pos[0],
        player_pos[1],
        player_health,
        world_map,
        input_mode,
        current_command_buffer,
        message_log,
        current_floor_id,
        True,
    )

    assert isinstance(output, list)
    map_output_section = output[: world_map.height]
    player_row_from_map = map_output_section[player_pos[1]]
    assert renderer.player_symbol in player_row_from_map

    ui_and_message_section = "\n".join(output[world_map.height :])
    assert f"HP: {player_health}" in ui_and_message_section
    assert f"Floor: {current_floor_id}" in ui_and_message_section
    assert f"MODE: {input_mode.name.upper()}" in ui_and_message_section
    assert "Msg1" in ui_and_message_section
    assert "Msg2" in ui_and_message_section


def test_render_ai_mode_info(setup_renderer):
    (
        renderer,
        world_map,
        player_pos,
        player_health,
        message_log,
        current_floor_id,
        input_mode,
        current_command_buffer,
    ) = setup_renderer
    ai_state = "Exploring"

    output = renderer.render_all(
        player_pos[0],
        player_pos[1],
        player_health,
        world_map,
        input_mode,
        current_command_buffer,
        message_log,
        current_floor_id,
        debug_render_to_list=True,
        ai_state=ai_state,
    )

    assert isinstance(output, list)
    ui_section = "\n".join(output[world_map.height :])
    assert f"AI State: {ai_state}" in ui_section
    assert f"Position: ({player_pos[0]}, {player_pos[1]})" in ui_section


def test_render_fog_of_war(setup_renderer):
    (
        renderer,
        world_map,
        _,
        player_health,
        message_log,
        current_floor_id,
        input_mode,
        current_command_buffer,
    ) = setup_renderer
    world_map.grid[0][0].is_explored = True
    for y_coord in range(world_map.height):
        for x_coord in range(world_map.width):
            if (x_coord, y_coord) != (0, 0):
                world_map.grid[y_coord][x_coord].is_explored = False

    output = renderer.render_all(
        0,
        0,
        player_health,
        world_map,
        input_mode,
        current_command_buffer,
        message_log,
        current_floor_id,
        True,
    )
    assert output[0][0] == renderer.player_symbol
    if world_map.width > 1 and world_map.height > 1:
        assert output[1][1] == " "


@pytest.mark.skip(reason="Curses rendering in a simulated terminal is hard to test.")
@patch("curses.initscr")
@patch("curses.start_color")
@patch("curses.noecho")
@patch("curses.cbreak")
@patch("curses.curs_set")
@patch("curses.endwin")
def test_render_adapts_to_small_terminal_curses_mode(
    mock_endwin, mock_curs_set, mock_cbreak, mock_noecho, mock_start_color, mock_initscr
):
    large_map_w, large_map_h = 30, 15
    player_symbol = "@"

    mock_stdscr = MagicMock()
    mock_initscr.return_value = mock_stdscr

    # Since curses.LINES/COLS are special, we don't patch them.
    # We trust the renderer's internal logic will try to access them,
    # and we just want to ensure it doesn't crash if they are not available
    # in the test environment (which they won't be without a real screen).
    # The try/except block in the renderer handles this.
    renderer_curses = Renderer(
        debug_mode=False,
        map_width=large_map_w,
        map_height=large_map_h,
        player_symbol=player_symbol,
    )

    try:
        renderer_curses.render_all(
            player_x=0,
            player_y=0,
            player_health=100,
            world_map_to_render=MockWorldMap(large_map_w, large_map_h),
            input_mode=InputMode.MOVEMENT,
            current_command_buffer="",
            message_log=MessageLog(),
            current_floor_id=0,
            debug_render_to_list=False,
        )
        assert mock_stdscr.addstr.called
    except Exception as e:
        pytest.fail(f"Curses render_all failed in small terminal simulation: {e}")
    finally:
        renderer_curses.cleanup_curses()


def test_render_path(setup_renderer):
    (
        renderer,
        world_map,
        player_pos,
        player_health,
        message_log,
        current_floor_id,
        input_mode,
        current_command_buffer,
    ) = setup_renderer
    path = [(1, 1, 0), (1, 2, 0), (1, 3, 0), (2, 3, 0)]
    for x, y, fid in path:
        if fid == current_floor_id:
            tile = world_map.get_tile(x, y)
            if tile:
                tile.type = "floor"

    output = renderer.render_all(
        player_pos[0],
        player_pos[1],
        player_health,
        world_map,
        input_mode,
        current_command_buffer,
        message_log,
        current_floor_id,
        debug_render_to_list=True,
        ai_path=path,
    )

    map_output_section = output[: world_map.height]
    assert map_output_section[1][1] == "*"
    assert map_output_section[2][1] == "*"
    assert map_output_section[3][1] == "*"
    assert map_output_section[3][2] == "x"
