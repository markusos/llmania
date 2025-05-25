from typing import TYPE_CHECKING, Optional

from src.item import Item

if TYPE_CHECKING:
    from src.player import Player
    from src.world_map import WorldMap


class InventoryManager:
    def __init__(self):
        pass

    def take_item(
        self,
        player: "Player",
        world_map: "WorldMap",
        item_name: Optional[str],
        message_log: list[str],
        win_pos: tuple[int, int],
    ) -> bool:
        game_won = False
        tile = world_map.get_tile(player.x, player.y)
        can_take = (
            tile
            and tile.item
            and (item_name is None or tile.item.name.lower() == item_name.lower())
        )

        if can_take and tile and tile.item:  # Added "and tile and tile.item" for mypy
            item_taken = world_map.remove_item(player.x, player.y)
            if item_taken:
                player.inventory.append(item_taken)  # Add to player's inventory
                message_log.append(f"You take the {item_taken.name}.")
                is_quest_win = (
                    player.x,
                    player.y,
                ) == win_pos and item_taken.properties.get("type") == "quest"
                if is_quest_win:
                    message_log.append(
                        "You picked up the Amulet of Yendor! You win!"
                    )
                    game_won = True
            else:
                # This case should ideally not be reached if can_take is true
                # and world_map.remove_item works as expected.
                message_log.append("Error: Tried to take item but failed.")
        else:
            no_item_msg = (
                f"There is no {item_name} here to take."
                if item_name
                else "Nothing here to take or item name mismatch."
            )
            message_log.append(no_item_msg)
        return game_won

    def drop_item(
        self,
        player: "Player",
        world_map: "WorldMap",
        item_name: str,
        message_log: list[str],
    ) -> None:
        item_to_drop = None
        for item in player.inventory:
            if item.name.lower() == item_name.lower():
                item_to_drop = item
                break

        if item_to_drop:
            player.inventory.remove(item_to_drop)
            # If item was equipped, unequip it
            if player.equipped_weapon == item_to_drop:
                player.equipped_weapon = None
                message_log.append(f"You unequip the {item_to_drop.name}.")

            current_tile = world_map.get_tile(player.x, player.y)
            if current_tile and current_tile.item is None:
                world_map.place_item(item_to_drop, player.x, player.y)
                message_log.append(f"You drop the {item_to_drop.name}.")
            else:
                player.inventory.append(item_to_drop)  # Player picks it back up
                # If item was unequipped, re-equip it as it couldn't be dropped
                if player.equipped_weapon is None and item_to_drop.properties.get("type") == "weapon":
                    player.equipped_weapon = item_to_drop
                    # No message here as it's like the drop was cancelled.
                msg = f"You can't drop {item_to_drop.name} here, space occupied."
                message_log.append(msg)
        else:
            message_log.append(f"You don't have a {item_name} to drop.")

    def use_item(
        self, player: "Player", item_name: str, message_log: list[str]
    ) -> bool:
        player_died = False
        item_to_use = None
        for item in player.inventory:
            if item.name.lower() == item_name.lower():
                item_to_use = item
                break

        if item_to_use:
            item_type = item_to_use.properties.get("type")
            if item_type == "heal":
                heal_amount = item_to_use.properties.get("heal_amount", 0)
                if player.health < player.max_health:
                    player.health = min(player.max_health, player.health + heal_amount)
                    message_log.append(
                        f"You use the {item_to_use.name} and heal for {heal_amount} HP."
                    )
                    player.inventory.remove(item_to_use)
                else:
                    message_log.append(
                        f"You use the {item_to_use.name}, but you are already at full health."
                    )
                    # Not removing item if it wasn't effectively used.
            elif item_type == "weapon":
                if player.equipped_weapon == item_to_use:
                    player.equipped_weapon = None # Unequip
                    message_log.append(f"You unequip the {item_to_use.name}.")
                else:
                    if player.equipped_weapon: # Unequip current weapon first
                        message_log.append(f"You unequip the {player.equipped_weapon.name}.")
                    player.equipped_weapon = item_to_use # Equip new weapon
                    message_log.append(f"You equip the {item_to_use.name}.")
                # Weapon is not removed from inventory upon equipping
            elif item_type == "cursed": # Example of a cursed item
                player.health -= item_to_use.properties.get("damage", 5)
                message_log.append(f"The {item_to_use.name} is cursed! You take {item_to_use.properties.get('damage', 5)} damage.")
                player.inventory.remove(item_to_use) # Cursed item is consumed/destroys itself
                if player.health <= 0:
                    message_log.append("The cursed item has led to your demise!")
                    player_died = True
            else:
                message_log.append(f"You can't use the {item_to_use.name} in that way.")
        else:
            message_log.append(f"You don't have a {item_name} to use.")

        return player_died
