"""HeartBuddy 配置中心 — 从 .env 文件和环境变量读取设置"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置，所有值可从 .env 文件或环境变量覆盖"""

    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # 数据库
    db_path: str = "data/heartbuddy.db"

    # 日志
    log_path: str = "logs/heartbuddy.log"

    # 上下文
    max_context_messages: int = 20

    # 模型参数
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# 单例
settings = Settings()
