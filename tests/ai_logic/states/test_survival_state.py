import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.survival_state import SurvivalState


class TestSurvivalState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        self.state = SurvivalState(self.ai_logic)

    def test_handle_transitions(self):
        # Test transition to ExploringState
        self.ai_logic.player.health = 6
        self.ai_logic.player.max_health = 10
        self.assertEqual(self.state.handle_transitions(), "ExploringState")

        # Test no transition
        self.ai_logic.player.health = 5
        self.ai_logic.player.max_health = 10
        self.assertEqual(self.state.handle_transitions(), "SurvivalState")

    def test_get_next_action(self):
        # Test using a health potion
        item = MagicMock()
        item.properties = {"type": "heal"}
        item.name = "Health Potion"
        self.ai_logic.player.inventory = [item]
        action = self.state.get_next_action()
        self.assertEqual(action, ("use", "Health Potion"))

        # Test fleeing from a monster
        self.ai_logic.player.inventory = []
        self.ai_logic._get_adjacent_monsters.return_value = [MagicMock()]
        self.state._get_safe_moves = MagicMock(return_value=["north"])
        self.ai_logic.random.choice.return_value = "north"
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "north"))

        # Test pathfinding to a health potion
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.ai_logic.target_finder.find_health_potions.return_value = [
            (1, 1, 0, "health_potion", 1)
        ]
        self.ai_logic.path_finder.find_path_bfs.return_value = [(1, 1, 0)]
        self.state._follow_path = MagicMock()
        self.state.get_next_action()
        self.state._follow_path.assert_called()

        # Test exploring
        self.ai_logic.target_finder.find_health_potions.return_value = []
        self.ai_logic.explorer.find_exploration_targets.return_value = [(1, 1, 0)]
        self.state._follow_path = MagicMock()
        self.state.get_next_action()
        self.state._follow_path.assert_called()

        # Test exploring randomly
        self.ai_logic.explorer.find_exploration_targets.return_value = None
        self.state._explore_randomly = MagicMock()
        self.state.get_next_action()
        self.state._explore_randomly.assert_called()
