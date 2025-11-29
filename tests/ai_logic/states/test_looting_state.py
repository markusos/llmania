import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.looting_state import LootingState


class TestLootingState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        # Mock player_view with proper numeric values
        self.ai_logic.player_view = MagicMock()
        self.ai_logic.player_view.health = 100
        self.ai_logic.player_view.max_health = 100
        self.ai_logic.player_view.current_floor_id = 0
        self.ai_logic.player_view.x = 1
        self.ai_logic.player_view.y = 1
        # Mock new methods from Phase 1
        self.ai_logic.should_enter_survival_mode.return_value = False
        self.ai_logic.get_safest_adjacent_monster.return_value = None
        self.state = LootingState(self.ai_logic)

    def test_handle_transitions(self):
        # Test transition to SurvivalState (via dynamic threshold)
        self.ai_logic.should_enter_survival_mode.return_value = True
        self.assertEqual(self.state.handle_transitions(), "SurvivalState")

        # Test transition to AttackingState (when monsters adjacent)
        self.ai_logic.should_enter_survival_mode.return_value = False
        monster = MagicMock()
        monster.name = "Goblin"
        self.ai_logic._get_adjacent_monsters.return_value = [monster]
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

        # Test equipping beneficial items (Phase 2.3 - replaces _equip_better_weapon)
        self.state._use_item = MagicMock(return_value=None)
        self.state._equip_beneficial_items = MagicMock(return_value=("use", "Axe"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("use", "Axe"))

        # Test taking an item
        self.state._equip_beneficial_items = MagicMock(return_value=None)
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
