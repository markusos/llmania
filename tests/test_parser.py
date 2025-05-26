import pytest

from src.parser import Parser


@pytest.fixture
def parser():
    return Parser()


# Test Empty and Unrecognized
def test_parse_empty_input(parser):
    assert parser.parse_command("") is None
    assert parser.parse_command("   ") is None


def test_parse_unrecognized_command(parser):
    assert parser.parse_command("fly") is None
    assert parser.parse_command("eat sandwich") is None
    assert parser.parse_command("move up") is None  # Invalid direction for "move"
    assert (
        parser.parse_command("n north") is None
    )  # "n" with argument "north" is not explicitly defined as valid
    assert parser.parse_command("take") == ("take", None)  # "take" without argument
    assert parser.parse_command("drop") == ("drop", None)  # "drop" without argument
    assert parser.parse_command("use") == ("use", None)  # "use" without argument
    assert parser.parse_command("attack") == ("attack", None)  # "attack" without argument
    assert parser.parse_command("inventory now") is None  # "inventory" with argument
    assert parser.parse_command("look around") is None  # "look" with argument
    assert parser.parse_command("quit now") is None  # "quit" with argument


# Test Movement Commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("move north", ("move", "north")),
        ("move south", ("move", "south")),
        ("move east", ("move", "east")),
        ("move west", ("move", "west")),
        ("MOVE NORTH", ("move", "north")),  # Case insensitivity
        ("   move   east   ", ("move", "east")),  # Extra spaces
        ("n", ("move", "north")),
        ("s", ("move", "south")),
        ("e", ("move", "east")),
        ("w", ("move", "west")),
        ("N", ("move", "north")),  # Case insensitivity for shorthand
        ("NORTH", ("move", "north")),  # Full direction as command
        ("SOUTH", ("move", "south")),
        ("EAST", ("move", "east")),
        ("WEST", ("move", "west")),
    ],
)
def test_parse_movement_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_movement_invalid_direction(parser):
    assert parser.parse_command("move sideways") is None
    assert parser.parse_command("northeast") is None  # Single word, not "n" or "north"


# Test "take" commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("take sword", ("take", "sword")),
        ("get shiny amulet", ("take", "shiny amulet")),
        ("Take Healing Potion", ("take", "healing potion")),  # Case insensitivity
        ("  take   key  ", ("take", "key")),  # Extra spaces
    ],
)
def test_parse_take_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_take_no_argument(parser):
    assert parser.parse_command("take") == ("take", None)
    assert parser.parse_command("get") == ("take", None)


# Test "drop" commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("drop shield", ("drop", "shield")),
        ("DROP OLD KEY", ("drop", "old key")),  # Case insensitivity
        ("  drop   torch   ", ("drop", "torch")),  # Extra spaces
    ],
)
def test_parse_drop_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_drop_no_argument(parser):
    assert parser.parse_command("drop") == ("drop", None)


# Test "use" commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("use potion", ("use", "potion")),
        ("USE map", ("use", "map")),  # Case insensitivity
        (
            "  use   scroll   of   teleportation  ",
            ("use", "scroll of teleportation"),
        ),  # Extra spaces + multiword
    ],
)
def test_parse_use_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_use_no_argument(parser):
    assert parser.parse_command("use") == ("use", None)


# Test "attack" commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("attack goblin", ("attack", "goblin")),
        ("fight dragon", ("attack", "dragon")),
        (
            "ATTACK Orc Leader",
            ("attack", "orc leader"),
        ),  # Case insensitivity + multiword
        (
            "  fight   giant   spider  ",
            ("attack", "giant spider"),
        ),  # Extra spaces + multiword
    ],
)
def test_parse_attack_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_attack_no_argument(parser):
    assert parser.parse_command("attack") == ("attack", None)
    assert parser.parse_command("fight") == ("attack", None)


# Test "inventory" commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("inventory", ("inventory", None)),
        ("i", ("inventory", None)),
        ("INVENTORY", ("inventory", None)),  # Case insensitivity
        ("  i  ", ("inventory", None)),  # Extra spaces
    ],
)
def test_parse_inventory_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_inventory_with_argument(parser):
    assert parser.parse_command("inventory list") is None
    assert parser.parse_command("i all") is None


# Test "look" commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("look", ("look", None)),
        ("l", ("look", None)),
        ("LOOK", ("look", None)),  # Case insensitivity
        ("  l  ", ("look", None)),  # Extra spaces
    ],
)
def test_parse_look_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_look_with_argument(parser):
    assert parser.parse_command("look around") is None
    assert parser.parse_command("l closely") is None


# Test "quit" commands
@pytest.mark.parametrize(
    "command_input, expected_output",
    [
        ("quit", ("quit", None)),
        ("q", ("quit", None)),
        ("QUIT", ("quit", None)),  # Case insensitivity
        ("  q  ", ("quit", None)),  # Extra spaces
        ("exit ", ("quit", None)),
    ],
)
def test_parse_quit_commands(parser, command_input, expected_output):
    assert parser.parse_command(command_input) == expected_output


def test_parse_quit_with_argument(parser):
    assert parser.parse_command("quit game") is None
    assert parser.parse_command("q now") is None
