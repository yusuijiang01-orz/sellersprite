"""
应用配置模块
使用 Pydantic Settings 管理环境变量
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 数据库
    database_url: str = "postgresql://postgres:password@localhost:5432/sellersprite"
    database_url_async: str = "postgresql+asyncpg://postgres:password@localhost:5432/sellersprite"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # 爬虫
    proxy_list: str = ""
    min_request_delay: int = 2
    max_request_delay: int = 5

    # 亚马逊
    amazon_marketplace: str = "US"
    amazon_base_url: str = "https://www.amazon.com"

    # 缓存
    cache_ttl_seconds: int = 21600  # 6小时
    cache_search_prefix: str = "search:"

    # 日志
    log_level: str = "INFO"


settings = Settings()
