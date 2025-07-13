import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.looting_state import LootingState


class TestLootingState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        self.state = LootingState(self.ai_logic)

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

        # Test transition to ExploringState
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.state._has_visible_items = MagicMock(return_value=False)
        self.assertEqual(self.state.handle_transitions(), "ExploringState")

        # Test no transition
        self.state._has_visible_items = MagicMock(return_value=True)
        self.assertEqual(self.state.handle_transitions(), "LootingState")

    def test_get_next_action(self):
        # Test using a health potion
        self.state._use_item = MagicMock(return_value=("use", "Health Potion"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("use", "Health Potion"))

        # Test equipping a better weapon
        self.state._use_item = MagicMock(return_value=None)
        self.state._equip_better_weapon = MagicMock(return_value=("use", "Axe"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("use", "Axe"))

        # Test taking an item
        self.state._equip_better_weapon = MagicMock(return_value=None)
        self.state._pickup_item = MagicMock(return_value=("take", "Rock"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("take", "Rock"))

        # Test pathfinding to an item
        self.state._pickup_item = MagicMock(return_value=None)
        self.state._path_to_best_target = MagicMock(return_value=("move", "north"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "north"))

        # Test exploring
        self.state._path_to_best_target = MagicMock(return_value=None)
        self.state._explore_randomly = MagicMock(return_value=("move", "south"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "south"))
