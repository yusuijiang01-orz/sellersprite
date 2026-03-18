"""
Celery 任务配置
异步任务处理：爬虫、数据处理
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "sellersprite",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"]
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务队列
    task_routes={
        "app.tasks.scrape_keyword": {"queue": "scrape"},
        "app.tasks.update_product_history": {"queue": "history"},
        "app.tasks.calculate_market_overview": {"queue": "analytics"},
    },
    
    # 任务优先级
    task_inherit_parent_priority=True,
    task_default_priority=5,
    task_acks_late=True,  # 任务完成后才确认
    worker_prefetch_multiplier=1,  # 每个 worker 一次只取1个任务
    
    # 重试策略
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # 结果过期时间
    result_expires=3600,  # 1小时后过期
)


# 定时任务配置（可选）
celery_app.conf.beat_schedule = {
    # 每天凌晨更新市场概览缓存
    "update-market-overview-daily": {
        "task": "app.tasks.calculate_market_overview",
        "schedule": crontab(hour=0, minute=0),
    },
}


# 导入任务模块
from app import tasks
