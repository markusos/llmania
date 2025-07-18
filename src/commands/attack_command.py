from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
    from src.monster import Monster
    from src.player import Player
    from src.world_map import WorldMap


class AttackCommand(Command):
    def __init__(
        self,
        player: "Player",
        world_map: "WorldMap",
        message_log: "MessageLog",
        winning_position: tuple[int, int, int],
        argument: Optional[str] = None,
        world_maps: Optional[Dict[int, "WorldMap"]] = None,
        game_engine: Optional["GameEngine"] = None,
        entity: Optional[Union["Player", "Monster"]] = None,
    ):
        super().__init__(
            player,
            world_map,
            message_log,
            winning_position,
            argument,
            world_maps,
            game_engine,
            entity,
        )

    def _select_attack_target(
        self,
        adj_monsters: list[tuple["Monster", int, int]],
    ) -> Optional[tuple["Monster", int, int]]:
        if not adj_monsters:
            self.message_log.add_message("There is no monster nearby to attack.")
            return None

        target_monster = None
        target_m_x, target_m_y = 0, 0

        if self.argument:
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
        elif len(adj_monsters) == 1:
            target_monster, target_m_x, target_m_y = adj_monsters[0]
        else:
            monster_names = sorted([m_tuple[0].name for m_tuple in adj_monsters])
            self.message_log.add_message(
                f"Multiple monsters nearby: {', '.join(monster_names)}. Which one?"
            )
            return None

        if not target_monster:
            self.message_log.add_message("Error: Could not select a target monster.")
            return None

        return target_monster, target_m_x, target_m_y

    def execute(self) -> Dict[str, Any]:
        from src.monster import Monster
        from src.player import Player

        if isinstance(self.entity, Player):
            monsters_in_range = self._get_monsters_in_range(
                self.player.x, self.player.y, 1
            )
            target_info = self._select_attack_target(monsters_in_range)

            if target_info is None:
                return {"game_over": False}

            target_monster, target_m_x, target_m_y = target_info

            attack_res = self.player.attack_monster(target_monster)
            self.message_log.add_message(
                f"You attack the {target_monster.name} "
                f"for {attack_res['damage_dealt']} damage."
            )

            if attack_res["monster_defeated"]:
                self.message_log.add_message(f"You defeated the {target_monster.name}!")
                self.world_map.remove_monster(target_m_x, target_m_y)
                return {"game_over": False}

            monster_attack_res = target_monster.attack(self.player)
            self.message_log.add_message(
                f"The {target_monster.name} attacks you for "
                f"{monster_attack_res['damage_dealt_to_player']} damage."
            )

            if monster_attack_res["player_is_defeated"]:
                self.message_log.add_message("You have been defeated. Game Over.")
                return {"game_over": True}

        elif isinstance(self.entity, Monster):
            monster_attack_res = self.entity.attack(self.player)
            self.message_log.add_message(
                f"The {self.entity.name} attacks you for "
                f"{monster_attack_res['damage_dealt_to_player']} damage."
            )

            if monster_attack_res["player_is_defeated"]:
                self.message_log.add_message("You have been defeated. Game Over.")
                return {"game_over": True}

        return {"game_over": False}
