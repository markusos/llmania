import os
import sys
import traceback

# --- Path setup ---
# Ensure the project root is in sys.path for module resolution.
# This allows `from src.game_engine import GameEngine` to work correctly
# when running main.py directly.
src_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(src_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.game_engine import GameEngine  # noqa: E402

# --- End Path setup ---

# curses import is only needed if the non-debug path directly uses curses.wrapper
# Since GameEngine handles its own curses initialization/cleanup, direct curses
# import here might only be for curses.error or specific constants if used.
# For now, let's assume GameEngine encapsulates all curses interactions for
# the non-debug path.
# import curses


def main_debug():
    # Initialize game engine
    game = GameEngine(map_width=20, map_height=10, debug_mode=True)

    # Initial render
    map_representation = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,
    )
    if map_representation:
        print("--- Initial Map State ---")
        for row in map_representation:
            print(row)
    else:
        print("Failed to render map for debugging.")

    # --- Test basic interactions ---
    print("\n--- Player initial 'look' ---")
    game.message_log.clear()  # Clear log for fresh messages
    game.command_processor.process_command(
        parsed_command_tuple=("look", None),
        player=game.player,
        world_map=game.world_map,
        message_log=game.message_log,
        win_pos=game.win_pos,
    )
    map_with_look_messages = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,
    )
    if map_with_look_messages:
        # Print only new messages from the message_log part of the output
        # The render_all output includes the map, UI, and then messages.
        # We need to identify where messages start. A simple heuristic:
        # messages usually appear after the command prompt line if in command mode,
        # or after HP/MODE lines.
        print("--- Output after 'look' (filtered for messages) ---")
        ui_and_map_lines = game.world_map.height + 3
        # Approx map height + HP, MODE, (optional CMD prompt)
        for i, row in enumerate(map_with_look_messages):
            # Heuristic to find messages
            is_message_line = any(
                msg_part in row for msg_part in game.message_log if msg_part
            )
            if i >= ui_and_map_lines or is_message_line:
                print(row)

    print("\n--- Moving player east ---")
    game.message_log.clear()  # Clear log for fresh messages
    game.command_processor.process_command(
        parsed_command_tuple=("move", "east"),
        player=game.player,
        world_map=game.world_map,
        message_log=game.message_log,
        win_pos=game.win_pos,
    )
    map_after_move = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,
    )
    if map_after_move:
        print("--- Map After Move (full output) ---")
        for row in map_after_move:
            print(row)
        print("--- Messages after 'move' ---")
        for msg in game.message_log:  # Directly print from game.message_log
            print(msg)
    else:
        print("Failed to render map after move.")

    print("\n--- Attempting to 'take' an item ---")
    game.message_log.clear()  # Clear log for fresh messages
    # Example: Assume there's no item at the starting location after moving east.
    game.command_processor.process_command(
        parsed_command_tuple=("take", None),
        player=game.player,
        world_map=game.world_map,
        message_log=game.message_log,
        win_pos=game.win_pos,
    )
    map_after_take_attempt = game.renderer.render_all(
        player_x=game.player.x,
        player_y=game.player.y,
        player_health=game.player.health,
        world_map=game.world_map,
        input_mode=game.input_handler.get_input_mode(),
        current_command_buffer=game.input_handler.get_command_buffer(),
        message_log=game.message_log,
        debug_render_to_list=True,
    )
    if map_after_take_attempt:
        print("--- Messages after 'take' attempt ---")
        # Print messages directly from game.message_log as it's populated
        # by CommandProcessor
        for msg in game.message_log:
            print(msg)
    else:
        print("Failed to render map after take attempt.")


if __name__ == "__main__":
    if "--debug" in sys.argv:
        main_debug()
    else:
        game = GameEngine(map_width=30, map_height=15, debug_mode=False)
        try:
            game.run()
        except Exception as e:
            # General catch-all if game.run() or its cleanup fails.
            # GameEngine.run() has its own finally block for curses cleanup.
            # This also catches errors from GameEngine.__init__ if curses init fails.
            print("-" * 70)
            print("The game encountered an unhandled error:")
            print(f"Error: {type(e).__name__}: {e}")
            print("Traceback:")
            print(traceback.format_exc())
            print("-" * 70)
            # Attempt final curses cleanup, though GameEngine should handle it.
            try:
                import curses

                if curses.has_colors():
                    curses.echo()
                    curses.nocbreak()
                    curses.endwin()
            except Exception:
                pass  # Avoid further errors during this fallback cleanup.
