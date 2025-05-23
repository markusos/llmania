import os
import sys
import traceback  # Keep for main_debug if it uses it, or for general error handling

# --- Path setup ---
# Get the absolute path of the directory containing main.py (src)
src_dir = os.path.dirname(os.path.abspath(__file__))
# Get the absolute path of the project root (parent of src)
project_root = os.path.dirname(src_dir)
# Add project_root to the beginning of sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path setup ---

# curses import is only needed if the non-debug path directly uses curses.wrapper
# Since GameEngine handles its own curses initialization/cleanup,
# direct curses import here might only be for curses.error or specific constants if used.
# For now, let's assume GameEngine encapsulates all curses interactions for the non-debug path.
# import curses

from src.game_engine import GameEngine


def main_debug():
    # Initialize game engine
    # Using a slightly smaller map for easier visual inspection in text output
    game = GameEngine(map_width=20, map_height=10, debug_mode=True)

    # Get the map representation as a list of strings
    map_representation = game.render_map(
        debug_render_to_list=True
    )  # Ensure this line is present in main_debug

    # Print the map representation
    if map_representation:
        print("--- Initial Map State ---")
        for row in map_representation:
            print(row)
    else:
        print("Failed to render map for debugging.")

    # --- Test basic interactions ---
    # (The rest of main_debug remains the same)
    # 1. Player's initial view (look around)
    print("\n--- Player initial 'look' ---")
    game.process_command_tuple(("look", None))  # Simulate a look command
    # Re-render to capture messages in the output buffer
    map_with_look_messages = game.render_map(debug_render_to_list=True)
    if map_with_look_messages:
        for row in map_with_look_messages:
            # We only need to print the messages here, map itself hasn't changed
            if (
                row.startswith("You are at")
                or row.startswith("You see a")
                or row.startswith("There is a")
                or row.startswith("The area is clear.")
            ):
                print(row)
            elif (
                "HP:" in row or "MODE:" in row
            ):  # print HP and mode lines as well for context
                print(row)

    # 2. Simulate a player move (e.g., east) and render again
    print("\n--- Moving player east ---")
    game.process_command_tuple(("move", "east"))
    map_after_move = game.render_map(debug_render_to_list=True)
    if map_after_move:
        print("--- Map After Move ---")
        for row in map_after_move:
            print(row)
    else:
        print("Failed to render map after move.")

    # 3. Simulate taking an item if one is at start (requires knowing mapgen logic)
    # This is a bit speculative as we don't know the exact map generation
    # For now, we'll just try a "take" command. If there's an item, it should say so.
    # If not, it will say "Nothing here to take".
    print("\n--- Attempting to 'take' an item ---")
    game.process_command_tuple(("take", None))  # Try to take any item
    map_after_take_attempt = game.render_map(debug_render_to_list=True)
    if map_after_take_attempt:
        # Print only new messages resulting from the "take" command
        print("--- Messages after 'take' attempt ---")
        for row in map_after_take_attempt:
            if not (
                row.startswith("🧱")
                or row.startswith("🟩")
                or row.startswith("🧑")
                or row.startswith("👹")
                or row.startswith("💰")
                or row.startswith("?")
                or "HP:" in row
                or "MODE:" in row
                or ">" in row
                or row.startswith("You move east.")  # Exclude map and previous messages
            ):
                print(row)


if __name__ == "__main__":
    if "--debug" in sys.argv:
        main_debug()
    else:
        # Default execution: run the curses-based game
        # GameEngine now handles its own curses setup and cleanup.
        # No need for curses.wrapper here if GameEngine.run() is self-contained.
        game = GameEngine(
            map_width=30, map_height=15, debug_mode=False
        )  # Ensure debug_mode is False
        try:
            game.run()
        except Exception as e:
            # This is a general catch-all if game.run() itself or its cleanup fails spectacularly.
            # GameEngine.run() has its own finally block for curses cleanup.
            # This will catch errors from GameEngine.__init__ if curses init fails there too.
            print(
                "----------------------------------------------------------------------"
            )
            print("The game encountered an unhandled error during execution:")
            print(f"Original Error: {type(e).__name__}: {e}")
            print("Traceback:")
            print(traceback.format_exc())
            print(
                "----------------------------------------------------------------------"
            )
            # Attempt a final curses cleanup if possible, though GameEngine should have done it.
            try:
                import curses  # Ensure curses is imported for this fallback

                if curses.has_colors():  # Check if curses was even initialized
                    curses.echo()
                    curses.nocbreak()
                    curses.endwin()
            except Exception:
                pass  # Avoid further errors during cleanup
