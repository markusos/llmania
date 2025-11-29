"""Tests for AIContext dataclass."""

from src.ai_logic.context import AIContext


class TestAIContext:
    """Test suite for AIContext dataclass."""

    def test_context_creation(self):
        """Verify AIContext can be instantiated with all required fields."""
        ctx = AIContext(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            player_health=50,
            player_max_health=100,
            player_attack=5,
            player_defense=2,
            health_ratio=0.5,
            survival_threshold=0.5,
            is_cornered=False,
            is_in_loop=False,
            loop_breaker_active=False,
            adjacent_monsters=[],
            current_tile_has_item=False,
            current_tile_item_name=None,
            current_tile_item=None,
            inventory_items=[],
            has_healing_item=False,
            has_fire_potion=False,
            equipped_items={},
            current_path=None,
            visible_maps={},
            path_finder=None,
            bestiary=None,
            explorer=None,
            target_finder=None,
            random=None,
        )
        assert ctx.player_pos == (5, 5)
        assert ctx.health_ratio == 0.5

    def test_player_pos_property(self):
        """Test player_pos property returns (x, y) tuple."""
        ctx = AIContext(
            player_x=10,
            player_y=20,
            player_floor_id=1,
            player_health=100,
            player_max_health=100,
            player_attack=5,
            player_defense=2,
            health_ratio=1.0,
            survival_threshold=0.5,
            is_cornered=False,
            is_in_loop=False,
            loop_breaker_active=False,
            adjacent_monsters=[],
            current_tile_has_item=False,
            current_tile_item_name=None,
            current_tile_item=None,
            inventory_items=[],
            has_healing_item=False,
            has_fire_potion=False,
            equipped_items={},
            current_path=None,
            visible_maps={},
            path_finder=None,
            bestiary=None,
            explorer=None,
            target_finder=None,
            random=None,
        )
        assert ctx.player_pos == (10, 20)

    def test_player_pos_3d_property(self):
        """Test player_pos_3d property returns (x, y, floor_id) tuple."""
        ctx = AIContext(
            player_x=10,
            player_y=20,
            player_floor_id=2,
            player_health=100,
            player_max_health=100,
            player_attack=5,
            player_defense=2,
            health_ratio=1.0,
            survival_threshold=0.5,
            is_cornered=False,
            is_in_loop=False,
            loop_breaker_active=False,
            adjacent_monsters=[],
            current_tile_has_item=False,
            current_tile_item_name=None,
            current_tile_item=None,
            inventory_items=[],
            has_healing_item=False,
            has_fire_potion=False,
            equipped_items={},
            current_path=None,
            visible_maps={},
            path_finder=None,
            bestiary=None,
            explorer=None,
            target_finder=None,
            random=None,
        )
        assert ctx.player_pos_3d == (10, 20, 2)

    def test_is_low_health_true(self):
        """Test is_low_health returns True when below threshold."""
        ctx = AIContext(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            player_health=30,
            player_max_health=100,
            player_attack=5,
            player_defense=2,
            health_ratio=0.3,
            survival_threshold=0.5,
            is_cornered=False,
            is_in_loop=False,
            loop_breaker_active=False,
            adjacent_monsters=[],
            current_tile_has_item=False,
            current_tile_item_name=None,
            current_tile_item=None,
            inventory_items=[],
            has_healing_item=False,
            has_fire_potion=False,
            equipped_items={},
            current_path=None,
            visible_maps={},
            path_finder=None,
            bestiary=None,
            explorer=None,
            target_finder=None,
            random=None,
        )
        assert ctx.is_low_health() is True

    def test_is_low_health_false(self):
        """Test is_low_health returns False when above threshold."""
        ctx = AIContext(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            player_health=80,
            player_max_health=100,
            player_attack=5,
            player_defense=2,
            health_ratio=0.8,
            survival_threshold=0.5,
            is_cornered=False,
            is_in_loop=False,
            loop_breaker_active=False,
            adjacent_monsters=[],
            current_tile_has_item=False,
            current_tile_item_name=None,
            current_tile_item=None,
            inventory_items=[],
            has_healing_item=False,
            has_fire_potion=False,
            equipped_items={},
            current_path=None,
            visible_maps={},
            path_finder=None,
            bestiary=None,
            explorer=None,
            target_finder=None,
            random=None,
        )
        assert ctx.is_low_health() is False

    def test_has_adjacent_monsters_true(self):
        """Test has_adjacent_monsters returns True when monsters present."""
        from src.ai_logic.ai_monster_view import AIMonsterView

        ctx = AIContext(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            player_health=100,
            player_max_health=100,
            player_attack=5,
            player_defense=2,
            health_ratio=1.0,
            survival_threshold=0.5,
            is_cornered=False,
            is_in_loop=False,
            loop_breaker_active=False,
            adjacent_monsters=[AIMonsterView("Goblin", 4, 5)],
            current_tile_has_item=False,
            current_tile_item_name=None,
            current_tile_item=None,
            inventory_items=[],
            has_healing_item=False,
            has_fire_potion=False,
            equipped_items={},
            current_path=None,
            visible_maps={},
            path_finder=None,
            bestiary=None,
            explorer=None,
            target_finder=None,
            random=None,
        )
        assert ctx.has_adjacent_monsters() is True

    def test_has_adjacent_monsters_false(self):
        """Test has_adjacent_monsters returns False when no monsters."""
        ctx = AIContext(
            player_x=5,
            player_y=5,
            player_floor_id=0,
            player_health=100,
            player_max_health=100,
            player_attack=5,
            player_defense=2,
            health_ratio=1.0,
            survival_threshold=0.5,
            is_cornered=False,
            is_in_loop=False,
            loop_breaker_active=False,
            adjacent_monsters=[],
            current_tile_has_item=False,
            current_tile_item_name=None,
            current_tile_item=None,
            inventory_items=[],
            has_healing_item=False,
            has_fire_potion=False,
            equipped_items={},
            current_path=None,
            visible_maps={},
            path_finder=None,
            bestiary=None,
            explorer=None,
            target_finder=None,
            random=None,
        )
        assert ctx.has_adjacent_monsters() is False
