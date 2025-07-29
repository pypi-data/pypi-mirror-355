# deepseek_chat/store.py
"""MongoDB persistence layer (Milestone M2).

This module hides all direct database operations behind the `ChatStore`
class so that the service layer can stay database‑agnostic.  The design
faithfully follows the data‑model agreed in the planning doc:

• Collection **sessions**   – one document per conversation
• Collection **nodes**      – one document per dialogue node (tree)

For ease of use every public method returns **primitive Python types**
(dict / str) that are JSON‑serialisable – no raw ObjectId leaks.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

__all__ = ["ChatStore", "SessionNotFound", "NodeNotFound"]


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SessionNotFound(KeyError):
    """Raised when a session_id does not exist."""


class NodeNotFound(KeyError):
    """Raised when a node_id does not exist."""


# ---------------------------------------------------------------------------
# Main store class
# ---------------------------------------------------------------------------
class ChatStore:
    """High‑level wrapper around two MongoDB collections.

    Parameters
    ----------
    mongo_uri
        Defaults to env ``MONGO_URI`` or ``mongodb://localhost:27017``.
    db_name
        Defaults to env ``MONGO_DB`` or ``deepseek_chat``.
    """

    def __init__(self, mongo_uri: str | None = None, db_name: str | None = None) -> None:
        uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self._client: MongoClient = MongoClient(uri, tz_aware=True)
        self._db: Database = self._client[db_name or os.getenv("MONGO_DB", "deepseek_chat")]

        self._sessions: Collection = self._db["sessions"]
        self._nodes: Collection = self._db["nodes"]
        self._ensure_indexes()

    # ------------------------------------------------------------------
    # Sessions CRUD
    # ------------------------------------------------------------------
    def create_session(
        self,
        *,
        system_prompt: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Insert a session and return its id (str)."""
        doc = {
            "system_prompt": system_prompt,
            "model": model,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
        }
        result = self._sessions.insert_one(doc)
        return str(result.inserted_id)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        doc = self._sessions.find_one({"_id": ObjectId(session_id)})
        if not doc:
            raise SessionNotFound(session_id)
        return self._clean_id(doc)

    # ------------------------------------------------------------------
    # Nodes CRUD
    # ------------------------------------------------------------------
    def create_node(
            self,
            *,
            session_id: str,
            parent_id: str | None,
            user_question: str,
            assistant_answer: str,
            messages_path: List[Dict[str, str]],
    ) -> str:
        """
        Insert a dialogue node; node_id = DeepSeek completion id.

        `role` 字段不再硬编码为 assistant，数据语义由 messages_path 决定。
        """
        node_id = messages_path[-1].get("id")
        if not node_id:
            raise ValueError("messages_path last element must contain 'id'")

        doc = {
            "_id": node_id,
            "session_id": ObjectId(session_id),
            "parent_id": parent_id,
            "user_question": user_question,
            "assistant_answer": assistant_answer,
            "messages_path": messages_path,
            "created_at": datetime.utcnow(),
        }
        self._nodes.insert_one(doc)
        return node_id

    def get_node(self, node_id: str) -> Dict[str, Any]:
        doc = self._nodes.find_one({"_id": node_id})
        if not doc:
            raise NodeNotFound(node_id)
        return self._clean_id(doc)

    # ------------------------------------------------------------------
    # Tree utilities
    # ------------------------------------------------------------------
    def get_children(self, parent_id: str) -> List[Dict[str, Any]]:
        cursor = self._nodes.find({"parent_id": parent_id}).sort("created_at", ASCENDING)
        return [self._clean_id(doc) for doc in cursor]

    def get_tree(self, session_id: str) -> Dict[str, Any]:
        """Return entire dialogue tree as nested dict structure."""
        root_nodes = list(self._nodes.find({
            "session_id": ObjectId(session_id),
            "parent_id": None,
        }))
        if not root_nodes:
            raise SessionNotFound(session_id)

        root = root_nodes[0]
        return self._build_subtree(root)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_subtree(self, node_doc: Dict[str, Any]) -> Dict[str, Any]:
        node = self._clean_id(node_doc)
        children_docs = self._nodes.find({"parent_id": node["id"]}).sort("created_at", ASCENDING)
        node["children"] = [self._build_subtree(doc) for doc in children_docs]
        return node

    @staticmethod
    def _clean_id(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ObjectId to str & pop Mongo internal fields."""
        doc = dict(doc)  # shallow copy
        doc["id"] = str(doc.pop("_id"))
        sid = doc.get("session_id")
        if isinstance(sid, ObjectId):
            doc["session_id"] = str(sid)
        return doc

    def _ensure_indexes(self) -> None:
        self._sessions.create_index("created_at")
        self._nodes.create_index([("session_id", ASCENDING), ("parent_id", ASCENDING)])
        self._nodes.create_index("created_at")
