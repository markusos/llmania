"""Tests for PathTo* Actions."""

from unittest.mock import Mock

from src.ai_logic.actions.path_actions import (
    PathToArmorAction,
    PathToHealthAction,
    PathToLootAction,
    PathToPortalAction,
    PathToQuestAction,
    PathToWeaponAction,
    apply_distance_modifier,
)
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


class TestDistanceModifier:
    """Tests for the distance modifier utility function."""

    def test_distance_0_returns_full_utility(self):
        """Test distance 0 returns full base utility."""
        assert apply_distance_modifier(1.0, 0) == 1.0

    def test_distance_50_returns_half_utility(self):
        """Test distance 50 returns 50% of base utility."""
        assert apply_distance_modifier(1.0, 50) == 0.5

    def test_distance_100_returns_minimum_utility(self):
        """Test distance 100+ returns minimum 50% of base."""
        assert apply_distance_modifier(1.0, 100) == 0.5
        assert apply_distance_modifier(1.0, 200) == 0.5

    def test_distance_modifier_scales_base_utility(self):
        """Test distance modifier scales with base utility."""
        assert apply_distance_modifier(0.7, 0) == 0.7
        assert apply_distance_modifier(0.7, 50) == 0.35


class TestPathToHealthAction:
    """Test suite for PathToHealthAction."""

    def test_is_available_returns_false_when_health_above_70_percent(self):
        """Test is_available returns False when health >= 70%."""
        action = PathToHealthAction()

        mock_target_finder = Mock()
        mock_target_finder.find_health_potions.return_value = [(10, 10, 0, "potion", 5)]

        ctx = create_mock_context(
            health_ratio=0.8,
            target_finder=mock_target_finder,
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_false_when_no_potions(self):
        """Test is_available returns False when no health potions visible."""
        action = PathToHealthAction()

        mock_target_finder = Mock()
        mock_target_finder.find_health_potions.return_value = []

        ctx = create_mock_context(
            health_ratio=0.5,
            target_finder=mock_target_finder,
        )
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_low_health_and_potion_visible(self):
        """Test is_available returns True when health < 70% and potion visible."""
        action = PathToHealthAction()

        mock_target_finder = Mock()
        mock_target_finder.find_health_potions.return_value = [(10, 10, 0, "potion", 5)]

        ctx = create_mock_context(
            health_ratio=0.5,
            target_finder=mock_target_finder,
        )
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_base_0_70(self):
        """Test calculate_utility returns base utility of 0.70."""
        action = PathToHealthAction()

        mock_target_finder = Mock()
        # (x, y, floor_id, type, distance)
        mock_target_finder.find_health_potions.return_value = [(10, 10, 0, "potion", 0)]

        ctx = create_mock_context(
            health_ratio=0.5,
            target_finder=mock_target_finder,
        )
        # Distance 0 should give full base utility
        assert action.calculate_utility(ctx) == 0.70


class TestPathToWeaponAction:
    """Test suite for PathToWeaponAction."""

    def test_is_available_returns_false_when_no_weapons(self):
        """Test is_available returns False when no weapons visible."""
        action = PathToWeaponAction()

        mock_target_finder = Mock()
        mock_target_finder.find_weapons.return_value = []

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_weapon_visible(self):
        """Test is_available returns True when better weapon visible."""
        action = PathToWeaponAction()

        mock_target_finder = Mock()
        mock_target_finder.find_weapons.return_value = [(10, 10, 0, "sword", 5)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_base_0_65(self):
        """Test calculate_utility returns base utility of 0.65."""
        action = PathToWeaponAction()

        mock_target_finder = Mock()
        mock_target_finder.find_weapons.return_value = [(10, 10, 0, "sword", 0)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.calculate_utility(ctx) == 0.65


class TestPathToArmorAction:
    """Test suite for PathToArmorAction."""

    def test_is_available_returns_false_when_no_armor(self):
        """Test is_available returns False when no armor visible."""
        action = PathToArmorAction()

        mock_target_finder = Mock()
        mock_target_finder.find_armor.return_value = []

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_armor_visible(self):
        """Test is_available returns True when armor visible."""
        action = PathToArmorAction()

        mock_target_finder = Mock()
        mock_target_finder.find_armor.return_value = [(10, 10, 0, "helmet", 5)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_base_0_60(self):
        """Test calculate_utility returns base utility of 0.60."""
        action = PathToArmorAction()

        mock_target_finder = Mock()
        mock_target_finder.find_armor.return_value = [(10, 10, 0, "helmet", 0)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.calculate_utility(ctx) == 0.60


class TestPathToQuestAction:
    """Test suite for PathToQuestAction."""

    def test_is_available_returns_false_when_no_quest_items(self):
        """Test is_available returns False when no quest items visible."""
        action = PathToQuestAction()

        mock_target_finder = Mock()
        mock_target_finder.find_quest_items.return_value = []

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_quest_item_visible(self):
        """Test is_available returns True when quest item visible."""
        action = PathToQuestAction()

        mock_target_finder = Mock()
        mock_target_finder.find_quest_items.return_value = [(10, 10, 0, "gem", 5)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_base_0_55(self):
        """Test calculate_utility returns base utility of 0.55."""
        action = PathToQuestAction()

        mock_target_finder = Mock()
        mock_target_finder.find_quest_items.return_value = [(10, 10, 0, "gem", 0)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.calculate_utility(ctx) == 0.55


class TestPathToPortalAction:
    """Test suite for PathToPortalAction."""

    def test_is_available_returns_false_when_no_portals(self):
        """Test is_available returns False when no unvisited portals."""
        action = PathToPortalAction()

        mock_explorer = Mock()
        mock_explorer.find_unvisited_portals.return_value = []
        mock_explorer.find_portal_to_unexplored_floor.return_value = []

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_portal_visible(self):
        """Test is_available returns True when unvisited portal visible."""
        action = PathToPortalAction()

        mock_explorer = Mock()
        mock_explorer.find_unvisited_portals.return_value = [(10, 10, 0, "portal", 5)]
        mock_explorer.find_portal_to_unexplored_floor.return_value = []

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_base_0_45(self):
        """Test utility returns 0.45 when floor < 80% explored."""
        action = PathToPortalAction()

        mock_explorer = Mock()
        mock_explorer.find_unvisited_portals.return_value = [(10, 10, 0, "portal", 0)]
        mock_explorer.find_portal_to_unexplored_floor.return_value = []
        mock_explorer.get_floor_exploration_ratio.return_value = 0.5  # < 80%

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.calculate_utility(ctx) == 0.45

    def test_calculate_utility_returns_0_55_when_floor_mostly_explored(self):
        """Test calculate_utility returns 0.55 when floor > 80% explored."""
        action = PathToPortalAction()

        mock_explorer = Mock()
        mock_explorer.find_unvisited_portals.return_value = [(10, 10, 0, "portal", 0)]
        mock_explorer.find_portal_to_unexplored_floor.return_value = []
        mock_explorer.get_floor_exploration_ratio.return_value = 0.9  # > 80%

        ctx = create_mock_context(explorer=mock_explorer)
        assert action.calculate_utility(ctx) == 0.55


class TestPathToLootAction:
    """Test suite for PathToLootAction."""

    def test_is_available_returns_false_when_no_loot(self):
        """Test is_available returns False when no other items visible."""
        action = PathToLootAction()

        mock_target_finder = Mock()
        mock_target_finder.find_other_items.return_value = []

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is False

    def test_is_available_returns_true_when_loot_visible(self):
        """Test is_available returns True when other items visible."""
        action = PathToLootAction()

        mock_target_finder = Mock()
        mock_target_finder.find_other_items.return_value = [(10, 10, 0, "gold", 5)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.is_available(ctx) is True

    def test_calculate_utility_returns_base_0_40(self):
        """Test calculate_utility returns base utility of 0.40."""
        action = PathToLootAction()

        mock_target_finder = Mock()
        mock_target_finder.find_other_items.return_value = [(10, 10, 0, "gold", 0)]

        ctx = create_mock_context(target_finder=mock_target_finder)
        assert action.calculate_utility(ctx) == 0.40


class TestPathActionExecution:
    """Test execute behavior for path actions."""

    def test_execute_sets_path_and_returns_move_command(self):
        """Test execute sets ai_logic.current_path and returns move command."""
        action = PathToWeaponAction()

        mock_target_finder = Mock()
        mock_target_finder.find_weapons.return_value = [(6, 5, 0, "sword", 1)]

        mock_path_finder = Mock()
        mock_path_finder.find_path_bfs.return_value = [(5, 5, 0), (6, 5, 0)]

        ctx = create_mock_context(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            target_finder=mock_target_finder,
            path_finder=mock_path_finder,
        )

        mock_ai_logic = Mock()
        mock_ai_logic.current_path = None
        mock_ai_logic._coordinates_to_move_command.return_value = ("move", "east")

        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)

        assert result == ("move", "east")
        assert mock_ai_logic.current_path is not None
        mock_message_log.add_message.assert_called()

    def test_execute_returns_none_when_no_path_found(self):
        """Test execute returns None when pathfinding fails."""
        action = PathToWeaponAction()

        mock_target_finder = Mock()
        mock_target_finder.find_weapons.return_value = [(10, 10, 0, "sword", 5)]

        mock_path_finder = Mock()
        mock_path_finder.find_path_bfs.return_value = None

        ctx = create_mock_context(
            target_finder=mock_target_finder,
            path_finder=mock_path_finder,
        )

        mock_ai_logic = Mock()
        mock_message_log = Mock()

        result = action.execute(ctx, mock_ai_logic, mock_message_log)
        assert result is None
