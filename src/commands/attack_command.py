from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_command import Command

if TYPE_CHECKING:
    from src.monster import Monster


class AttackCommand(Command):
    def _select_attack_target(
        self,
        adj_monsters: list[tuple["Monster", int, int]],
    ) -> Optional[tuple["Monster", int, int]]:
        # Monster is already available via TYPE_CHECKING for hints
        # from src.monster import Monster # Not needed if only for type hint

        if not adj_monsters:
            self.message_log.add_message("There is no monster nearby to attack.")
            return None

        target_monster = None
        target_m_x, target_m_y = 0, 0

        if self.argument:  # Monster name specified by player
            found_monster_tuple = next(
                (
                    m_tuple
                    for m_tuple in adj_monsters
                    if m_tuple[0].name.lower() == self.argument.lower()
                ),
                None,
            )
            if not found_monster_tuple:
                self.message_log.add_message(
                    f"No monster named '{self.argument}' nearby."
                )
                return None
            target_monster, target_m_x, target_m_y = found_monster_tuple
        elif len(adj_monsters) == 1:  # No name specified, only one monster nearby
            target_monster, target_m_x, target_m_y = adj_monsters[0]
        else:  # No name specified, multiple monsters nearby
            monster_names = sorted([m_tuple[0].name for m_tuple in adj_monsters])
            self.message_log.add_message(
                f"Multiple monsters nearby: {', '.join(monster_names)}. Which one?"
            )
            return None

        if (
            not target_monster
        ):  # Should ideally not be reached if logic above is correct
            self.message_log.add_message(
                "Error: Could not select a target monster."
            )  # Should not happen
            return None

        return target_monster, target_m_x, target_m_y

    def execute(self) -> Dict[str, Any]:
        # _get_adjacent_monsters is inherited from Command base class
        adj_monsters = self._get_adjacent_monsters(self.player.x, self.player.y)
        target_info = self._select_attack_target(adj_monsters)

        if target_info is None:
            # Target selection failed or no target, message already logged by
            # _select_attack_target.
            return {"game_over": False}

        target_monster, target_m_x, target_m_y = target_info

        # Player attacks the selected monster
        attack_res = self.player.attack_monster(target_monster)
        self.message_log.add_message(
            f"You attack the {target_monster.name} "
            f"for {attack_res['damage_dealt']} damage."
        )

        if attack_res["monster_defeated"]:
            self.message_log.add_message(f"You defeated the {target_monster.name}!")
            self.world_map.remove_monster(target_m_x, target_m_y)
            return {"game_over": False}  # Monster defeated, game not over

        # Monster attacks back if not defeated
        monster_attack_res = target_monster.attack(self.player)
        self.message_log.add_message(
            f"The {target_monster.name} attacks you for "
            f"{monster_attack_res['damage_dealt_to_player']} damage."
        )

        if monster_attack_res["player_is_defeated"]:
            self.message_log.add_message("You have been defeated. Game Over.")
            return {"game_over": True}  # Player defeated, game over

        return {"game_over": False}  # Default: game not over
