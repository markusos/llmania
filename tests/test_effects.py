from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.effects.damage_effect import DamageEffect
from src.effects.healing_effect import HealingEffect
from src.effects.invisibility_effect import InvisibilityEffect
from src.effects.teleport_effect import TeleportEffect
from src.game_engine import GameEngine
from src.player import Player


class TestEffects(unittest.TestCase):
    def setUp(self):
        with (
            patch("src.game_engine.WorldGenerator") as mock_world_gen,
            patch("src.game_engine.InputHandler"),
            patch("src.game_engine.Renderer"),
            patch("src.game_engine.CommandProcessor"),
            patch("src.game_engine.Parser"),
            patch("src.game_engine.curses"),
        ):
            mock_map = MagicMock()
            mock_map.width = 20
            mock_map.height = 10
            mock_map.get_tile.return_value.type = "floor"
            mock_world_gen.return_value.generate_world.return_value = (
                {0: mock_map},
                (1, 1, 0),
                (5, 5, 0),
                [],
            )
            # Use a fixed seed for deterministic test behavior
            self.game_engine = GameEngine(debug_mode=True, seed=12345)
            self.player = self.game_engine.player

    def test_healing_effect(self):
        player = Player(x=1, y=1, health=50, current_floor_id=0)
        player.max_health = 100
        effect = HealingEffect(heal_amount=10)
        message = effect.apply(player, self.game_engine)
        self.assertEqual(player.health, 60)
        self.assertEqual(message, "You feel a warm glow and recover 10 HP.")

    def test_teleport_effect(self):
        effect = TeleportEffect()

        # Create a proper mock that returns different floor tiles
        # to ensure teleportation has multiple options
        mock_map = MagicMock()
        mock_map.width = 20
        mock_map.height = 10

        def mock_get_tile(x, y):
            tile = MagicMock()
            # Make all tiles walkable floors
            tile.type = "floor"
            return tile

        mock_map.get_tile = mock_get_tile
        self.game_engine.world_maps[0] = mock_map

        message = effect.apply(self.player, self.game_engine)

        # The message should indicate successful teleport
        self.assertEqual(message, "You were teleported to a new location.")
        # With seeded random (from game engine), the teleport is deterministic
        # Verify the player moved to a valid position within map bounds
        self.assertTrue(0 <= self.player.x < 20)
        self.assertTrue(0 <= self.player.y < 10)

    def test_damage_effect(self):
        effect = DamageEffect(damage_amount=10)
        message = effect.apply(self.player, self.game_engine)
        self.assertEqual(message, "The item crackles with power, ready to be thrown.")

    def test_invisibility_effect(self):
        player = Player(x=1, y=1, health=100, current_floor_id=0)
        effect = InvisibilityEffect(duration=10)
        message = effect.apply(player, self.game_engine)
        self.assertEqual(player.invisibility_turns, 10)
        self.assertEqual(
            message, "You drink the potion and become invisible for 10 turns."
        )


if __name__ == "__main__":
    unittest.main()
