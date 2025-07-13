import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.attacking_state import AttackingState


class TestAttackingState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        self.state = AttackingState(self.ai_logic)

    def test_handle_transitions(self):
        # Test transition to SurvivalState
        self.ai_logic.player.health = 1
        self.ai_logic.player.max_health = 10
        self.assertEqual(self.state.handle_transitions(), "SurvivalState")

        # Test transition to ExploringState
        self.ai_logic.player.health = 10
        self.ai_logic.player.max_health = 10
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.assertEqual(self.state.handle_transitions(), "ExploringState")

        # Test no transition
        self.ai_logic._get_adjacent_monsters.return_value = [MagicMock()]
        self.assertEqual(self.state.handle_transitions(), "AttackingState")

    def test_get_next_action(self):
        # Test attacking a monster
        monster = MagicMock()
        monster.name = "Goblin"
        self.ai_logic._get_adjacent_monsters.return_value = [monster]
        self.ai_logic.random.choice.return_value = monster
        action = self.state.get_next_action()
        self.assertEqual(action, ("attack", "Goblin"))

        # Test no adjacent monsters
        self.ai_logic._get_adjacent_monsters.return_value = []
        action = self.state.get_next_action()
        self.assertIsNone(action)

        # Test that it doesn't attack if there are no monsters
        self.ai_logic._get_adjacent_monsters.return_value = []
        action = self.state.get_next_action()
        self.assertIsNone(action)
