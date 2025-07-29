"""
Token helpers – count tokens & trim message list to fit model context.

深度求索官方尚未发布 tokenizer；若安装了 *tiktoken*
则用 GPT-4 的 tokenizer 近似计算，否则退化到「词数≈token」。
"""
from __future__ import annotations

from typing import Dict, List

try:
    import tiktoken
except ImportError:
    tiktoken = None  # noqa: N816

from .config import get_settings
from .exceptions import TokenLimitExceeded

_SETTINGS = get_settings()
_LIMIT = _SETTINGS.token_limit

# Use GPT-4 tokenizer as proxy if available
_ENCODER = tiktoken.encoding_for_model("gpt-4") if tiktoken else None


# ---------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------
def count_tokens(messages: List[Dict[str, str]]) -> int:
    """Rough token estimation."""
    if _ENCODER:
        # official-ish heuristic: 4 tokens per message + 2 priming
        return sum(len(_ENCODER.encode(m["content"])) + 4 for m in messages) + 2
    return sum(len(m["content"].split()) for m in messages)


def ensure_token_budget(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Trim earliest user/assistant pairs until total tokens <= limit.

    Strategy:
    • index 0 认为是 system，不删
    • 之后按 “早 -> 晚” pop，保证连续成对删除
    """
    if count_tokens(messages) <= _LIMIT:
        return messages

    # 保留 system，滑窗删除
    while len(messages) > 2 and count_tokens(messages) > _LIMIT:
        # 删除第二条 (第一条 user) 和第三条 (其 assistant) – 成对
        messages.pop(1)
        if len(messages) > 2 and messages[1]["role"] == "assistant":
            messages.pop(1)

    if count_tokens(messages) > _LIMIT:
        raise TokenLimitExceeded("Context still exceeds model limit after trimming.")

    return messages
