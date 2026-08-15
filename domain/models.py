from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    """A single turn in a conversation (role: "user" | "assistant")."""

    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Conversation:
    """Recent turns of one channel's conversation plus the last activity time."""

    messages: list[ChatMessage] = field(default_factory=list)
    last_activity: float = 0.0
