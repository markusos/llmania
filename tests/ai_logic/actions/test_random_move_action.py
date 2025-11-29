"""Tests for RandomMoveAction."""

import random
from unittest.mock import Mock

from src.ai_logic.actions.random_move_action import RandomMoveAction
from src.ai_logic.context import AIContext
from src.world_map import WorldMap


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


class TestRandomMoveAction:
    """Test suite for RandomMoveAction."""

    def test_is_available_always_returns_true(self):
        """Test is_available always returns True."""
        action = RandomMoveAction()
        ctx = create_mock_context()
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_0_10_normally(self):
        """Test calculate_utility returns 0.10 in normal mode."""
        action = RandomMoveAction()
        ctx = create_mock_context(loop_breaker_active=False)
        assert action.calculate_utility(ctx) == 0.10

    def test_calculate_utility_returns_0_99_when_loop_breaker_active(self):
        """Test calculate_utility returns 0.99 when loop_breaker_active."""
        action = RandomMoveAction()
        ctx = create_mock_context(loop_breaker_active=True)
        assert action.calculate_utility(ctx) == 0.99

    def test_execute_returns_look_when_no_map(self):
        """Test execute returns ('look', None) when no map available."""
        action = RandomMoveAction()
        ctx = create_mock_context(visible_maps={})
        ai_logic = Mock()
        message_log = Mock()

        result = action.execute(ctx, ai_logic, message_log)
        assert result == ("look", None)

    def test_execute_returns_move_command(self):
        """Test execute returns a move command when moves available."""
        # Create a simple map with open tiles
        world_map = WorldMap(width=10, height=10)
        for y in range(10):
            for x in range(10):
                tile = world_map.get_tile(x, y)
                if tile:
                    tile.type = "floor"

        action = RandomMoveAction()
        ctx = create_mock_context(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            visible_maps={0: world_map},
            random=random.Random(42),
        )
        ai_logic = Mock()
        ai_logic.last_move_command = None
        message_log = Mock()

        result = action.execute(ctx, ai_logic, message_log)
        assert result is not None
        assert result[0] == "move"
        assert result[1] in ["north", "south", "east", "west"]
