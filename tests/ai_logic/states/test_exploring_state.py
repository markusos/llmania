import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.exploring_state import ExploringState


class TestExploringState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        self.state = ExploringState(self.ai_logic)

    def test_handle_transitions(self):
        # Test transition to SurvivalState
        self.ai_logic.player.health = 1
        self.ai_logic.player.max_health = 10
        self.assertEqual(self.state.handle_transitions(), "SurvivalState")

        # Test transition to AttackingState
        self.ai_logic.player.health = 10
        self.ai_logic.player.max_health = 10
        self.ai_logic._get_adjacent_monsters.return_value = [MagicMock()]
        self.assertEqual(self.state.handle_transitions(), "AttackingState")

        # Test transition to LootingState
        self.ai_logic._get_adjacent_monsters.return_value = []
        (
            self.ai_logic.ai_visible_maps.get.return_value.get_tile.return_value.item
        ) = MagicMock()
        self.assertEqual(self.state.handle_transitions(), "LootingState")

        # Test no transition
        (
            self.ai_logic.ai_visible_maps.get.return_value.get_tile.return_value.item
        ) = None
        self.assertEqual(self.state.handle_transitions(), "ExploringState")

    def test_get_next_action(self):
        # Test exploring
        self.ai_logic.explorer.find_exploration_targets.return_value = [
            (1, 1, 0, "explorer_target", 1)
        ]
        self.state._follow_path = MagicMock(return_value=("move", "south"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "south"))

        # Test pathfinding to a target
        self.ai_logic.explorer.find_exploration_targets.return_value = None
        self.state._path_to_best_target = MagicMock(return_value=("move", "north"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "north"))

        # Test exploring randomly
        self.state._path_to_best_target = MagicMock(return_value=None)
        self.state._explore_randomly = MagicMock(return_value=("look", None))
        action = self.state.get_next_action()
        self.assertEqual(action, ("look", None))
