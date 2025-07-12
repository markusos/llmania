import unittest
from typing import Dict, Optional  # Optional is now imported
from unittest.mock import MagicMock, patch

from src.ai_logic import AILogic
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
        self.mock_player.health = 20
        self.mock_player.max_health = 100
        self.mock_player.inventory = []

        self.ai_visible_maps: Dict[int, WorldMap] = {0: WorldMap(10, 10)}
        self.mock_real_world_maps: Dict[int, MagicMock] = {0: MagicMock(spec=WorldMap)}
        self.mock_real_world_maps[0].width = 10
        self.mock_real_world_maps[0].height = 10

        self.message_log = MagicMock(spec=MessageLog)

        self.ai = AILogic(
            player=self.mock_player,
            real_world_maps=self.mock_real_world_maps,
            ai_visible_maps=self.ai_visible_maps,
            message_log=self.message_log,
        )

        self.current_tile_f0 = self.ai_visible_maps[0].get_tile(
            self.mock_player.x, self.mock_player.y
        )
        if self.current_tile_f0:
            self.current_tile_f0.type = "floor"
            self.current_tile_f0.is_explored = True
            self.current_tile_f0.item = None
            self.current_tile_f0.monster = None

        def default_real_get_tile_f0(x, y):
            tile = Tile(tile_type="floor")
            tile.is_explored = True
            return tile

        self.mock_real_world_maps[0].get_tile.side_effect = default_real_get_tile_f0
        self.mock_real_world_maps[0].is_valid_move.return_value = True

        for r_idx in range(self.ai_visible_maps[0].height):
            for c_idx in range(self.ai_visible_maps[0].width):
                tile = self.ai_visible_maps[0].get_tile(c_idx, r_idx)
                if tile:
                    tile.type = "floor"
                    tile.is_explored = True

        self.ai.physically_visited_coords = []
        self.ai.last_move_command = None

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
                        name="TestMonster", health=10, attack_power=2, x=c, y=r
                    )
                elif char.isdigit():
                    tile_type = "portal"
                    portal_to_floor_id = int(char)

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
                self.mock_real_world_maps[floor_id].get_tile.return_value = Tile(
                    tile_type="floor", is_explored=True
                )

        target_map = self.ai_visible_maps[floor_id]
        tile = target_map.get_tile(x, y)
        if not tile:
            tile = Tile()
            target_map.grid[y][x] = tile

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

    def test_ai_takes_quest_item_on_current_floor(self):
        self.mock_player.current_floor_id = 0
        quest_item = MagicMock(spec=Item)
        quest_item.name = "Amulet of Yendor"
        quest_item.properties = {"type": "quest"}

        player_tile_ai = self.ai_visible_maps[0].get_tile(
            self.mock_player.x, self.mock_player.y
        )
        if player_tile_ai:
            player_tile_ai.item = quest_item

        real_tile_with_item = Tile(tile_type="floor", item=quest_item)
        self.mock_real_world_maps[0].get_tile.side_effect = (
            lambda rx, ry: real_tile_with_item
            if rx == self.mock_player.x and ry == self.mock_player.y
            else Tile(tile_type="floor")
        )

        action = self.ai.get_next_action()
        self.assertEqual(action, ("take", quest_item.name))
        self.message_log.add_message.assert_any_call(
            f"AI: Found quest item {quest_item.name}!"
        )

    def test_ai_uses_health_potion_when_low_health_on_current_floor(self):
        self.mock_player.current_floor_id = 0
        self.mock_player.health = 5
        potion = MagicMock(spec=Item)
        potion.name = "Health Potion"
        potion.properties = {"type": "heal"}
        self.mock_player.inventory = [potion]

        action = self.ai.get_next_action()
        self.assertEqual(action, ("use", "Health Potion"))
        self.message_log.add_message.assert_any_call(
            "AI: Low health, using Health Potion from inventory."
        )

    def test_ai_does_not_use_health_potion_if_not_present_current_floor(self):
        self.mock_player.current_floor_id = 0
        self.mock_player.health = 5
        self.mock_player.inventory = []

        self.ai_visible_maps[0].is_valid_move = MagicMock(return_value=False)
        self.mock_real_world_maps[0].is_valid_move = MagicMock(return_value=False)

        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        for call_args in self.message_log.add_message.call_args_list:
            self.assertNotIn("AI: Low health, using Health Potion.", call_args[0][0])

    def test_ai_takes_regular_item_current_floor(self):
        self.mock_player.current_floor_id = 0
        self.mock_player.health = 20
        sword_item = MagicMock(spec=Item)
        sword_item.name = "Sword"
        sword_item.properties = {}

        player_tile_ai = self.ai_visible_maps[0].get_tile(
            self.mock_player.x, self.mock_player.y
        )
        if player_tile_ai:
            player_tile_ai.item = sword_item

        real_tile_with_item = Tile(tile_type="floor", item=sword_item)
        self.mock_real_world_maps[0].get_tile.side_effect = (
            lambda rx, ry: real_tile_with_item
            if rx == self.mock_player.x and ry == self.mock_player.y
            else Tile(tile_type="floor")
        )

        action = self.ai.get_next_action()
        self.assertEqual(action, ("take", "Sword"))
        self.message_log.add_message.assert_any_call(
            "AI: Found item Sword on current tile, taking it."
        )

    def test_ai_attacks_adjacent_monster_current_floor(self):
        self.mock_player.current_floor_id = 0
        monster_mock = Monster(
            name="Goblin",
            health=10,
            attack_power=3,
            x=self.mock_player.x + 1,
            y=self.mock_player.y,
        )

        self._setup_tile_at(
            0, self.mock_player.x + 1, self.mock_player.y, monster=monster_mock
        )

        real_monster_tile = Tile(tile_type="floor", monster=monster_mock)

        def real_map_get_tile_monster(rx, ry):
            if rx == self.mock_player.x + 1 and ry == self.mock_player.y:
                return real_monster_tile
            if rx == self.mock_player.x and ry == self.mock_player.y:
                return Tile(tile_type="floor")
            return Tile(tile_type="floor")

        self.mock_real_world_maps[0].get_tile.side_effect = real_map_get_tile_monster

        action = self.ai.get_next_action()
        self.assertEqual(action, ("attack", "Goblin"))
        self.message_log.add_message.assert_any_call("AI: Attacking adjacent Goblin.")

    @patch("src.ai_logic.random.choice")
    def test_ai_attacks_one_of_multiple_adj_monsters_current_floor(
        self, mock_random_choice
    ):
        self.mock_player.current_floor_id = 0
        monster1 = Monster(
            name="Orc",
            health=15,
            attack_power=4,
            x=self.mock_player.x,
            y=self.mock_player.y - 1,
        )
        monster2 = Monster(
            name="Slime",
            health=5,
            attack_power=1,
            x=self.mock_player.x + 1,
            y=self.mock_player.y,
        )
        mock_random_choice.return_value = monster1

        self._setup_tile_at(
            0, self.mock_player.x, self.mock_player.y - 1, monster=monster1
        )
        self._setup_tile_at(
            0, self.mock_player.x + 1, self.mock_player.y, monster=monster2
        )

        action = self.ai.get_next_action()
        self.assertEqual(action, ("attack", "Orc"))
        self.message_log.add_message.assert_any_call("AI: Attacking adjacent Orc.")

    def test_ai_explores_unvisited_tile_current_floor(self):
        self.mock_player.x = 0
        self.mock_player.y = 0
        self.mock_player.current_floor_id = 0
        self.ai_visible_maps[0] = self._create_floor_layout(
            0, 3, 3, ["S..", ".#.", ".#."]
        )
        self.mock_player.x = 0
        self.mock_player.y = 0
        self.ai.physically_visited_coords = [(0, 0, 0), (0, 1, 0)]

        self.ai.get_next_action()  # F841: Removed assignment to 'action'
        self.assertIsNotNone(self.ai.current_path)
        if self.ai.current_path:
            self.assertEqual(
                self.ai.current_path[-1],
                (1, 0, 0),
                "AI should target the closest unvisited floor tile.",
            )
        self.assertTrue(
            any(
                (
                    f"AI: Pathing to explore unvisited tile at "
                    f"({self.ai.current_path[-1][0]},{self.ai.current_path[-1][1]}) "
                    f"on current floor."
                )
                in str(call_args)
                for call_args in self.message_log.add_message.call_args_list
            ),
            "Log message for exploring unvisited tile not found or incorrect.",
        )

    @patch("src.ai_logic.random.choice")
    def test_ai_explores_randomly_when_all_neighbors_visited_current_floor(
        self, mock_random_choice
    ):
        self.mock_player.x = 1
        self.mock_player.y = 1
        self.mock_player.current_floor_id = 0

        self.ai_visible_maps[0] = self._create_floor_layout(
            0, 3, 3, ["...", ".S.", "..."], is_ai_map=True
        )
        # F841: Removed real_map_f0 assignment
        self._create_floor_layout(0, 3, 3, ["...", ".S.", "..."], is_ai_map=False)
        self.mock_player.x = 1
        self.mock_player.y = 1

        self.ai.physically_visited_coords = [
            (1, 1, 0),
            (0, 1, 0),
            (2, 1, 0),
            (1, 0, 0),
            (1, 2, 0),
        ]

        for r_idx in range(self.ai_visible_maps[0].height):
            for c_idx in range(self.ai_visible_maps[0].width):
                tile = self.ai_visible_maps[0].get_tile(c_idx, r_idx)
                if tile:
                    tile.item = None
                    tile.monster = None

                real_tile = self.mock_real_world_maps[0].get_tile(c_idx, r_idx)
                if real_tile:
                    real_tile.item = None
                    real_tile.monster = None

        self.ai.path_finder.find_path_bfs = MagicMock(return_value=None)
        mock_random_choice.return_value = ("move", "east")
        self.message_log.reset_mock()
        action = self.ai.get_next_action()
        self.assertEqual(action, ("move", "east"))

        actual_log_calls = self.message_log.add_message.call_args_list
        self.assertTrue(
            any(
                c.args[0] == "AI: No path found for any target or exploration."
                for c in actual_log_calls
                if c.args
            ),
            "Log 'No path found for any target or exploration.' not found.",
        )

        self.assertEqual(
            len(actual_log_calls),
            2,
            f"Expected 2 logs, got {len(actual_log_calls)}. Calls: {actual_log_calls}",
        )
        if len(actual_log_calls) == 2:
            actual_msg_text = str(actual_log_calls[1].args[0])
            self.assertIn(
                "AI: All nearby visited",
                actual_msg_text,
                f"Substring 'AI: All nearby visited' not in '{actual_msg_text}'",
            )
            self.assertIn(
                "on current floor",
                actual_msg_text,
                f"Substring 'on current floor' not in '{actual_msg_text}'",
            )
            self.assertIn(
                "Moving east",
                actual_msg_text,
                f"Substring 'Moving east' not in '{actual_msg_text}'",
            )

        possible_random_moves = [
            ("move", "north"),
            ("move", "south"),
            ("move", "west"),
            ("move", "east"),
        ]
        mock_random_choice.assert_called_once_with(possible_random_moves)

    def test_ai_looks_when_stuck_current_floor(self):
        self.mock_player.current_floor_id = 0
        self.ai_visible_maps[0] = self._create_floor_layout(0, 1, 1, ["S"])
        self.mock_player.x = 0
        self.mock_player.y = 0

        self.ai.path_finder.find_path_bfs = MagicMock(return_value=None)

        action = self.ai.get_next_action()
        self.assertEqual(action, ("look", None))
        self.message_log.add_message.assert_any_call(
            "AI: No actions available. Looking around."
        )
        self.assertEqual(self.ai.last_move_command, ("look", None))

    def test_ai_paths_to_quest_item_on_different_floor(self):
        self._create_floor_layout(0, 3, 1, ["S.1"], is_ai_map=True)
        self._create_floor_layout(1, 3, 1, ["G.0"], is_ai_map=True)
        self.mock_player.x = 0
        self.mock_player.y = 0
        self.mock_player.current_floor_id = 0

        quest_item = Item(
            name="Amulet", description="Quest item", properties={"type": "quest"}
        )
        self._setup_tile_at(1, 0, 0, item=quest_item)

        action = self.ai.get_next_action()

        self.assertIsNotNone(
            self.ai.current_path,
            "AI should find a path to the quest item on another floor.",
        )
        if self.ai.current_path:
            self.assertEqual(
                self.ai.current_path[-1],
                (0, 0, 1),
                "Path should end at quest item on floor 1.",
            )
            self.assertEqual(
                action, ("move", "east"), "AI should move towards the portal."
            )
        self.message_log.add_message.assert_any_call(
            "AI: Pathing to quest_item at (0,0) on floor 1."
        )


if __name__ == "__main__":
    unittest.main()
