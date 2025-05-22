class Parser:
    def parse_command(self, text_input: str) -> tuple[str, str | None] | None:
        if not text_input.strip():
            return None

        words = text_input.lower().strip().split()
        command_verb = words[0]
        argument_parts = words[1:]
        argument = " ".join(argument_parts) if argument_parts else None

        # Movement commands
        if command_verb == "move":
            if argument == "north":
                return ("move", "north")
            elif argument == "south":
                return ("move", "south")
            elif argument == "east":
                return ("move", "east")
            elif argument == "west":
                return ("move", "west")
            else:  # "move" without valid direction or with other words
                return None
        elif command_verb in ["n", "north"]:
            if not argument or argument == "north":  # handles "n" or "north"
                return ("move", "north")
        elif command_verb in ["s", "south"]:
            if not argument or argument == "south":
                return ("move", "south")
        elif command_verb in ["e", "east"]:
            if not argument or argument == "east":
                return ("move", "east")
        elif command_verb in ["w", "west"]:
            if not argument or argument == "west":
                return ("move", "west")

        # "take <item>" commands
        elif command_verb in ["take", "get"]:
            if argument:
                return ("take", argument)
            else:  # "take" without argument
                return None

        # "drop <item>" commands
        elif command_verb == "drop":
            if argument:
                return ("drop", argument)
            else:  # "drop" without argument
                return None

        # "use <item>" commands
        elif command_verb == "use":
            if argument:
                return ("use", argument)
            else:  # "use" without argument
                return None

        # "attack <monster>" commands
        elif command_verb in ["attack", "fight"]:
            if argument:
                return ("attack", argument)
            else:  # "attack" without argument
                return None

        # "inventory" or "i" commands
        elif command_verb in ["inventory", "i"]:
            if not argument:  # "inventory" or "i" should not have arguments
                return ("inventory", None)
            else:
                return None

        # "look" or "l" commands
        elif command_verb in ["look", "l"]:
            if not argument:  # "look" or "l" should not have arguments
                return ("look", None)
            else:
                return None

        # "quit" or "q" commands
        elif command_verb in ["quit", "q"]:
            if not argument:  # "quit" or "q" should not have arguments
                return ("quit", None)
            else:
                return None

        # If the command is not recognized
        return None
