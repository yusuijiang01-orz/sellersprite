"""
数据库连接和会话管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.database_url_async,
    echo=False,  # 生产环境设为 False
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 创建基类
Base = declarative_base()


async def get_db():
    """
    获取数据库会话的依赖函数
    用于 FastAPI 路由中
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """
    获取数据库会话（手动管理时使用）
    """
    async with async_session_maker() as session:
        return session
