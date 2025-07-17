import random
from unittest.mock import MagicMock

from src.monster import Monster
from src.monster_ai.main import MonsterAILogic
from src.player import Player
from src.world_map import WorldMap


def test_monster_ai_initial_state():
    monster = Monster("test", 10, 1)
    player = Player(x=10, y=10, current_floor_id=0, health=100)
    world_map = WorldMap(20, 20)
    rng = random.Random()
    ai = MonsterAILogic(monster, player, world_map, rng)
    assert ai.state.__class__.__name__ == "IdleState"


def test_monster_ai_idle_to_attacking_transition():
    monster = Monster("test", 10, 1, x=5, y=5, line_of_sight=5)
    player = Player(x=6, y=6, current_floor_id=0, health=100)
    world_map = WorldMap(20, 20)
    rng = random.Random()
    ai = MonsterAILogic(monster, player, world_map, rng)
    pathfinder_mock = MagicMock()
    pathfinder_mock.a_star_search.return_value = [(5, 5), (6, 5)]
    ai.path_finder = pathfinder_mock
    action = ai.get_next_action()
    assert ai.state.__class__.__name__ == "AttackingState"
    assert action == ("move", "east")


def test_monster_ai_attacking_to_idle_transition():
    monster = Monster("test", 10, 1, x=5, y=5, line_of_sight=5)
    player = Player(x=15, y=15, current_floor_id=0, health=100)
    world_map = WorldMap(20, 20)
    rng = random.Random()
    ai = MonsterAILogic(monster, player, world_map, rng)
    ai.state = ai._get_state("AttackingState")
    action = ai.get_next_action()
    assert ai.state.__class__.__name__ == "IdleState"
    assert action is None


def test_monster_ai_attack_when_in_range():
    monster = Monster("test", 10, 1, x=5, y=5, attack_range=1)
    player = Player(x=5, y=6, current_floor_id=0, health=100)
    world_map = WorldMap(20, 20)
    rng = random.Random()
    ai = MonsterAILogic(monster, player, world_map, rng)
    ai.state = ai._get_state("AttackingState")
    action = ai.get_next_action()
    assert action == ("attack", None)


def test_monster_ai_move_when_in_los_but_not_in_range():
    monster = Monster("test", 10, 1, x=5, y=5, line_of_sight=5, attack_range=1)
    player = Player(x=7, y=7, current_floor_id=0, health=100)
    world_map = WorldMap(20, 20)
    pathfinder_mock = MagicMock()
    pathfinder_mock.a_star_search.return_value = [(5, 5), (6, 5)]
    rng = random.Random()
    ai = MonsterAILogic(monster, player, world_map, rng)
    ai.path_finder = pathfinder_mock
    ai.state = ai._get_state("AttackingState")
    action = ai.get_next_action()
    assert action == ("move", "east")
