# deepseek_chat/schema.py
"""Pydantic schema models for type‑safe I/O across layers.

These are *optional* but extremely handy for runtime validation and IDE
intellisense.  Service layer will rely on them; other layers may keep
using plain dicts for flexibility.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator

# ---------------------------------------------------------------------------
# Primitive message schema  --------------------------------------------------
# ---------------------------------------------------------------------------
class MessageModel(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    id: Optional[str] = None  # DeepSeek chatcmpl id for assistant messages


# ---------------------------------------------------------------------------
# Session & Node DB documents  ----------------------------------------------
# ---------------------------------------------------------------------------
class SessionDocument(BaseModel):
    id: str = Field(alias="_id")
    system_prompt: str
    model: str = "deepseek-chat"
    created_at: datetime
    metadata: dict = {}


class NodeDocument(BaseModel):
    id: str = Field(alias="_id")
    session_id: str
    parent_id: Optional[str]
    user_question: str
    assistant_answer: str
    messages_path: List[MessageModel]
    created_at: datetime

    @validator("messages_path")
    def ensure_last_has_id(cls, v):  # noqa: N805
        if v and v[-1].role == "assistant" and not v[-1].id:
            raise ValueError("Assistant message must contain `id` field")
        return v
