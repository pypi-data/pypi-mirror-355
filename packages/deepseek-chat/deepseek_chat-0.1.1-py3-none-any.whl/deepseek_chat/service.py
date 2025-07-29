# deepseek_chat/service.py
"""Business orchestration – connect client ↔ store with token trimming."""
from __future__ import annotations

from typing import Dict, List, Tuple

from .client import DeepSeekClient
from .store import ChatStore, NodeNotFound, SessionNotFound
from .utils import ensure_token_budget

__all__ = ["ChatService"]


class ChatService:
    """High-level API specified in the product requirements."""

    def __init__(self, *, client: DeepSeekClient | None = None, store: ChatStore | None = None):
        self._client = client or DeepSeekClient()
        self._store = store or ChatStore()

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def create_session(
        self,
        *,
        system_prompt: str,
        question: str,
        model: str | None = None,
    ) -> Tuple[str, str, str]:
        """
        Return ``(answer, session_id, node_id)``.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        messages = ensure_token_budget(messages)

        rsp = self._client.chat(messages=messages, model=model)
        answer = rsp["choices"][0]["message"]["content"].strip()
        node_id = rsp["id"]

        assistant_msg = {"role": "assistant", "content": answer, "id": node_id}
        full_path = messages + [assistant_msg]

        session_id = self._store.create_session(system_prompt=system_prompt, model=model or self._client.model)
        self._store.create_node(
            session_id=session_id,
            parent_id=None,
            user_question=question,
            assistant_answer=answer,
            messages_path=full_path,
        )
        return answer, session_id, node_id

    def continue_chat(
        self,
        *,
        session_id: str,
        parent_node_id: str,
        question: str,
        model: str | None = None,
    ) -> Tuple[str, str]:
        """
        Return ``(answer, new_node_id)``.
        """
        parent = self._store.get_node(parent_node_id)
        if str(parent["session_id"]) != session_id:
            raise SessionNotFound(f"Node {parent_node_id} not in session {session_id}")

        path = parent["messages_path"] + [{"role": "user", "content": question}]
        path = ensure_token_budget(path)

        rsp = self._client.chat(messages=path, model=model)
        answer = rsp["choices"][0]["message"]["content"].strip()
        new_node_id = rsp["id"]

        full_path = path + [{"role": "assistant", "content": answer, "id": new_node_id}]
        self._store.create_node(
            session_id=session_id,
            parent_id=parent_node_id,
            user_question=question,
            assistant_answer=answer,
            messages_path=full_path,
        )
        return answer, new_node_id

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def get_tree(self, session_id: str):
        """Return entire tree dict."""
        return self._store.get_tree(session_id)
