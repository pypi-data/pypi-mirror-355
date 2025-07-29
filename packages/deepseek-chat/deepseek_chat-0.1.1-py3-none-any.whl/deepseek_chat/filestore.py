"""
FileStore – drop-in replacement for Mongo-backed ChatStore.

• 数据持久化到一个 JSON 文件（默认 ~/.deepseek_chat/history.json）
• 结构与 Mongo 版一致：sessions / nodes 两张“表”
• 适合 PoC、本地离线使用，不依赖 pymongo
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class FileStore:
    def __init__(self, path: str | None = None) -> None:
        self._path = Path(path or Path.home() / ".deepseek_chat" / "history.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            self._data = json.loads(self._path.read_text("utf-8"))
        else:
            self._data = {"sessions": [], "nodes": []}
            self._flush()

    # ------------------------------------------------------------------ helpers
    def _flush(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(self._path)

    def _now(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # ------------------------------------------------------------------ sessions
    def create_session(self, *, system_prompt: str, model: str, metadata: dict | None = None) -> str:
        sid = str(uuid.uuid4())
        self._data["sessions"].append(
            {
                "id": sid,
                "system_prompt": system_prompt,
                "model": model,
                "created_at": self._now(),
                "metadata": metadata or {},
            }
        )
        self._flush()
        return sid

    def get_session(self, session_id: str) -> Dict:
        for s in self._data["sessions"]:
            if s["id"] == session_id:
                return s
        raise KeyError(f"Session {session_id} not found")

    # ------------------------------------------------------------------ nodes
    def create_node(
        self,
        *,
        session_id: str,
        parent_id: str | None,
        user_question: str,
        assistant_answer: str,
        messages_path: List[Dict],
    ) -> str:
        node_id = messages_path[-1].get("id") or str(uuid.uuid4())
        self._data["nodes"].append(
            {
                "id": node_id,
                "session_id": session_id,
                "parent_id": parent_id,
                "user_question": user_question,
                "assistant_answer": assistant_answer,
                "messages_path": messages_path,
                "created_at": self._now(),
            }
        )
        self._flush()
        return node_id

    def get_node(self, node_id: str) -> Dict:
        for n in self._data["nodes"]:
            if n["id"] == node_id:
                return n
        raise KeyError(f"Node {node_id} not found")

    # ------------------------------------------------------------------ tree
    def get_tree(self, session_id: str) -> Dict:
        roots = [n for n in self._data["nodes"] if n["session_id"] == session_id and n["parent_id"] is None]
        if not roots:
            raise KeyError(f"Session {session_id} not found")
        return self._build_subtree(roots[0])

    def _build_subtree(self, node: Dict) -> Dict:
        children = [n for n in self._data["nodes"] if n["parent_id"] == node["id"]]
        node = dict(node)  # shallow-copy
        node["children"] = [self._build_subtree(c) for c in children]
        return node
