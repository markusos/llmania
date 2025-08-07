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
            self.game_engine = GameEngine(debug_mode=True)
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
        with patch.object(self.game_engine.world_maps[0], "get_tile") as mock_get_tile:
            mock_tile = MagicMock()
            mock_tile.type = "floor"
            mock_get_tile.return_value = mock_tile
            message = effect.apply(self.player, self.game_engine)
        self.assertNotEqual((self.player.x, self.player.y), (1, 1))
        self.assertEqual(message, "You were teleported to a new location.")

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
