# deepseek_chat/__init__.py
"""
Package façade

• 提供「类式」（ChatService）和「函数式」三大便捷接口
• DeepSeek / MongoDB 参数可通过 *函数参数* 覆盖，不必只依赖环境变量
• 新增存储后端选项:
    - store_backend="mongo"  (默认，兼容旧代码)
    - store_backend="file"   (本地 JSON 文件，无需 Mongo)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional, Tuple

from .client import DeepSeekClient
from .filestore import FileStore          # 轻量 JSON 存储
from .service import ChatService
from .store import ChatStore              # Mongo 存储

__all__ = [
    "ChatService",
    "create_session",
    "continue_chat",
    "get_tree",
]

# ---------------------------------------------------------------------------#
# 单例 (默认走环境变量 + Mongo)                                               #
# ---------------------------------------------------------------------------#
@lru_cache(maxsize=1)
def _get_default_service() -> ChatService:
    return ChatService()                  # 默认 DeepSeekClient & ChatStore 均用 ENV


# ---------------------------------------------------------------------------#
# 构造自定义 Service（覆盖 API key / BaseURL / 存储后端等）                   #
# ---------------------------------------------------------------------------#
def _build_service(
    *,
    api_key: Optional[str],
    base_url: Optional[str],
    model: Optional[str],
    store_backend: str,
    mongo_uri: Optional[str],
    json_path: Optional[str],
) -> ChatService:
    client = DeepSeekClient(api_key=api_key, base_url=base_url, model=model)

    if store_backend == "file":
        store = FileStore(json_path)
    else:  # "mongo"
        store = ChatStore(mongo_uri=mongo_uri)

    return ChatService(client=client, store=store)


# ---------------------------------------------------------------------------#
# 函数式入口 1: create_session                                               #
# ---------------------------------------------------------------------------#
def create_session(
    *,
    system_prompt: str,
    question: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    store_backend: str = "mongo",       # "mongo" | "file"
    mongo_uri: Optional[str] = None,
    json_path: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Start a new conversation and return (answer, session_id, node_id)."""
    use_custom = any(
        [api_key, base_url, mongo_uri, json_path, store_backend != "mongo"]
    )
    svc = (
        _build_service(
            api_key=api_key,
            base_url=base_url,
            model=model,
            store_backend=store_backend,
            mongo_uri=mongo_uri,
            json_path=json_path,
        )
        if use_custom
        else _get_default_service()
    )
    return svc.create_session(system_prompt=system_prompt, question=question, model=model)


# ---------------------------------------------------------------------------#
# 函数式入口 2: continue_chat                                                #
# ---------------------------------------------------------------------------#
def continue_chat(
    *,
    session_id: str,
    parent_node_id: str,
    question: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    store_backend: str = "mongo",
    mongo_uri: Optional[str] = None,
    json_path: Optional[str] = None,
) -> Tuple[str, str]:
    """Append a new turn and return (answer, new_node_id)."""
    use_custom = any(
        [api_key, base_url, mongo_uri, json_path, store_backend != "mongo"]
    )
    svc = (
        _build_service(
            api_key=api_key,
            base_url=base_url,
            model=model,
            store_backend=store_backend,
            mongo_uri=mongo_uri,
            json_path=json_path,
        )
        if use_custom
        else _get_default_service()
    )
    return svc.continue_chat(
        session_id=session_id,
        parent_node_id=parent_node_id,
        question=question,
        model=model,
    )


# ---------------------------------------------------------------------------#
# 函数式入口 3: get_tree                                                     #
# ---------------------------------------------------------------------------#
def get_tree(
    session_id: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    store_backend: str = "mongo",
    mongo_uri: Optional[str] = None,
    json_path: Optional[str] = None,
) -> dict:
    """Return the full conversation tree."""
    use_custom = any(
        [api_key, base_url, mongo_uri, json_path, store_backend != "mongo"]
    )
    svc = (
        _build_service(
            api_key=api_key,
            base_url=base_url,
            model=None,
            store_backend=store_backend,
            mongo_uri=mongo_uri,
            json_path=json_path,
        )
        if use_custom
        else _get_default_service()
    )
    return svc.get_tree(session_id)
