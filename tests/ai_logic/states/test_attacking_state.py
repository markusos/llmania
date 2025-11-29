import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.attacking_state import AttackingState


class TestAttackingState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        # Mock player_view with proper numeric values
        self.ai_logic.player_view = MagicMock()
        self.ai_logic.player_view.health = 100
        self.ai_logic.player_view.max_health = 100
        # Mock new methods from Phase 1
        self.ai_logic.should_enter_survival_mode.return_value = False
        self.ai_logic.should_heal_before_combat.return_value = False
        self.ai_logic.get_safest_adjacent_monster.return_value = None
        self.state = AttackingState(self.ai_logic)

    def test_handle_transitions(self):
        # Test transition to SurvivalState
        self.ai_logic.should_enter_survival_mode.return_value = True
        self.assertEqual(self.state.handle_transitions(), "SurvivalState")

        # Test transition to ExploringState
        self.ai_logic.should_enter_survival_mode.return_value = False
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.assertEqual(self.state.handle_transitions(), "ExploringState")

        # Test no transition
        monster = MagicMock()
        monster.name = "Goblin"
        self.ai_logic._get_adjacent_monsters.return_value = [monster]
        self.assertEqual(self.state.handle_transitions(), "AttackingState")

    def test_get_next_action(self):
        # Test attacking a monster (safe to engage)
        monster = MagicMock()
        monster.name = "Goblin"
        self.ai_logic.get_safest_adjacent_monster.return_value = monster
        self.ai_logic._get_adjacent_monsters.return_value = [monster]
        action = self.state.get_next_action()
        self.assertEqual(action, ("attack", "Goblin"))

        # Test no safe monster but still attacks (fallback to random)
        self.ai_logic.get_safest_adjacent_monster.return_value = None
        self.ai_logic._get_adjacent_monsters.return_value = [monster]
        self.ai_logic.random.choice.return_value = monster
        action = self.state.get_next_action()
        self.assertEqual(action, ("attack", "Goblin"))

        # Test no adjacent monsters at all
        self.ai_logic._get_adjacent_monsters.return_value = []
        action = self.state.get_next_action()
        self.assertIsNone(action)
