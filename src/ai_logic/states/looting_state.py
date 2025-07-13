from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_state import AIState

if TYPE_CHECKING:
    pass


class LootingState(AIState):
    def handle_transitions(self) -> str:
        player = self.ai_logic.player
        if player.health <= player.max_health / 2:
            return "SurvivalState"
        if self.ai_logic._get_adjacent_monsters():
            return "AttackingState"
        # If no items are visible, switch to ExploringState
        if not self._has_visible_items():
            return "ExploringState"
        return "LootingState"

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        # 1. Use health potions if low on health
        action = self._use_item("heal")
        if action:
            return action

        # 2. Equip better weapons
        action = self._equip_better_weapon()
        if action:
            return action

        # 3. Take item on current tile
        action = self._pickup_item()
        if action:
            return action

        # 4. Pathfind to other known items
        action = self._path_to_best_target(
            self.ai_logic.target_finder.find_other_items,
        )
        if action:
            return action

        # 5. If no items to loot, explore
        return self._explore_randomly()

    def _has_visible_items(self) -> bool:
        player_pos_xy = (self.ai_logic.player.x, self.ai_logic.player.y)
        player_floor_id = self.ai_logic.player.current_floor_id
        items = self.ai_logic.target_finder.find_other_items(
            player_pos_xy, player_floor_id
        )
        return bool(items)
