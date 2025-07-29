"""
自定义异常，把 DeepSeek / Mongo / 业务错误做一次语义化封装，方便上层捕获。
"""

class DeepSeekError(Exception):
    """所有 DeepSeek 相关错误的基类"""


class DeepSeekRateLimitError(DeepSeekError):
    """HTTP 429"""


class DeepSeekServerError(DeepSeekError):
    """HTTP 5xx"""


class DeepSeekClientError(DeepSeekError):
    """HTTP 4xx（除 429）"""


class SessionNotFound(ValueError):
    """给定 session_id 在 DB 中不存在"""


class NodeNotFound(ValueError):
    """给定 node_id 在 DB 中不存在，或不属于当前会话"""


class TokenLimitExceeded(RuntimeError):
    """拼接 messages 超过模型上下文限制"""
