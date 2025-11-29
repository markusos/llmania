"""
Attack actions for the Utility-Based AI system.

Contains:
- AttackAction: Melee attack against adjacent monsters
- UseCombatItemAction: Use combat items like fire potions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base_action import AIAction

if TYPE_CHECKING:
    from src.ai_logic.context import AIContext
    from src.ai_logic.main import AILogic
    from src.message_log import MessageLog


class AttackAction(AIAction):
    """
    Attack an adjacent monster.

    Utility Scores:
    - 0.90: cornered (no choice but to fight)
    - 0.85: safe to engage (can win without critical damage)
    - 0.35: risky engagement (last resort)
    """

    @property
    def name(self) -> str:
        return "Attack"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available if there are adjacent monsters."""
        return len(ctx.adjacent_monsters) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """
        Calculate utility based on combat evaluation.

        Uses bestiary to look up monster stats (fair - simulates player knowledge).
        """
        if not self.is_available(ctx):
            return 0.0

        # If cornered, must fight - high utility
        if ctx.is_cornered:
            return 0.90

        # Check if any monster is safe to engage
        has_safe_target = any(
            self._is_safe_to_engage(ctx, m.name) for m in ctx.adjacent_monsters
        )

        if has_safe_target:
            return 0.85

        # Risky but forced to fight (no safe target, but monsters present)
        return 0.35

    def _is_safe_to_engage(self, ctx: "AIContext", monster_name: str) -> bool:
        """
        Evaluate if combat with a monster is winnable/safe.

        Mirrors should_engage_monster() logic from AILogic.
        """
        if not ctx.bestiary:
            return False

        stats = ctx.bestiary.get_stats(monster_name)

        player_health = ctx.player_health
        player_attack = ctx.player_attack
        player_defense = ctx.player_defense

        monster_attack = stats.get("attack_power", 2)
        monster_health = stats.get("health", 10)
        monster_defense = stats.get("defense", 0)

        # Calculate expected turns to kill monster
        effective_player_damage = max(1, player_attack - monster_defense)
        turns_to_kill = (monster_health + effective_player_damage - 1) // (
            effective_player_damage
        )

        # Calculate expected damage taken
        effective_monster_damage = max(0, monster_attack - player_defense)
        expected_damage = turns_to_kill * effective_monster_damage

        # Never engage if health is critical (could die in 1-2 hits)
        if player_health <= monster_attack * 2:
            return False

        # Don't engage if expected damage would kill us
        if expected_damage >= player_health:
            return False

        # Don't engage if would leave at <15% HP with no healing
        remaining_health = player_health - expected_damage
        max_health = ctx.player_max_health
        if remaining_health < max_health * 0.15:
            if not ctx.has_healing_item:
                return False

        return True

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """
        Execute attack against the safest adjacent monster.

        Targets monster with lowest danger rating that we can safely engage.
        """
        # Get safest monster to attack
        monster = ai_logic.get_safest_adjacent_monster()

        # If no safe monster, attack any adjacent monster
        if not monster:
            monsters = ctx.adjacent_monsters
            if monsters and ctx.random:
                monster = ctx.random.choice(monsters)

        if monster:
            message_log.add_message(f"AI: Attacking adjacent {monster.name}.")
            ai_logic.current_path = None
            return ("attack", monster.name)

        return None


class UseCombatItemAction(AIAction):
    """
    Use a combat item (like fire potion) against monsters.

    Utility Score: 0.91 when:
    - Facing fire-vulnerable monster and have fire potion
    - Facing 2+ adjacent monsters with fire potion (area damage)
    """

    @property
    def name(self) -> str:
        return "UseCombatItem"

    def is_available(self, ctx: "AIContext") -> bool:
        """Available if we have combat items and adjacent monsters."""
        return ctx.has_fire_potion and len(ctx.adjacent_monsters) > 0

    def calculate_utility(self, ctx: "AIContext") -> float:
        """High utility for vulnerable monsters or groups."""
        if not self.is_available(ctx):
            return 0.0

        if not ctx.bestiary:
            return 0.0

        # Check for fire-vulnerable monster
        for monster in ctx.adjacent_monsters:
            vulnerability = ctx.bestiary.get_vulnerability(monster.name)
            if vulnerability == "fire":
                return 0.91

        # Use against groups of 2+ monsters (area damage efficient)
        if len(ctx.adjacent_monsters) >= 2:
            return 0.91

        return 0.0

    def execute(
        self,
        ctx: "AIContext",
        ai_logic: "AILogic",
        message_log: "MessageLog",
    ) -> Optional[Tuple[str, Optional[str]]]:
        """Use fire potion against monsters."""
        # Find a fire potion in inventory
        for item in ctx.inventory_items:
            if "fire" in item.name.lower():
                effects = item.properties.get("effects", [])
                if any(effect.get("type") == "damage" for effect in effects):
                    target_name = ctx.adjacent_monsters[0].name
                    message_log.add_message(
                        f"AI: Using {item.name} against {target_name}."
                    )
                    return ("use", item.name)

        return None
