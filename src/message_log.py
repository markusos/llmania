from typing import List


class MessageLog:
    """
    Manages a log of messages, ensuring it does not exceed a maximum size.
    """

    def __init__(self, max_messages: int = 5):
        """
        Initializes the MessageLog.

        Args:
            max_messages: The maximum number of messages to store.
                          Older messages are discarded when this limit is exceeded.
        """
        self.max_messages: int = max_messages
        self.messages: List[str] = []

    def add_message(self, text: str) -> None:
        """
        Adds a message to the log.

        If the log exceeds max_messages, the oldest messages are removed.

        Args:
            text: The message string to add.
        """
        self.messages.append(text)
        while len(self.messages) > self.max_messages:
            self.messages.pop(0)  # Remove the oldest message

    def clear(self) -> None:
        """
        Clears all messages from the log.
        """
        self.messages.clear()

    def get_messages(self) -> List[str]:
        """
        Returns a copy of the current messages in the log.

        Returns:
            A list of message strings.
        """
        return list(self.messages)  # Return a copy
