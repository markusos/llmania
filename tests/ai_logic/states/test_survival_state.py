import sys
import unittest
from os import path
from unittest.mock import MagicMock

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))))
from src.ai_logic.states.survival_state import SurvivalState


class TestSurvivalState(unittest.TestCase):
    def setUp(self):
        self.ai_logic = MagicMock()
        # Mock player_view with proper numeric values
        self.ai_logic.player_view = MagicMock()
        self.ai_logic.player_view.health = 100
        self.ai_logic.player_view.max_health = 100
        self.ai_logic.player_view.current_floor_id = 0
        self.ai_logic.player_view.x = 1
        self.ai_logic.player_view.y = 1
        # Mock verbose for debug logging
        self.ai_logic.verbose = 0
        # Mock new methods from Phase 1
        self.ai_logic.should_enter_survival_mode.return_value = True
        self.ai_logic.get_safest_adjacent_monster.return_value = None
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.state = SurvivalState(self.ai_logic)
        self.ai_logic.state = self.state

    def test_handle_transitions(self):
        # Test transition to ExploringState (no longer in survival mode)
        self.ai_logic.should_enter_survival_mode.return_value = False
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.assertEqual(self.state.handle_transitions(), "ExploringState")

        # Test transition to AttackingState (healthy and safe monster nearby)
        monster = MagicMock()
        monster.name = "Goblin"
        self.ai_logic._get_adjacent_monsters.return_value = [monster]
        self.ai_logic.get_safest_adjacent_monster.return_value = monster
        self.assertEqual(self.state.handle_transitions(), "AttackingState")

        # Test no transition (still in survival mode)
        self.ai_logic.should_enter_survival_mode.return_value = True
        self.assertEqual(self.state.handle_transitions(), "SurvivalState")

    def test_get_next_action(self):
        # Test using a health potion
        self.state._use_item = MagicMock(return_value=("use", "Health Potion"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("use", "Health Potion"))

        # Test fleeing from a monster
        self.state._use_item = MagicMock(return_value=None)
        self.ai_logic._get_adjacent_monsters.return_value = [MagicMock()]
        self.ai_logic._is_in_loop.return_value = False  # Not in a loop
        self.state._get_safe_moves = MagicMock(return_value=[("move", "north")])
        self.ai_logic.random.choice.return_value = ("move", "north")
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "north"))

        # Test taking an item
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.state._pickup_item = MagicMock(return_value=("take", "Health Potion"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("take", "Health Potion"))

        # Test pathfinding to a health potion
        self.state._pickup_item = MagicMock(return_value=None)
        self.state._path_to_best_target = MagicMock(return_value=("move", "north"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "north"))

        # Test exploring
        self.state._path_to_best_target = MagicMock(return_value=None)
        self.ai_logic.explorer.find_exploration_targets.return_value = [
            (1, 1, 0, "explorer_target", 1)
        ]
        self.state._follow_path = MagicMock(return_value=("move", "south"))
        action = self.state.get_next_action()
        self.assertEqual(action, ("move", "south"))

        # Test exploring randomly
        self.ai_logic.explorer.find_exploration_targets.return_value = None
        self.state._explore_randomly = MagicMock(return_value=("look", None))
        action = self.state.get_next_action()
        self.assertEqual(action, ("look", None))

    def test_fleeing_loop(self):
        # Test that the AI can break out of a fleeing loop
        self.state._use_item = MagicMock(return_value=None)
        self.ai_logic._get_adjacent_monsters.return_value = [MagicMock()]
        self.state._get_safe_moves = MagicMock(
            return_value=[("move", "north"), ("move", "south")]
        )
        self.ai_logic.random.choice.side_effect = [
            ("move", "north"),
            ("move", "south"),
            ("move", "north"),
            ("move", "south"),
        ]
        self.ai_logic._is_in_loop.return_value = False
        self.state.get_next_action()
        self.state.get_next_action()
        self.state.get_next_action()
        self.ai_logic._is_in_loop.return_value = True
        self.state._explore_randomly = MagicMock(return_value=("move", "east"))
        action = self.state.get_next_action()
        self.assertNotEqual(action, ("move", "north"))
        self.assertNotEqual(action, ("move", "south"))

    def test_path_to_potion_avoids_monsters(self):
        # Test that the AI uses risk-aware pathfinding in SurvivalState
        self.state._use_item = MagicMock(return_value=None)
        self.ai_logic._get_adjacent_monsters.return_value = []
        self.state._pickup_item = MagicMock(return_value=None)
        self.ai_logic.target_finder.find_health_potions.return_value = [
            (1, 1, 0, "health_potion", 1)
        ]
        self.ai_logic.path_finder.find_path_risk_aware.return_value = None
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_risk_aware.assert_called_with(
            self.ai_logic.ai_visible_maps,
            (self.ai_logic.player_view.x, self.ai_logic.player_view.y),
            self.ai_logic.player_view.current_floor_id,
            (1, 1),
            0,
            player_health_ratio=1.0,  # health/max_health = 100/100
            require_explored=True,
        )
