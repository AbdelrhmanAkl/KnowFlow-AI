from dataclasses import dataclass, field


@dataclass
class ConversationMemory:
    """
    Store conversation history for a single chat session.
    """

    messages: list[dict[str, str]] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""

        if not content or not content.strip():
            raise ValueError("User message cannot be empty.")

        self.messages.append(
            {
                "role": "user",
                "content": content.strip(),
            }
        )

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation."""

        if not content or not content.strip():
            raise ValueError("Assistant message cannot be empty.")

        self.messages.append(
            {
                "role": "assistant",
                "content": content.strip(),
            }
        )

    def get_messages(self) -> list[dict[str, str]]:
        """Return a copy of the conversation history."""

        return list(self.messages)

    def clear(self) -> None:
        """Clear the conversation history."""

        self.messages.clear()

    def __len__(self) -> int:
        """Return the number of stored messages."""

        return len(self.messages)
