from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from src.monster import Monster
from src.player import Player

from .base_command import Command

if TYPE_CHECKING:
    from src.game_engine import GameEngine
    from src.message_log import MessageLog
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

    def _perform_attack(
        self, attacker: Union[Player, Monster], defender: Union[Player, Monster]
    ) -> bool:
        if isinstance(attacker, Player):
            attacker_name = "You"
            attacker_speed = attacker.get_attack_speed()
        else:
            attacker_name = f"The {attacker.name}"
            attacker_speed = attacker.attack_speed

        if isinstance(defender, Player):
            defender_name = "you"
            defender_speed = defender.get_attack_speed()
        else:
            defender_name = f"the {defender.name}"
            defender_speed = defender.attack_speed

        hit_chance = 0.5 + (attacker_speed - defender_speed) * 0.1
        hit_chance = max(0.1, min(0.9, hit_chance))  # Clamp between 10% and 90%

        if self.game_engine.random.random() > hit_chance:
            self.message_log.add_message(f"{attacker_name} miss {defender_name}.")
            return False

        if isinstance(attacker, Player) and isinstance(defender, Monster):
            attack_res = attacker.attack_monster(defender)
            self.message_log.add_message(
                f"You attack the {defender.name} "
                f"for {attack_res['damage_dealt']} damage."
            )
            if attack_res["monster_defeated"]:
                self.message_log.add_message(f"You defeated the {defender.name}!")
                return True
        elif isinstance(attacker, Monster) and isinstance(defender, Player):
            monster_attack_res = attacker.attack(defender)
            self.message_log.add_message(
                f"The {attacker.name} attacks you for "
                f"{monster_attack_res['damage_dealt_to_player']} damage."
            )
            if monster_attack_res["player_is_defeated"]:
                self.message_log.add_message("You have been defeated. Game Over.")
                return True
        return False

    def execute(self) -> Dict[str, Any]:
        if isinstance(self.entity, Player):
            monsters_in_range = self._get_monsters_in_range(
                self.player.x, self.player.y, 1
            )
            target_info = self._select_attack_target(monsters_in_range)

            if target_info is None:
                return {"game_over": False}

            target_monster, target_m_x, target_m_y = target_info

            if self._perform_attack(self.player, target_monster):
                self.world_map.remove_monster(target_m_x, target_m_y)
                return {"game_over": False}

            if self._perform_attack(target_monster, self.player):
                return {"game_over": True}

        elif isinstance(self.entity, Monster):
            if self._perform_attack(self.entity, self.player):
                return {"game_over": True}

            if self._perform_attack(self.player, self.entity):
                monster_tile = self.world_map.get_tile_by_monster(self.entity)
                if monster_tile:
                    self.world_map.remove_monster(monster_tile.x, monster_tile.y)

        return {"game_over": False}
