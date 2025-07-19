import random
import unittest
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

from src.ai_logic.main import AILogic
from src.ai_logic.states.attacking_state import AttackingState
from src.ai_logic.states.exploring_state import ExploringState
from src.ai_logic.states.looting_state import LootingState
from src.item import Item
from src.message_log import MessageLog
from src.monster import Monster
from src.player import Player
from src.tile import Tile
from src.world_map import WorldMap


class TestAILogic(unittest.TestCase):
    def setUp(self):
        self.mock_player = MagicMock(spec=Player)
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.current_floor_id = 0
        self.mock_player.health = 100
        self.mock_player.max_health = 100
        self.mock_player.inventory = []

        self.ai_visible_maps: Dict[int, WorldMap] = {0: WorldMap(10, 10)}
        self.mock_real_world_maps: Dict[int, MagicMock] = {0: MagicMock(spec=WorldMap)}
        self.mock_real_world_maps[0].width = 10
        self.mock_real_world_maps[0].height = 10

        self.message_log = MagicMock(spec=MessageLog)

        with patch("src.ai_logic.main.TargetFinder") as self.mock_target_finder, patch(
            "src.ai_logic.main.Explorer"
        ) as self.mock_explorer:
            self.ai = AILogic(
                player=self.mock_player,
                real_world_maps=self.mock_real_world_maps,
                ai_visible_maps=self.ai_visible_maps,
                message_log=self.message_log,
                random_generator=random.Random(),
            )
            self.ai.target_finder.find_health_potions.return_value = []

    def _create_floor_layout(
        self,
        floor_id: int,
        width: int,
        height: int,
        layout: list[str],
        is_ai_map: bool = True,
    ) -> WorldMap:
        world_map = WorldMap(width, height)
        for r, row_str in enumerate(layout):
            for c, char in enumerate(row_str):
                tile_type = "wall"
                item = None
                monster = None
                portal_to_floor_id = None

                if char == ".":
                    tile_type = "floor"
                elif char == "#":
                    tile_type = "wall"
                elif char == "S":
                    tile_type = "floor"
                elif char == "G":
                    tile_type = "floor"
                elif char == "M":
                    tile_type = "floor"
                    monster = Monster(
                        "TestMonster",
                        10,
                        2,
                        random.Random(),
                        x=c,
                        y=r,
                    )
                elif char.isdigit():
                    tile_type = "portal"
                    portal_to_floor_id = int(char)
                elif char == "R":
                    tile_type = "floor"
                    item = Item(name="Rock", description="A plain rock", properties={})

                tile = Tile(
                    tile_type=tile_type,
                    monster=monster,
                    item=item,
                    portal_to_floor_id=portal_to_floor_id,
                )
                if tile_type == "portal":
                    tile.is_portal = True

                world_map.grid[r][c] = tile
                world_map.grid[r][c].is_explored = True

        if is_ai_map:
            self.ai_visible_maps[floor_id] = world_map
            if floor_id not in self.mock_real_world_maps:
                mock_real_map = MagicMock(spec=WorldMap)
                mock_real_map.width = width
                mock_real_map.height = height
                mock_real_map.get_tile.side_effect = (
                    lambda mx, my, current_map=world_map: current_map.get_tile(mx, my)
                )
                self.mock_real_world_maps[floor_id] = mock_real_map
        else:
            real_map_mock_local = MagicMock(spec=WorldMap)
            real_map_mock_local.width = width
            real_map_mock_local.height = height
            real_map_mock_local.grid = world_map.grid
            real_map_mock_local.get_tile.side_effect = (
                lambda mx, my: world_map.get_tile(mx, my)
            )
            self.mock_real_world_maps[floor_id] = real_map_mock_local
        return world_map

    def _setup_tile_at(
        self,
        floor_id: int,
        x: int,
        y: int,
        item=None,
        monster=None,
        explored=True,
        tile_type="floor",
        portal_to: Optional[int] = None,
    ):
        if floor_id not in self.ai_visible_maps:
            self.ai_visible_maps[floor_id] = WorldMap(10, 10)
            if floor_id not in self.mock_real_world_maps:
                self.mock_real_world_maps[floor_id] = MagicMock(spec=WorldMap)
                tile = Tile(tile_type="floor")
                tile.is_explored = True
                self.mock_real_world_maps[floor_id].get_tile.return_value = tile

        target_map = self.ai_visible_maps[floor_id]
        tile = target_map.get_tile(x, y)
        if not tile:
            tile = Tile()
            target_map.grid[y][x] = tile

        if tile:
            tile.item = item
        tile.monster = monster
        tile.type = tile_type
        tile.is_explored = explored
        tile.is_portal = portal_to is not None
        tile.portal_to_floor_id = portal_to

        if floor_id in self.mock_real_world_maps:
            mock_real_tile = Tile(
                tile_type=tile_type,
                item=item,
                monster=monster,
                portal_to_floor_id=portal_to,
            )
            mock_real_tile.is_portal = portal_to is not None

            original_side_effect = self.mock_real_world_maps[
                floor_id
            ].get_tile.side_effect

            def new_side_effect(
                mx,
                my,
                current_x_val=x,
                current_y_val=y,
                new_tile_val=mock_real_tile,
                orig_effect_val=original_side_effect,
            ):
                if mx == current_x_val and my == current_y_val:
                    return new_tile_val
                if orig_effect_val and callable(orig_effect_val):
                    try:
                        return orig_effect_val(mx, my)
                    except TypeError:
                        return Tile(tile_type="floor")
                return Tile(tile_type="floor")

            self.mock_real_world_maps[floor_id].get_tile.side_effect = new_side_effect
        return tile

    def test_ai_transitions_to_looting_state(self):
        self.mock_player.current_floor_id = 0
        sword_item = MagicMock(spec=Item)
        sword_item.name = "Sword"
        sword_item.properties = {}
        self._setup_tile_at(0, self.mock_player.x, self.mock_player.y, item=sword_item)

        self.ai.get_next_action()
        self.assertIsInstance(self.ai.state, LootingState)

    def test_ai_transitions_to_attacking_state(self):
        self.mock_player.current_floor_id = 0
        monster_mock = Monster(
            "Goblin",
            10,
            3,
            random.Random(),
            x=self.mock_player.x + 1,
            y=self.mock_player.y,
        )
        self._setup_tile_at(
            0, self.mock_player.x + 1, self.mock_player.y, monster=monster_mock
        )

        self.ai.get_next_action()
        self.assertIsInstance(self.ai.state, AttackingState)

    def test_ai_explores_when_no_other_targets(self):
        self.ai.target_finder.find_quest_items.return_value = []
        self.ai.target_finder.find_health_potions.return_value = []
        self.ai.target_finder.find_other_items.return_value = []
        self.ai.target_finder.find_monsters.return_value = []
        self.ai.explorer.find_unvisited_portals.return_value = []
        self.ai.explorer.find_portal_to_unexplored_floor.return_value = []
        self.ai.explorer.find_exploration_targets.return_value = [
            (1, 2, 0),
            (1, 1, 0),
        ]

        self.ai.get_next_action()
        self.assertIsInstance(self.ai.state, ExploringState)
        self.assertIsNotNone(self.ai.current_path)

    def test_ai_prioritizes_exploration_over_portals(self):
        # Setup: Player on a floor with unexplored areas and a portal
        self.mock_player.x, self.mock_player.y, self.mock_player.current_floor_id = (
            1,
            1,
            0,
        )
        self._create_floor_layout(
            0, 5, 5, [".....", ".S.1.", ".....", ".....", "....."]
        )
        self.ai.explorer.find_exploration_targets.return_value = [
            (1, 2, 0),
            (1, 1, 0),
        ]
        self.ai.explorer.find_unvisited_portals.return_value = [
            (3, 1, 0, "unvisited_portal", 2)
        ]

        # Action should be to explore, not use the portal
        self.ai.get_next_action()
        self.assertIsNotNone(self.ai.current_path)
        # Verify that the target is an exploration target, not the portal
        self.assertNotEqual(self.ai.current_path[-1], (3, 1, 0))

    def test_ai_breaks_out_of_stuck_loop(self):
        self.ai.player_pos_history = [(1, 1), (1, 2), (1, 1), (1, 2)]
        self.ai.current_path = [(1, 3, 0)]
        self.ai.explorer.find_exploration_targets.return_value = None
        self.ai.get_next_action()
        self.assertIsNone(self.ai.current_path)


if __name__ == "__main__":
    unittest.main()
