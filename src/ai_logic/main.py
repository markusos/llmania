from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.map_algorithms.pathfinding import PathFinder

from .ai_monster_view import AIMonsterView
from .ai_player_view import AIPlayerView
from .bestiary import Bestiary
from .explorer import Explorer
from .states.attacking_state import AttackingState
from .states.exploring_state import ExploringState
from .states.looting_state import LootingState
from .states.survival_state import SurvivalState
from .target_finder import TargetFinder

if TYPE_CHECKING:
    from random import Random

    from src.message_log import MessageLog
    from src.player import Player
    from src.world_map import WorldMap

    from .states import AIState


class AILogic:
    def _get_state(self, state_name: str) -> "AIState":
        if state_name == "ExploringState":
            return ExploringState(self)
        elif state_name == "AttackingState":
            return AttackingState(self)
        elif state_name == "LootingState":
            return LootingState(self)
        elif state_name == "SurvivalState":
            return SurvivalState(self)
        else:
            raise ValueError(f"Unknown state name: {state_name}")

    """
    Handles the decision-making for AI-controlled characters, primarily the player
    when AI mode is active.
    """

    def __init__(
        self,
        player: "Player",
        ai_visible_maps: Dict[int, "WorldMap"],
        message_log: "MessageLog",
        random_generator: "Random",
        verbose: int = 0,
    ):
        # Store both the raw player (for target_finder/explorer compatibility)
        # and the view wrapper for AI decision-making
        self.player = player
        self.player_view = AIPlayerView(player)
        self.ai_visible_maps = ai_visible_maps
        self.message_log = message_log
        self.random = random_generator
        self.verbose = verbose
        self.path_finder = PathFinder()
        self.current_path: Optional[List[Tuple[int, int, int]]] = None
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None
        self.target_finder = TargetFinder(self.player_view, self.ai_visible_maps)
        self.explorer = Explorer(self.player_view, self.ai_visible_maps)
        self.state: "AIState" = ExploringState(self)
        self.last_player_floor_id = player.current_floor_id
        self.last_player_pos = (player.x, player.y)
        self.player_pos_history: list[tuple[int, int]] = []
        self.command_history: List[Optional[Tuple[str, Optional[str]]]] = []
        self.loop_breaker_moves_left = 0

    def _is_in_loop(self, lookback: int = 4) -> bool:
        if len(self.command_history) < lookback:
            return False
        # Check if the last `lookback` commands are stuck in a loop of 2 commands
        last_commands = self.command_history[-lookback:]
        if len(set(last_commands)) <= 2:
            # Check if we are alternating between two positions
            if len(self.player_pos_history) >= 4:
                # Check if the last 4 positions are just 2 unique positions
                if len(set(self.player_pos_history[-4:])) <= 2:
                    return True
        return False

    def _is_stuck_in_area(self) -> bool:
        """Check if AI is stuck moving in a small area (within 3 unique positions)."""
        if len(self.player_pos_history) < 8:
            return False
        # If we've only visited 3 or fewer positions in the last 8 moves, we're stuck
        return len(set(self.player_pos_history[-8:])) <= 3

    def _break_loop(self) -> None:
        self.message_log.add_message("AI: Detected a loop, breaking.")
        self.current_path = None
        self.loop_breaker_moves_left = 8  # Increased from 5 to give more room to escape

    def calculate_optimal_quest_route(
        self,
    ) -> Optional[List[Tuple[int, int, int]]]:
        """
        Calculate best route to quest item considering all floors and portals.

        Uses risk-aware pathfinding when health is low to avoid monsters.

        Returns:
            A list of (x, y, floor_id) tuples representing the path to the
            nearest quest item, or None if no quest items are known.
        """
        quest_locations = self.target_finder.find_quest_items(
            (self.player_view.x, self.player_view.y),
            self.player_view.current_floor_id,
            same_floor_only=False,
        )

        if not quest_locations:
            return None

        best_route: Optional[List[Tuple[int, int, int]]] = None
        best_distance = float("inf")

        # Calculate health ratio for risk-aware pathfinding
        health_ratio = self.player_view.health / self.player_view.max_health

        for quest_x, quest_y, quest_floor, _, _ in quest_locations:
            # Use risk-aware pathfinding when health is below 70%
            if health_ratio < 0.7:
                path = self.path_finder.find_path_risk_aware(
                    self.ai_visible_maps,
                    (self.player_view.x, self.player_view.y),
                    self.player_view.current_floor_id,
                    (quest_x, quest_y),
                    quest_floor,
                    player_health_ratio=health_ratio,
                    require_explored=True,
                )
            else:
                path = self.path_finder.find_path_bfs(
                    self.ai_visible_maps,
                    (self.player_view.x, self.player_view.y),
                    self.player_view.current_floor_id,
                    (quest_x, quest_y),
                    quest_floor,
                    require_explored=True,
                )

            if path and len(path) < best_distance:
                best_distance = len(path)
                best_route = path

        return best_route

    def _get_adjacent_monsters(self) -> List[AIMonsterView]:
        """Returns visible monster info (name and position only)."""
        adjacent_monsters: List[AIMonsterView] = []
        current_floor_id = self.player_view.current_floor_id
        current_ai_map = self.ai_visible_maps.get(current_floor_id)
        if not current_ai_map:
            return []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_x, check_y = self.player_view.x + dx, self.player_view.y + dy
            tile = current_ai_map.get_tile(check_x, check_y)
            if tile and tile.is_explored and tile.monster:
                # Only expose name and position, not internal stats
                adjacent_monsters.append(
                    AIMonsterView(tile.monster.name, check_x, check_y)
                )
        return adjacent_monsters

    def calculate_survival_threshold(self) -> float:
        """
        Calculate dynamic survival threshold based on context.

        Returns a value between 0.5 and 0.75 representing the health
        percentage at which the AI should enter survival mode.
        """
        base_threshold = 0.5

        # Increase threshold if no healing available
        has_healing = self.player_view.has_item_type("heal")
        if not has_healing:
            base_threshold += 0.15

        # Increase threshold based on nearby monster danger
        adjacent_monsters = self._get_adjacent_monsters()
        if adjacent_monsters:
            bestiary = Bestiary.get_instance()
            max_monster_damage = max(
                bestiary.get_attack_power(m.name) for m in adjacent_monsters
            )
            # If a monster could deal 30%+ of our current health in one hit
            if max_monster_damage >= self.player_view.health * 0.3:
                base_threshold += 0.1

        return min(base_threshold, 0.75)

    def should_enter_survival_mode(self) -> bool:
        """Check if AI should enter survival mode based on dynamic threshold."""
        threshold = self.calculate_survival_threshold()
        return self.player_view.health <= self.player_view.max_health * threshold

    def should_engage_monster(self, monster_name: str) -> bool:
        """
        Evaluate if combat with a monster is winnable/safe.

        Uses Bestiary to look up monster stats (fair - simulates player knowledge).
        """
        bestiary = Bestiary.get_instance()
        stats = bestiary.get_stats(monster_name)

        player_health = self.player_view.health
        player_attack = self.player_view.get_attack_power()
        player_defense = self.player_view.get_defense()

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

        # If we're cornered (no safe escape), we must fight
        if self._is_cornered():
            self.message_log.add_message(f"AI: Cornered! Must engage {monster_name}.")
            return True

        # Never engage if health is critical (could die in 1-2 hits)
        # unless cornered (handled above)
        if player_health <= monster_attack * 2:
            self.message_log.add_message(
                f"AI: Health too low to engage {monster_name} safely."
            )
            return False

        # Don't engage if expected damage would kill us
        if expected_damage >= player_health:
            self.message_log.add_message(
                f"AI: Combat with {monster_name} too risky (expected {expected_damage}"
                f" damage, have {player_health} HP)."
            )
            return False

        # Engage even if left at low health - better to fight than timeout
        # Only be cautious if we'd be left at <15% and have no healing
        remaining_health = player_health - expected_damage
        if remaining_health < self.player_view.max_health * 0.15:
            has_healing = self.player_view.has_item_type("heal")
            if not has_healing:
                self.message_log.add_message(
                    f"AI: Would be left at {remaining_health} HP after fighting "
                    f"{monster_name} with no healing available."
                )
                return False

        return True

    def _is_cornered(self) -> bool:
        """Check if player has no safe escape routes."""
        current_ai_map = self.ai_visible_maps.get(self.player_view.current_floor_id)
        if not current_ai_map:
            return True  # Can't see map, assume cornered

        safe_moves = 0
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_x = self.player_view.x + dx
            check_y = self.player_view.y + dy
            tile = current_ai_map.get_tile(check_x, check_y)
            if tile and tile.type != "wall" and not tile.monster:
                safe_moves += 1

        return safe_moves == 0

    def should_heal_before_combat(self) -> bool:
        """
        Check if AI should use a healing item before engaging in combat.

        Returns True if health is at risk and healing would help.
        """
        # Don't heal if already at high health
        if self.player_view.health >= self.player_view.max_health * 0.8:
            return False

        # Check for adjacent monsters
        adjacent_monsters = self._get_adjacent_monsters()
        if not adjacent_monsters:
            return False

        # Check if we have healing available
        if not self.player_view.has_item_type("heal"):
            return False

        # Use bestiary to estimate incoming damage
        bestiary = Bestiary.get_instance()
        max_incoming_damage = max(
            bestiary.get_attack_power(m.name) for m in adjacent_monsters
        )

        # Heal if a single attack could put us in critical danger
        if self.player_view.health <= max_incoming_damage * 1.5:
            return True

        # Heal if we're below 50% and facing dangerous monsters
        if self.player_view.health <= self.player_view.max_health * 0.5:
            max_danger = max(
                bestiary.get_danger_rating(m.name) for m in adjacent_monsters
            )
            if max_danger >= 3:
                return True

        return False

    def get_safest_adjacent_monster(self) -> Optional[AIMonsterView]:
        """
        Get the safest monster to attack from adjacent monsters.

        Returns the monster with lowest danger rating that we can safely engage.
        """
        adjacent_monsters = self._get_adjacent_monsters()
        if not adjacent_monsters:
            return None

        bestiary = Bestiary.get_instance()
        safe_monsters = [
            m for m in adjacent_monsters if self.should_engage_monster(m.name)
        ]

        if not safe_monsters:
            return None

        # Sort by danger rating (lowest first)
        safe_monsters.sort(key=lambda m: bestiary.get_danger_rating(m.name))
        return safe_monsters[0]
        return adjacent_monsters

    def _coordinates_to_move_command(
        self, start_pos_xy: Tuple[int, int], end_pos_xy: Tuple[int, int]
    ) -> Optional[Tuple[str, str]]:
        dx = end_pos_xy[0] - start_pos_xy[0]
        dy = end_pos_xy[1] - start_pos_xy[1]
        if dx == 0 and dy == -1:
            return ("move", "north")
        if dx == 0 and dy == 1:
            return ("move", "south")
        if dx == -1 and dy == 0:
            return ("move", "west")
        if dx == 1 and dy == 0:
            return ("move", "east")
        return None

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        action = self._get_next_action_logic()
        self.command_history.append(action)
        if len(self.command_history) > 10:
            self.command_history.pop(0)
        if self.verbose > 0:
            if action:
                print(f"AI Action: {action[0]} {action[1] if action[1] else ''}")
            else:
                print("AI Action: None")
        return action

    def _get_next_action_logic(self) -> Optional[Tuple[str, Optional[str]]]:
        # Check state transitions FIRST - survival takes priority over loop breaking
        next_state_name = self.state.handle_transitions()
        if next_state_name != self.state.__class__.__name__:
            self.state = self._get_state(next_state_name)
            # If we just entered SurvivalState, let it handle the action
            # (it will try to heal or flee properly)
            if next_state_name == "SurvivalState":
                self.loop_breaker_moves_left = 0  # Cancel loop breaker
                return self.state.get_next_action()

        if self.loop_breaker_moves_left > 0:
            self.loop_breaker_moves_left -= 1
            self.message_log.add_message("AI: Taking a random action to break a loop.")
            return self.state._explore_randomly(break_loop=True)

        if self.player_view.current_floor_id != self.last_player_floor_id:
            prev_map = self.ai_visible_maps.get(self.last_player_floor_id)
            if prev_map:
                prev_tile = prev_map.get_tile(
                    self.last_player_pos[0], self.last_player_pos[1]
                )
                if prev_tile and prev_tile.is_portal:
                    self.explorer.mark_portal_as_visited(
                        self.last_player_pos[0],
                        self.last_player_pos[1],
                        self.last_player_floor_id,
                    )
                    if self.verbose > 0:
                        print(
                            "AI: Portal at "
                            f"({self.last_player_pos[0]},{self.last_player_pos[1]}) "
                            f"on floor {self.last_player_floor_id} marked as visited."
                        )

        self.last_player_floor_id = self.player_view.current_floor_id
        self.last_player_pos = (self.player_view.x, self.player_view.y)

        # Stuck detection - check for oscillation and small area movement
        self.player_pos_history.append(self.last_player_pos)
        if len(self.player_pos_history) > 10:
            self.player_pos_history.pop(0)

        # Check for 2-position oscillation (strict loop)
        if len(self.player_pos_history) >= 4:
            if len(set(self.player_pos_history[-4:])) <= 2:
                self._break_loop()
                self.player_pos_history = []
                return self.state._explore_randomly(break_loop=True)

        # Check for stuck in small area (3 positions in 8 moves)
        if self._is_stuck_in_area():
            self._break_loop()
            self.player_pos_history = []
            return self.state._explore_randomly(break_loop=True)

        # Delegate action to the current state (transitions already handled above)
        return self.state.get_next_action()
