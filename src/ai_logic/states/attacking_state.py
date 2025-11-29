from __future__ import annotations

from typing import Optional, Tuple

from src.ai_logic.bestiary import Bestiary

from .base_state import AIState


class AttackingState(AIState):
    def handle_transitions(self) -> str:
        # Use dynamic survival threshold instead of fixed 50%
        if self.ai_logic.should_enter_survival_mode():
            return "SurvivalState"
        if not self.ai_logic._get_adjacent_monsters():
            return "ExploringState"
        return "AttackingState"

    def _should_use_combat_item(self, monster_name: str) -> Optional[str]:
        """Check if we should use a combat item against this monster."""
        bestiary = Bestiary.get_instance()
        vulnerability = bestiary.get_vulnerability(monster_name)

        # Get fire potions from inventory (damage items with fire effect)
        fire_potions = [
            item
            for item in self.ai_logic.player_view.inventory_items
            if "fire" in item.name.lower()
            and any(
                effect.get("type") == "damage"
                for effect in item.properties.get("effects", [])
            )
        ]

        # Use fire potion against fire-vulnerable monsters (e.g., Troll)
        if vulnerability == "fire" and fire_potions:
            return fire_potions[0].name

        # Use fire potion against groups of 2+ monsters (area damage is efficient)
        adjacent_count = len(self.ai_logic._get_adjacent_monsters())
        if adjacent_count >= 2 and fire_potions:
            return fire_potions[0].name

        return None

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        # Check if we should heal before fighting
        if self.ai_logic.should_heal_before_combat():
            action = self._use_item("heal")
            if action:
                self.ai_logic.message_log.add_message(
                    "AI: Healing before continuing combat."
                )
                return action

        # Get adjacent monsters and attack the safest one (or any if all are risky)
        adjacent_monsters = self.ai_logic._get_adjacent_monsters()
        if adjacent_monsters:
            # Try to get safest monster first
            monster_to_attack = self.ai_logic.get_safest_adjacent_monster()
            if not monster_to_attack:
                # No safe monster - just attack any (random choice)
                monster_to_attack = self.ai_logic.random.choice(adjacent_monsters)

            # Check if we should use a combat item instead of melee attack
            combat_item = self._should_use_combat_item(monster_to_attack.name)
            if combat_item:
                self.ai_logic.message_log.add_message(
                    f"AI: Using {combat_item} against {monster_to_attack.name}."
                )
                return ("use", combat_item)

            self.ai_logic.message_log.add_message(
                f"AI: Attacking adjacent {monster_to_attack.name}."
            )
            self.ai_logic.current_path = None
            return ("attack", monster_to_attack.name)

        return None
