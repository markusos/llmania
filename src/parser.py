class Parser:
    """
    Parses text input from the player into structured command tuples.
    It recognizes a variety of command verbs and their aliases,
    and extracts arguments where appropriate.
    """

    def parse_command(self, text_input: str) -> tuple[str, str | None] | None:
        """
        Parses a line of text input into a command verb and an optional argument.

        The method handles various aliases for commands (e.g., "n" for "move north",
        "get" for "take"). It converts the input to lowercase and strips whitespace.

        Args:
            text_input: The raw string input from the player.

        Returns:
            A tuple (verb, argument) if the command is recognized.
            'verb' is the canonical command action (e.g., "move", "take").
            'argument' is a string if an argument is present (e.g., "north", "potion"),
            or None if no argument is needed or provided for that verb.
            Returns None if the input is empty or the command is not recognized.
        """
        if not text_input.strip():
            return None  # Ignore empty or whitespace-only input

        words = text_input.lower().strip().split()
        command_verb = words[0]
        argument_parts = words[1:]
        # Join all parts after the verb to form the argument string
        argument = " ".join(argument_parts) if argument_parts else None

        # --- Movement Commands ---
        # Handles "move <direction>" and shorthand directions like "n", "north".
        if command_verb == "move":
            if argument in ["north", "south", "east", "west"]:
                return ("move", argument)
            else:
                # "move" with an invalid or missing direction
                return None  # Or potentially ("move", None) if we want to message "Move where?"
        elif command_verb in ["n", "north"]:
            if not argument:  # Shorthand directions should not have further arguments
                return ("move", "north")
        elif command_verb in ["s", "south"]:
            if not argument:
                return ("move", "south")
        elif command_verb in ["e", "east"]:
            if not argument:
                return ("move", "east")
        elif command_verb in ["w", "west"]:
            if not argument:
                return ("move", "west")

        # --- Item Interaction Commands ---
        # "take <item>" or "get <item>"
        elif command_verb in ["take", "get"]:
            if argument:  # Argument (item name) is required
                return ("take", argument)
            else:  # "take" without specifying an item
                return ("take", None)  # Let CommandProcessor handle "Take what?"

        # "drop <item>"
        elif command_verb == "drop":
            if argument:  # Argument (item name) is required
                return ("drop", argument)
            else:  # "drop" without specifying an item
                return ("drop", None)  # Let CommandProcessor handle "Drop what?"

        # "use <item>" or "u <item>"
        elif command_verb in ["use", "u"]:
            if argument:  # Argument (item name) is required
                return ("use", argument)
            else:  # "use" without specifying an item
                return ("use", None)  # Let CommandProcessor handle "Use what?"

        # --- Combat Commands ---
        # "attack <monster>" or "fight <monster>" or "f <monster>"
        elif command_verb in ["attack", "fight", "f"]:
            # Argument (monster name) is optional; CommandProcessor can auto-target if one monster.
            return ("attack", argument)  # Pass argument whether it's None or a name

        # --- Information Commands ---
        # "inventory" or "i"
        elif command_verb in ["inventory", "i"]:
            if not argument:  # These commands should not have arguments
                return ("inventory", None)
            else:  # e.g. "inventory sword" is invalid
                return None

        # "look" or "l"
        elif command_verb in ["look", "l"]:
            if not argument:  # "look" should not have arguments
                return ("look", None)
            else:  # e.g. "look monster" is not supported by this basic "look"
                return None  # A more advanced parser might handle "look <target>"

        # --- Game Control Commands ---
        # "quit" or "q" or "exit"
        elif command_verb in ["quit", "q", "exit"]:
            if not argument:  # These commands should not have arguments
                return ("quit", None)
            else:
                return None

        # If the command verb is not recognized after all checks
        return None
