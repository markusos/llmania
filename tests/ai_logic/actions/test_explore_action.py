"""Tests for ExploreAction."""

from unittest.mock import Mock

from src.ai_logic.actions.explore_action import ExploreAction
from src.ai_logic.context import AIContext


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
    return AIContext(**defaults)  # type: ignore[arg-type]


class TestExploreAction:
    """Test suite for ExploreAction."""

    def test_is_available_returns_false_when_no_explorer(self):
        """Test is_available returns False when explorer is None."""
        action = ExploreAction()
        ctx = create_mock_context(explorer=None)
        assert action.is_available(ctx) is False

    def test_is_available_returns_false_when_floor_fully_explored(self):
        """Test is_available returns False when no unexplored tiles."""
        action = ExploreAction()

        mock_explorer = Mock()
        mock_explorer.find_exploration_targets.return_value = None

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_unexplored_tiles_exist(self):
        """Test is_available returns True when unexplored tiles exist."""
        action = ExploreAction()

        mock_explorer = Mock()
        mock_explorer.find_exploration_targets.return_value = [(10, 10, 0)]

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_0_35_when_available(self):
        """Test calculate_utility returns 0.35 when same-floor exploration available."""
        action = ExploreAction()

        mock_explorer = Mock()
        # Return a path to the same floor (floor_id=0)
        mock_explorer.find_exploration_targets.return_value = [(10, 10, 0)]

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.calculate_utility(ctx) == 0.35

    def test_calculate_utility_returns_0_50_for_cross_floor_exploration(self):
        """Test calculate_utility returns 0.50 for cross-floor exploration."""
        action = ExploreAction()

        mock_explorer = Mock()
        # Return a path to a different floor (floor_id=1 while player is on floor 0)
        mock_explorer.find_exploration_targets.return_value = [(10, 10, 1)]

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.calculate_utility(ctx) == 0.50

    def test_calculate_utility_returns_0_when_not_available(self):
        """Test calculate_utility returns 0.0 when exploration not available."""
        action = ExploreAction()

        mock_explorer = Mock()
        mock_explorer.find_exploration_targets.return_value = None

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.calculate_utility(ctx) == 0.0

    def test_execute_sets_path_and_returns_move_command(self):
        """Test execute paths to nearest exploration frontier."""
        action = ExploreAction()

        mock_explorer = Mock()
        # Return a path to an unexplored area
        mock_explorer.find_exploration_targets.return_value = [
            (6, 5, 0),  # One step east
            (7, 5, 0),
            (8, 5, 0),
        ]

        ctx = create_mock_context(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            explorer=mock_explorer,
        )

        mock_ai_logic = Mock()
        mock_ai_logic.current_path = None
        mock_ai_logic._coordinates_to_move_command.return_value = ("move", "east")

        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)

        assert result == ("move", "east")
        assert mock_ai_logic.current_path is not None
        mock_message_log.add_message.assert_called()

    def test_execute_returns_none_when_no_explorer(self):
        """Test execute returns None when explorer is None."""
        action = ExploreAction()
        ctx = create_mock_context(explorer=None)

        mock_ai_logic = Mock()
        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)
        assert result is None

    def test_execute_returns_none_when_no_exploration_path(self):
        """Test execute returns None when no exploration path found."""
        action = ExploreAction()

        mock_explorer = Mock()
        mock_explorer.find_exploration_targets.return_value = None

        ctx = create_mock_context(explorer=mock_explorer)

        mock_ai_logic = Mock()
        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)
        assert result is None
