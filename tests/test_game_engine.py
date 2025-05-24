import curses  # For curses constants like curses.KEY_ENTER,
from unittest.mock import patch

import pytest

# curses.KEY_BACKSPACE if needed by engine
from src.game_engine import GameEngine
from src.item import Item
from src.monster import Monster
from src.parser import Parser
from src.player import Player
from src.tile import ENTITY_SYMBOLS, TILE_SYMBOLS
from src.world_generator import WorldGenerator
from src.world_map import WorldMap


@pytest.fixture
def game_engine_setup():
    """Fixture to set up a game engine with a predictable map and player/win
    positions."""
    with patch("src.game_engine.curses") as mock_curses_fixture:
        mock_curses_fixture.KEY_ENTER = curses.KEY_ENTER
        mock_curses_fixture.KEY_BACKSPACE = curses.KEY_BACKSPACE
        mock_curses_fixture.error = curses.error
        with patch.object(
            WorldGenerator,
            "generate_map",
            return_value=(WorldMap(5, 5), (1, 1), (3, 3)),
        ):
            engine = GameEngine(map_width=5, map_height=5)

        engine.world_map = WorldMap(5, 5) # Overwrite with a simple 5x5 map
        # Ensure all tiles are floor initially for predictability
        for y in range(engine.world_map.height):
            for x in range(engine.world_map.width):
                engine.world_map.get_tile(x,y).type = "floor"
        
        engine.player = Player(x=1, y=1, health=20) # Player at (1,1)
        engine.win_pos = (3, 3) # Win position at (3,3)
        amulet = Item(
            "Amulet of Yendor", "The object of your quest!", {"type": "quest"}
        )
        engine.world_map.place_item(amulet, engine.win_pos[0], engine.win_pos[1])
        
        engine.game_over = False
        engine.message_log = []
        yield engine


@pytest.fixture
def game_engine_and_curses_mock_setup():
    """Fixture to set up a game engine and also return the curses mock."""
    with patch("src.game_engine.curses") as mock_curses_fixture:
        mock_curses_fixture.KEY_ENTER = curses.KEY_ENTER
        mock_curses_fixture.KEY_BACKSPACE = curses.KEY_BACKSPACE
        mock_curses_fixture.error = curses.error
        with patch.object(
            WorldGenerator,
            "generate_map",
            return_value=(WorldMap(5, 5), (1, 1), (3, 3)),
        ):
            engine = GameEngine(map_width=5, map_height=5)

        engine.world_map = WorldMap(5, 5)
        for y in range(engine.world_map.height):
            for x in range(engine.world_map.width):
                engine.world_map.get_tile(x,y).type = "floor"

        engine.player = Player(x=1, y=1, health=20)
        engine.win_pos = (3, 3)
        amulet = Item(
            "Amulet of Yendor", "The object of your quest!", {"type": "quest"}
        )
        engine.world_map.place_item(amulet, engine.win_pos[0], engine.win_pos[1])
        engine.game_over = False
        engine.message_log = []
        yield engine, mock_curses_fixture


@patch("src.game_engine.curses")
def test_game_engine_init_curses_setup_specific(mock_curses_module):
    mock_stdscr_instance = mock_curses_module.initscr.return_value
    with patch.object(
        WorldGenerator, "generate_map", return_value=(WorldMap(5, 5), (1, 1), (3, 3))
    ):
        engine = GameEngine(map_width=5, map_height=5)

    mock_curses_module.initscr.assert_called_once()
    mock_curses_module.noecho.assert_called_once()
    mock_curses_module.cbreak.assert_called_once()
    mock_stdscr_instance.keypad.assert_called_with(True)
    mock_curses_module.curs_set.assert_called_with(0)
    assert engine.input_mode == "movement"
    assert engine.current_command_buffer == ""


def test_game_engine_initialization_attributes(game_engine_setup):
    engine = game_engine_setup
    assert isinstance(engine.world_generator, WorldGenerator)
    assert isinstance(engine.parser, Parser)
    assert isinstance(engine.world_map, WorldMap)
    assert engine.world_map.width == 5
    assert engine.world_map.height == 5
    assert isinstance(engine.player, Player)
    assert engine.player.health == 20
    assert (engine.player.x, engine.player.y) == (1, 1)
    assert engine.win_pos == (3, 3)
    assert not engine.game_over
    assert engine.message_log == []
    assert engine.input_mode == "movement"


class TestHandleInput:
    def test_movement_mode_arrow_keys(self, game_engine_and_curses_mock_setup):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "movement"
        test_cases = {
            "KEY_UP": ("move", "north"), "w": ("move", "north"), 
            "W": ("move", "north"),
            "KEY_DOWN": ("move", "south"), "s": ("move", "south"), 
            "S": ("move", "south"),
            "KEY_LEFT": ("move", "west"), "a": ("move", "west"), 
            "A": ("move", "west"),
            "KEY_RIGHT": ("move", "east"), "d": ("move", "east"), 
            "D": ("move", "east"),
        }
        for key_input, expected_command in test_cases.items():
            engine.stdscr.getkey.return_value = key_input
            command = engine.handle_input_and_get_command()
            assert command == expected_command
            mock_curses.curs_set.assert_called_with(0)

    def test_movement_mode_switch_to_command_mode_with_q(
        self, game_engine_and_curses_mock_setup
    ):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "movement"
        engine.stdscr.getkey.return_value = "q"
        command = engine.handle_input_and_get_command()
        assert command is None
        assert engine.input_mode == "command"
        assert engine.current_command_buffer == ""
        mock_curses.curs_set.assert_called_with(1)

    def test_command_mode_char_input(self, game_engine_and_curses_mock_setup):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "command"
        engine.current_command_buffer = "get "
        engine.stdscr.getkey.return_value = "s"
        command = engine.handle_input_and_get_command()
        assert command is None
        assert engine.current_command_buffer == "get s"
        mock_curses.curs_set.assert_called_with(1)

    def test_command_mode_backspace(self, game_engine_and_curses_mock_setup):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "command"
        engine.current_command_buffer = "drop axe"
        engine.stdscr.getkey.return_value = "KEY_BACKSPACE"
        command = engine.handle_input_and_get_command()
        assert command is None
        assert engine.current_command_buffer == "drop ax"
        engine.stdscr.getkey.return_value = "\x08" 
        command = engine.handle_input_and_get_command()
        assert command is None
        assert engine.current_command_buffer == "drop a"
        engine.stdscr.getkey.return_value = "\x7f" 
        command = engine.handle_input_and_get_command()
        assert command is None
        assert engine.current_command_buffer == "drop "
        mock_curses.curs_set.assert_any_call(1)

    def test_command_mode_enter_parses_command(
        self, game_engine_and_curses_mock_setup
    ):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "command"
        test_typed_command = "use health potion"
        engine.current_command_buffer = test_typed_command
        expected_parsed_command = ("use", "health potion")
        with patch.object(
            engine.parser, "parse_command", return_value=expected_parsed_command
        ) as mock_parse_method:
            engine.stdscr.getkey.return_value = "\n"
            returned_command = engine.handle_input_and_get_command()
            mock_parse_method.assert_called_once_with(test_typed_command)
            assert returned_command == expected_parsed_command
            assert engine.input_mode == "movement"
            assert engine.current_command_buffer == ""
            mock_curses.curs_set.assert_called_with(0)

    def test_command_mode_enter_with_curses_key_enter(
        self, game_engine_and_curses_mock_setup
    ):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "command"
        engine.current_command_buffer = "look"
        engine.stdscr.getkey.return_value = curses.KEY_ENTER
        expected_parsed_command = ("look", None)
        with patch.object(
            engine.parser, "parse_command", return_value=expected_parsed_command
        ) as mock_parse:
            returned_command = engine.handle_input_and_get_command()
            mock_parse.assert_called_once_with("look")
            assert returned_command == expected_parsed_command
            assert engine.input_mode == "movement"

    def test_command_mode_escape_exits(self, game_engine_and_curses_mock_setup):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "command"
        engine.current_command_buffer = "look around"
        engine.stdscr.getkey.return_value = "\x1b" 
        command = engine.handle_input_and_get_command()
        assert command is None
        assert engine.input_mode == "movement"
        assert engine.current_command_buffer == ""
        mock_curses.curs_set.assert_called_with(0)

    def test_command_mode_q_exits(self, game_engine_and_curses_mock_setup):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "command"
        engine.current_command_buffer = "anything"
        engine.stdscr.getkey.return_value = "q"
        command = engine.handle_input_and_get_command()
        assert command is None
        assert engine.input_mode == "movement"
        assert engine.current_command_buffer == ""
        mock_curses.curs_set.assert_called_with(0)

    def test_command_mode_resize_key(self, game_engine_and_curses_mock_setup):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.input_mode = "command"
        engine.stdscr.getkey.return_value = "KEY_RESIZE"
        command = engine.handle_input_and_get_command()
        assert command is None
        engine.stdscr.clear.assert_called_once()
        assert engine.input_mode == "command"

    def test_getkey_error_returns_none(self, game_engine_and_curses_mock_setup):
        engine, mock_curses = game_engine_and_curses_mock_setup
        engine.stdscr.getkey.side_effect = curses.error
        command = engine.handle_input_and_get_command()
        assert command is None


@patch("src.game_engine.curses")
def test_render_map_movement_mode(
    mock_curses_module, game_engine_setup  # mock_curses_module is unused
):
    engine = game_engine_setup
    # Player starts at (1,1) in fixture
    engine.player.x, engine.player.y = 2, 3  # Move player for test
    engine.player.health = 50
    engine.world_map.set_tile_type(1, 1, "wall")  # Wall at (1,1)
    # Amulet (Item) is at engine.win_pos = (3,3) by fixture setup
    # Ensure other relevant tiles are floors for predictable output
    engine.world_map.get_tile(0, 1).type = "floor"
    engine.world_map.get_tile(0, 3).type = "floor"
    engine.world_map.get_tile(1, 3).type = "floor"


    engine.message_log.extend(["Message A", "Message B"])
    engine.input_mode = "movement"
    output_buffer = engine.render_map(debug_render_to_list=True)

    map_height = engine.world_map.height # 5

    # Expected map (5x5 tiles): Player (P) at (2,3), Wall (W) at (1,1), Item (I) at (3,3)
    # F F F F F  (y=0)
    # F W F F F  (y=1)
    # F F F F F  (y=2)
    # F F P I F  (y=3)
    # F F F F F  (y=4)

    # Check player
    assert output_buffer[3][2] == engine.PLAYER_SYMBOL
    # Check wall
    assert output_buffer[1][1] == TILE_SYMBOLS["wall"]
    # Check item (Amulet)
    assert output_buffer[3][3] == ENTITY_SYMBOLS["item"]
    
    # Check some floor tiles
    assert output_buffer[0][0] == TILE_SYMBOLS["floor"] # (0,0)
    assert output_buffer[1][0] == TILE_SYMBOLS["floor"] # (0,1)
    assert output_buffer[3][1] == TILE_SYMBOLS["floor"] # (1,3) Floor next to Player
    assert output_buffer[4][4] == TILE_SYMBOLS["floor"] # (4,4)

    # UI elements
    assert output_buffer[map_height] == f"HP: {engine.player.health}"
    assert output_buffer[map_height + 1] == f"MODE: {engine.input_mode.upper()}"
    assert output_buffer[map_height + 2] == "Message A"
    assert output_buffer[map_height + 3] == "Message B"


@patch("src.game_engine.curses")
def test_render_map_command_mode(
    mock_curses_module, game_engine_setup # mock_curses_module unused
):
    engine = game_engine_setup
    engine.player.x, engine.player.y = 0, 0 # Player at (0,0)
    engine.player.health = 25
    engine.message_log.append("Last Message")
    engine.input_mode = "command"
    engine.current_command_buffer = "take pot"
    output_buffer = engine.render_map(debug_render_to_list=True)

    map_height = engine.world_map.height # 5

    # Player at (0,0)
    assert output_buffer[0][0] == engine.PLAYER_SYMBOL
    # Check a floor tile next to player
    assert output_buffer[0][1] == TILE_SYMBOLS["floor"]
    assert output_buffer[1][0] == TILE_SYMBOLS["floor"]

    # UI elements
    assert output_buffer[map_height] == f"HP: {engine.player.health}"
    assert output_buffer[map_height + 1] == f"MODE: {engine.input_mode.upper()}"
    assert output_buffer[map_height + 2] == \
        f"> {engine.current_command_buffer}"
    assert output_buffer[map_height + 3] == "Last Message"


def test_process_command_tuple_move_valid(game_engine_setup):
    engine = game_engine_setup
    # Player starts at (1,1) in fixture
    engine.world_map.get_tile(1, 2).type = "floor" # Ensure south is movable
    engine.process_command_tuple(("move", "south"))
    assert engine.player.x == 1 and engine.player.y == 2
    assert "You move south." in engine.message_log


def test_process_command_tuple_take_quest_item(game_engine_setup):
    engine = game_engine_setup
    engine.player.x, engine.player.y = engine.win_pos # Move player to win_pos
    engine.process_command_tuple(("take", "Amulet of Yendor"))
    assert "You picked up the Amulet of Yendor! You win!" in engine.message_log
    assert engine.game_over is True


def test_process_command_tuple_unknown_command_from_parser(game_engine_setup):
    engine = game_engine_setup
    engine.process_command_tuple(None)
    assert "Unknown command." in engine.message_log


@patch.object(GameEngine, "handle_input_and_get_command")
@patch.object(GameEngine, "process_command_tuple")
@patch.object(GameEngine, "render_map")
def test_run_loop_flow_and_quit(
    mock_render, mock_process, mock_handle, game_engine_setup
):
    engine = game_engine_setup
    mock_handle.side_effect = [("look", None), ("quit", None)]
    def process_side_effect(parsed_command):
        engine.message_log.append(f"Processed: {parsed_command}")
        if parsed_command == ("quit", None): 
            engine.game_over = True
    mock_process.side_effect = process_side_effect
    engine.run()
    assert engine.game_over is True
    assert mock_handle.call_count == 2
    mock_process.assert_any_call(("look", None))
    mock_process.assert_any_call(("quit", None))
    assert mock_render.call_count >= 3


@patch.object(GameEngine, "handle_input_and_get_command")
@patch.object(GameEngine, "render_map")
def test_game_engine_run_curses_cleanup_normal_exit(
    mock_render_map, mock_handle_input, game_engine_and_curses_mock_setup
):
    mock_handle_input.return_value = ("quit", None)
    engine, mock_curses = game_engine_and_curses_mock_setup
    original_process = engine.process_command_tuple
    def side_effect(cmd_tuple):
        original_process(cmd_tuple)
        if cmd_tuple == ("quit", None): 
            assert engine.game_over is True
    with patch.object(engine, "process_command_tuple", side_effect=side_effect):
        engine.run()
    engine.stdscr.keypad.assert_called_with(False)
    mock_curses.echo.assert_called_once()
    mock_curses.nocbreak.assert_called_once()
    mock_curses.endwin.assert_called_once()


@patch.object(GameEngine, "handle_input_and_get_command")
@patch.object(GameEngine, "render_map")
def test_game_engine_run_curses_cleanup_on_exception(
    mock_render_map, mock_handle_input, game_engine_and_curses_mock_setup
):
    mock_handle_input.return_value = ("move", "north")
    mock_render_map.side_effect = Exception("Test rendering error")
    engine, mock_curses = game_engine_and_curses_mock_setup
    with pytest.raises(Exception, match="Test rendering error"):
        engine.run()
    engine.stdscr.keypad.assert_called_with(False)
    mock_curses.echo.assert_called_once()
    mock_curses.nocbreak.assert_called_once()
    mock_curses.endwin.assert_called_once()


def test_player_initial_position_is_floor(game_engine_setup):
    engine = game_engine_setup
    tile = engine.world_map.get_tile(engine.player.x, engine.player.y)
    assert tile is not None and tile.type == "floor"


def test_win_position_is_floor_and_has_amulet(game_engine_setup):
    engine = game_engine_setup
    wx, wy = engine.win_pos
    tile = engine.world_map.get_tile(wx, wy)
    assert tile is not None and tile.type == "floor"
    assert tile.item is not None and tile.item.name == "Amulet of Yendor"


def test_player_start_and_win_positions_differ(game_engine_setup):
    engine = game_engine_setup
    assert (engine.player.x, engine.player.y) != engine.win_pos


def test_process_command_tuple_drop_item_empty_tile(game_engine_setup):
    engine = game_engine_setup
    # Player starts at (1,1). Ensure tile (1,1) is clear for dropping.
    engine.world_map.get_tile(1, 1).item = None 
    potion = Item("Potion", "Heals", {})
    engine.player.take_item(potion)
    engine.process_command_tuple(("drop", "Potion"))
    assert len(engine.player.inventory) == 0
    tile = engine.world_map.get_tile(1, 1)
    assert tile.item is not None and tile.item.name == "Potion"
    assert "You drop the Potion." in engine.message_log


def test_process_command_tuple_use_heal_item(game_engine_setup):
    engine = game_engine_setup
    engine.player.health = 10
    potion = Item("Health Potion", "Heals 5 HP", {"type": "heal", "amount": 5})
    engine.player.take_item(potion)
    engine.process_command_tuple(("use", "Health Potion"))
    assert engine.player.health == 15 and len(engine.player.inventory) == 0
    assert "Used Health Potion, healed by 5 HP." in engine.message_log


def test_process_command_tuple_attack_no_monster(game_engine_setup):
    engine = game_engine_setup
    # Player at (1,1). Ensure no monster is adjacent.
    engine.world_map.get_tile(1,0).monster = None # North
    engine.world_map.get_tile(1,2).monster = None # South
    engine.world_map.get_tile(0,1).monster = None # West
    engine.world_map.get_tile(2,1).monster = None # East
    engine.process_command_tuple(("attack", "ghost"))
    assert "There is no monster named ghost nearby." in engine.message_log


def test_process_command_tuple_attack_no_arg_monster_exists(game_engine_setup):
    engine = game_engine_setup
    # Player at (1,1). Place monster adjacent, e.g., at (1,0) North.
    monster = Monster("Goblin", 10, 3)
    engine.world_map.place_monster(monster, 1, 0) # North of player
    
    initial_monster_health = monster.health
    initial_player_health = engine.player.health
    engine.player.base_attack_power = 5 # Set player attack for predictability

    engine.process_command_tuple(("attack", None)) # Attack with no argument
    
    # Monster should be attacked
    assert f"You attack the Goblin for {engine.player.base_attack_power} damage." in engine.message_log
    assert monster.health == initial_monster_health - engine.player.base_attack_power
    # Monster should retaliate
    assert f"The Goblin attacks you for {monster.attack_power} damage." in engine.message_log
    assert engine.player.health == initial_player_health - monster.attack_power


def test_process_command_tuple_take_no_arg_item_exists(game_engine_setup):
    engine = game_engine_setup
    # Player at (1,1)
    item = Item("Rock", "", {})
    engine.world_map.place_item(item, 1, 1) # Item at player's location
    engine.process_command_tuple(("take", None))
    assert item.name in [i.name for i in engine.player.inventory]
    assert engine.world_map.get_tile(1, 1).item is None
    assert f"You take the {item.name}." in engine.message_log


class TestAttackCommand:
    def test_attack_adjacent_by_name_success_kill(self, game_engine_setup):
        engine = game_engine_setup
        engine.player.x, engine.player.y = 2, 2 # Move player for space
        engine.player.base_attack_power = 10
        bat = Monster("Bat", health=5, attack_power=2)
        engine.world_map.place_monster(bat, 2, 1) # North
        engine.process_command_tuple(("attack", "Bat"))
        assert (f"You attack the Bat for {engine.player.base_attack_power} damage."
                in engine.message_log)
        assert "You defeated the Bat!" in engine.message_log
        assert engine.world_map.get_tile(2, 1).monster is None

    def test_attack_adjacent_no_name_one_target_survives(self, game_engine_setup):
        engine = game_engine_setup
        engine.player.x, engine.player.y = 2, 2
        engine.player.base_attack_power = 3
        goblin = Monster("Goblin", health=10, attack_power=4)
        engine.world_map.place_monster(goblin, 3, 2) # East
        init_gob_hp, init_plyr_hp = goblin.health, engine.player.health
        engine.process_command_tuple(("attack", None))
        assert (f"You attack the Goblin for {engine.player.base_attack_power} damage."
                in engine.message_log)
        assert goblin.health == init_gob_hp - engine.player.base_attack_power
        assert (f"The Goblin attacks you for {goblin.attack_power} damage."
                in engine.message_log)
        assert engine.player.health == init_plyr_hp - goblin.attack_power
        assert engine.world_map.get_tile(3, 2).monster is goblin

    def test_attack_non_existent_monster_by_name(self, game_engine_setup):
        engine = game_engine_setup
        engine.player.x, engine.player.y = 2, 2
        bat = Monster("Bat", health=5, attack_power=2)
        engine.world_map.place_monster(bat, 2, 1) # North
        engine.process_command_tuple(("attack", "NonExistentMonster"))
        assert ("There is no monster named NonExistentMonster nearby."
                in engine.message_log)
        assert engine.world_map.get_tile(2, 1).monster is bat

    def test_attack_no_adjacent_monsters(self, game_engine_setup):
        engine = game_engine_setup
        engine.player.x, engine.player.y = 2, 2
        # Ensure no monsters are adjacent by clearing tiles around (2,2)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                tile_to_clear = engine.world_map.get_tile(2+dx, 2+dy)
                if tile_to_clear: tile_to_clear.monster = None
        
        engine.process_command_tuple(("attack", None))
        assert "There is no monster nearby to attack." in engine.message_log

    def test_ambiguity_multiple_same_name_attack_by_name(self, game_engine_setup):
        engine = game_engine_setup
        engine.player.x, engine.player.y = 2, 2
        bat1 = Monster("Bat", health=5, attack_power=2)
        bat2 = Monster("Bat", health=5, attack_power=2)
        engine.world_map.place_monster(bat1, 2, 1) # North
        engine.world_map.place_monster(bat2, 3, 2) # East
        engine.process_command_tuple(("attack", "Bat"))
        assert "Multiple Bats found. Which one?" in engine.message_log
        assert engine.world_map.get_tile(2,1).monster is bat1 
        assert engine.world_map.get_tile(3,2).monster is bat2

    def test_ambiguity_multiple_different_names_attack_no_name(
        self, game_engine_setup
    ):
        engine = game_engine_setup
        engine.player.x, engine.player.y = 2, 2
        bat = Monster("Bat", health=5, attack_power=2)
        goblin = Monster("Goblin", health=10, attack_power=3)
        engine.world_map.place_monster(bat, 2, 1) # North
        engine.world_map.place_monster(goblin, 3, 2) # East
        engine.process_command_tuple(("attack", None))
        # Message can have names in either order
        assert "Multiple monsters nearby:" in engine.message_log[0] 
        assert "Bat" in engine.message_log[0] 
        assert "Goblin" in engine.message_log[0] 
        assert "Which one to attack?" in engine.message_log[0]
        assert engine.world_map.get_tile(2,1).monster is bat 
        assert engine.world_map.get_tile(3,2).monster is goblin

    def test_monster_counter_attack_and_player_death(self, game_engine_setup):
        engine = game_engine_setup
        engine.player.x, engine.player.y = 2, 2
        engine.player.health = 5
        engine.player.base_attack_power = 1
        ogre = Monster("Ogre", health=50, attack_power=10)
        engine.world_map.place_monster(ogre, 2, 1) # North
        init_ogre_hp = ogre.health
        engine.process_command_tuple(("attack", "Ogre"))
        assert (f"You attack the Ogre for {engine.player.base_attack_power} damage."
                in engine.message_log)
        assert ogre.health == init_ogre_hp - engine.player.base_attack_power
        assert (f"The Ogre attacks you for {ogre.attack_power} damage."
                in engine.message_log)
        assert engine.player.health <= 0
        assert "You have been defeated. Game Over." in engine.message_log
        assert engine.game_over is True
        assert engine.world_map.get_tile(2, 1).monster is ogre
