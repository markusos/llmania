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
# --- End Path setup ---

from src.game_engine import GameEngine

# curses import is only needed if the non-debug path directly uses curses.wrapper
# Since GameEngine handles its own curses initialization/cleanup, direct curses
# import here might only be for curses.error or specific constants if used.
# For now, let's assume GameEngine encapsulates all curses interactions for
# the non-debug path.
# import curses


def main_debug():
    # Initialize game engine
    game = GameEngine(map_width=20, map_height=10, debug_mode=True)

    map_representation = game.render_map(debug_render_to_list=True)

    if map_representation:
        print("--- Initial Map State ---")
        for row in map_representation:
            print(row)
    else:
        print("Failed to render map for debugging.")

    # --- Test basic interactions ---
    print("\n--- Player initial 'look' ---")
    game.process_command_tuple(("look", None))
    map_with_look_messages = game.render_map(debug_render_to_list=True)
    if map_with_look_messages:
        for row in map_with_look_messages:
            # Print messages and relevant UI lines
            if (row.startswith("You are at") or row.startswith("You see a") or
                    row.startswith("There is a") or row.startswith("The area is clear.") or
                    "HP:" in row or "MODE:" in row):
                print(row)

    print("\n--- Moving player east ---")
    game.process_command_tuple(("move", "east"))
    map_after_move = game.render_map(debug_render_to_list=True)
    if map_after_move:
        print("--- Map After Move ---")
        for row in map_after_move:
            print(row)
    else:
        print("Failed to render map after move.")

    print("\n--- Attempting to 'take' an item ---")
    game.process_command_tuple(("take", None))
    map_after_take_attempt = game.render_map(debug_render_to_list=True)
    if map_after_take_attempt:
        print("--- Messages after 'take' attempt ---")
        for row in map_after_take_attempt:
            # Exclude map, previous messages, and general UI
            map_chars = ["🧱", "🟩", "🧑", "👹", "💰", "?"]
            ui_indicators = ["HP:", "MODE:", ">"]
            prev_msgs = ["You move east."]
            
            is_map_char = any(row.startswith(s) for s in map_chars)
            is_ui_char = any(s in row for s in ui_indicators)
            is_prev_message = any(s in row for s in prev_msgs)

            if not (is_map_char or is_ui_char or is_prev_message):
                print(row)


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
                pass # Avoid further errors during this fallback cleanup.
