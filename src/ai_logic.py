import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from entity import Monster  # Assuming Monster class is in entity.py
    from message_log import MessageLog
    from player import Player
    from world_map import WorldMap


class AILogic:
    """
    Handles the decision-making for AI-controlled characters, primarily the player
    when AI mode is active.
    """

    def __init__(
        self, player: "Player", world_map: "WorldMap", message_log: "MessageLog"
    ):
        """
        Initializes the AILogic system.

        Args:
            player: The player object that the AI will control.
            world_map: The game world map.
            message_log: The message log for recording actions or observations.
        """
        self.player = player
        self.world_map = world_map
        self.message_log = message_log  # For logging AI decisions if needed

        self.visited_tiles: List[Tuple[int, int]] = []
        self.last_move_command: Optional[Tuple[str, Optional[str]]] = None

    def _get_adjacent_monsters(self) -> List["Monster"]:
        """
        Checks N, S, E, W tiles around the player for monsters.

        Returns:
            A list of Monster objects found in adjacent tiles.
        """
        adjacent_monsters: List["Monster"] = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # N, S, W, E
            check_x, check_y = self.player.x + dx, self.player.y + dy
            tile = self.world_map.get_tile(check_x, check_y)
            if tile and tile.monster:
                adjacent_monsters.append(tile.monster)
        return adjacent_monsters

    def get_next_action(self) -> Optional[Tuple[str, Optional[str]]]:
        """
        Determines the next action for the AI-controlled player.

        Returns:
            A tuple representing the command and its argument (e.g., ("move", "north")),
            or None if no action can be decided.
        """
        current_tile = self.world_map.get_tile(self.player.x, self.player.y)

        # 1. Winning Condition
        if (
            current_tile
            and current_tile.item
            and current_tile.item.properties.get("type") == "quest"
        ):
            self.message_log.add_message(
                f"AI: Found quest item {current_tile.item.name}!"
            )
            return ("take", current_tile.item.name)

        # 2. Use Potion if Low Health
        # Assuming max_health might be available, otherwise using a fixed threshold.
        # e.g. low_health_threshold = self.player.max_health * 0.5
        low_health_threshold = 10  # Fixed threshold for now
        if self.player.health < low_health_threshold:
            if "Health Potion" in self.player.inventory:  # Direct check by name
                # Check if we actually have one
                if self.player.inventory["Health Potion"].quantity > 0:
                    self.message_log.add_message("AI: Low health, using Health Potion.")
                    return ("use", "Health Potion")

        # 3. Take Items (non-quest)
        if current_tile and current_tile.item:  # (Quest item already handled above)
            self.message_log.add_message(
                f"AI: Found item {current_tile.item.name}, taking it."
            )
            return ("take", current_tile.item.name)

        # 4. Attack Monsters
        adjacent_monsters = self._get_adjacent_monsters()
        if adjacent_monsters:
            monster_to_attack = adjacent_monsters[0]
            self.message_log.add_message(f"AI: Attacking {monster_to_attack.name}.")
            return (
                "attack",
                monster_to_attack.name,
            )  # Assuming command processor handles name->object

        # 5. Exploration
        current_pos = (self.player.x, self.player.y)
        if current_pos not in self.visited_tiles:
            self.visited_tiles.append(current_pos)

        moves: Dict[str, Tuple[int, int]] = {
            "north": (0, -1),
            "south": (0, 1),
            "west": (-1, 0),
            "east": (1, 0),
        }
        reverse_moves: Dict[Optional[str], Optional[str]] = {
            "north": "south",
            "south": "north",
            "west": "east",
            "east": "west",
            None: None,
        }

        possible_actions: List[Tuple[str, str]] = []
        all_valid_moves: List[Tuple[str, str]] = []

        for direction, (dx, dy) in moves.items():
            next_x, next_y = self.player.x + dx, self.player.y + dy
            # Check for monsters in the target tile before considering it for movement
            target_tile_for_move = self.world_map.get_tile(next_x, next_y)
            monster_in_path = target_tile_for_move and target_tile_for_move.monster

            if self.world_map.is_valid_move(next_x, next_y) and not monster_in_path:
                all_valid_moves.append(("move", direction))
                if (next_x, next_y) not in self.visited_tiles:
                    possible_actions.append(("move", direction))

        chosen_action: Optional[Tuple[str, str]] = None

        if possible_actions:  # Prefer unvisited cells
            chosen_action = random.choice(possible_actions)
            self.message_log.add_message(
                f"AI: Exploring unvisited. Moving {chosen_action[1]}."
            )
        elif all_valid_moves:  # If all adjacent are visited, pick a random valid one
            # Avoid simple back-and-forth if possible
            if len(all_valid_moves) > 1 and self.last_move_command:
                last_direction = self.last_move_command[1]
                # Try to remove the reverse of the last move
                non_reverse_moves = [
                    m
                    for m in all_valid_moves
                    if m[1] != reverse_moves.get(last_direction)
                ]
                if non_reverse_moves:
                    chosen_action = random.choice(non_reverse_moves)
                else:  # Only reverse move is possible
                    chosen_action = random.choice(all_valid_moves)
            else:  # Only one move, or no last move history
                chosen_action = random.choice(all_valid_moves)
            self.message_log.add_message(
                f"AI: All visited nearby. Moving {chosen_action[1]}."
            )

        if chosen_action:
            self.last_move_command = chosen_action
            return chosen_action

        # If no valid moves at all (e.g., boxed in)
        self.message_log.add_message("AI: No valid moves, looking around.")
        self.last_move_command = ("look", None)  # Reset last move if looking
        return ("look", None)
