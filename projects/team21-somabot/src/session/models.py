from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Session:
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    chat_history: list[dict] = field(default_factory=list)  # [{"role": ..., "content": ...}]

    def touch(self) -> None:
        self.last_active = datetime.utcnow()

    def append_turn(self, user_msg: str, assistant_msg: str) -> None:
        self.chat_history.append({"role": "user",      "content": user_msg})
        self.chat_history.append({"role": "assistant", "content": assistant_msg})
        self.touch()
