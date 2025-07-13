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
        self.ai_logic.ai_visible_maps.get.return_value.get_tile.return_value.item = None
        self.assertEqual(self.state.handle_transitions(), "ExploringState")

    def test_get_next_action(self):
        # Test finding health potions
        self.ai_logic.target_finder.find_health_potions.return_value = [
            (1, 1, 0, "health_potion", 1)
        ]
        self.ai_logic.path_finder.find_path_bfs.return_value = [(1, 1, 0)]
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_bfs.assert_called()

        # Test finding quest items
        self.ai_logic.target_finder.find_health_potions.return_value = []
        self.ai_logic.target_finder.find_quest_items.return_value = [
            (1, 1, 0, "quest_item", 1)
        ]
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_bfs.assert_called()

        # Test finding exploration targets
        self.ai_logic.target_finder.find_quest_items.return_value = []
        self.ai_logic.explorer.find_exploration_targets.return_value = [(1, 1, 0)]
        self.state.get_next_action()
        self.assertIsNotNone(self.ai_logic.current_path)

        # Test exploring randomly
        self.ai_logic.explorer.find_exploration_targets.return_value = None
        self.state._explore_randomly = MagicMock()
        self.state.get_next_action()
        self.state._explore_randomly.assert_called()

        # Test finding unvisited portals
        self.ai_logic.explorer.find_exploration_targets.return_value = None
        self.ai_logic.explorer.find_unvisited_portals.return_value = [
            (1, 1, 0, "unvisited_portal", 1)
        ]
        self.ai_logic.path_finder.find_path_bfs.return_value = [(1, 1, 0)]
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_bfs.assert_called()

        # Test finding portals to unexplored floors
        self.ai_logic.explorer.find_unvisited_portals.return_value = []
        self.ai_logic.explorer.find_portal_to_unexplored_floor.return_value = [
            (1, 1, 0, "portal_to_unexplored", 1)
        ]
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_bfs.assert_called()

        # Test finding other items
        self.ai_logic.explorer.find_portal_to_unexplored_floor.return_value = []
        self.ai_logic.target_finder.find_other_items.return_value = [
            (1, 1, 0, "item", 1)
        ]
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_bfs.assert_called()

        # Test finding monsters
        self.ai_logic.target_finder.find_other_items.return_value = []
        self.ai_logic.target_finder.find_monsters.return_value = [
            (1, 1, 0, "monster", 1)
        ]
        self.state.get_next_action()
        self.ai_logic.path_finder.find_path_bfs.assert_called()
