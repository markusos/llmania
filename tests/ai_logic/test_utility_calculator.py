"""Tests for UtilityCalculator."""

from unittest.mock import Mock

from src.ai_logic.context import AIContext
from src.ai_logic.utility_calculator import UtilityCalculator


def create_mock_context(**kwargs):
    """Create a mock AIContext with default values."""
    defaults = {
        "player_x": 5,
        "player_y": 5,
        "player_floor_id": 0,
        "player_health": 100,
        "player_max_health": 100,
        "player_attack": 5,
        "player_defense": 2,
        "health_ratio": 1.0,
        "survival_threshold": 0.5,
        "is_cornered": False,
        "is_in_loop": False,
        "loop_breaker_active": False,
        "adjacent_monsters": [],
        "current_tile_has_item": False,
        "current_tile_item_name": None,
        "current_tile_item": None,
        "inventory_items": [],
        "has_healing_item": False,
        "has_fire_potion": False,
        "equipped_items": {},
        "current_path": None,
        "visible_maps": {},
        "path_finder": None,
        "bestiary": None,
        "explorer": None,
        "target_finder": None,
        "random": None,
    }
    defaults.update(kwargs)
    return AIContext(**defaults)


class TestUtilityCalculator:
    """Test suite for UtilityCalculator."""

    def test_returns_none_when_no_actions_available(self):
        """Test that select_action returns None when no actions available."""
        # Create a mock action that's never available
        mock_action = Mock()
        mock_action.is_available.return_value = False
        mock_action.calculate_utility.return_value = 0.0

        calculator = UtilityCalculator([mock_action])
        ctx = create_mock_context()

        result = calculator.select_action(ctx)
        assert result is None

    def test_returns_highest_utility_action(self):
        """Test that select_action returns the highest utility action."""
        # Create mock actions with different utilities
        low_action = Mock()
        low_action.is_available.return_value = True
        low_action.calculate_utility.return_value = 0.3
        low_action.name = "LowAction"

        high_action = Mock()
        high_action.is_available.return_value = True
        high_action.calculate_utility.return_value = 0.9
        high_action.name = "HighAction"

        calculator = UtilityCalculator([low_action, high_action])
        ctx = create_mock_context()

        result = calculator.select_action(ctx)
        assert result == high_action

    def test_deterministic_ordering_when_utilities_tie(self):
        """Test that actions with same utility are ordered by name."""
        # Create mock actions with same utility
        action_b = Mock()
        action_b.is_available.return_value = True
        action_b.calculate_utility.return_value = 0.5
        action_b.name = "BAction"

        action_a = Mock()
        action_a.is_available.return_value = True
        action_a.calculate_utility.return_value = 0.5
        action_a.name = "AAction"

        # Add in reverse alphabetical order
        calculator = UtilityCalculator([action_b, action_a])
        ctx = create_mock_context()

        result = calculator.select_action(ctx)
        # Should return "AAction" (alphabetically first when utilities tie)
        assert result == action_a

    def test_get_action_scores_returns_all_actions(self):
        """Test that get_action_scores returns info for all actions."""
        action1 = Mock()
        action1.is_available.return_value = True
        action1.calculate_utility.return_value = 0.7
        action1.name = "Action1"

        action2 = Mock()
        action2.is_available.return_value = False
        action2.calculate_utility.return_value = 0.3
        action2.name = "Action2"

        calculator = UtilityCalculator([action1, action2])
        ctx = create_mock_context()

        scores = calculator.get_action_scores(ctx)
        assert len(scores) == 2

        # Check first action
        name1, score1, available1 = scores[0]
        assert name1 == "Action1"
        assert score1 == 0.7
        assert available1 is True

        # Check second action
        name2, score2, available2 = scores[1]
        assert name2 == "Action2"
        assert score2 == 0.3
        assert available2 is False

    def test_returns_none_for_zero_utility(self):
        """Test that select_action returns None when best utility is 0."""
        mock_action = Mock()
        mock_action.is_available.return_value = True
        mock_action.calculate_utility.return_value = 0.0
        mock_action.name = "ZeroAction"

        calculator = UtilityCalculator([mock_action])
        ctx = create_mock_context()

        result = calculator.select_action(ctx)
        assert result is None

    def test_execute_best_action_calls_execute(self):
        """Test that execute_best_action calls the best action's execute."""
        mock_action = Mock()
        mock_action.is_available.return_value = True
        mock_action.calculate_utility.return_value = 0.9
        mock_action.name = "MockAction"
        mock_action.execute.return_value = ("move", "north")

        calculator = UtilityCalculator([mock_action])
        ctx = create_mock_context()
        ai_logic = Mock()
        message_log = Mock()

        result = calculator.execute_best_action(ctx, ai_logic, message_log)
        assert result == ("move", "north")
        mock_action.execute.assert_called_once_with(ctx, ai_logic, message_log)

    def test_execute_best_action_returns_none_when_no_action(self):
        """Test that execute_best_action returns None when no action available."""
        mock_action = Mock()
        mock_action.is_available.return_value = False
        mock_action.calculate_utility.return_value = 0.0

        calculator = UtilityCalculator([mock_action])
        ctx = create_mock_context()
        ai_logic = Mock()
        message_log = Mock()

        result = calculator.execute_best_action(ctx, ai_logic, message_log)
        assert result is None
