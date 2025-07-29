# deepseek_chat/config.py
"""
统一读取环境变量；BaseSettings 从 pydantic-settings 包里导入，
Field 仍然来自 pydantic。
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DeepSeek 相关配置
    deepseek_api_key: str | None = Field(None, env="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", env="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-chat", env="DEEPSEEK_MODEL")

    # MongoDB 相关配置
    mongo_uri: str = Field("mongodb://localhost:27017", env="MONGO_URI")
    mongo_db: str = Field("deepseek_chat", env="MONGO_DB")

    # 运行时可调整参数
    request_timeout: int = Field(60, env="REQUEST_TIMEOUT")   # 秒
    max_retries: int = Field(3, env="MAX_RETRIES")
    token_limit: int = Field(32000, env="TOKEN_LIMIT")        # 模型上下文最大 token 数

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
