"""
SellerSprite Clone - 主应用入口
亚马逊选品与数据分析工具 API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api import products, search, market, fba


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时：关闭数据库连接
    await engine.dispose()


# 创建 FastAPI 应用
app = FastAPI(
    title="SellerSprite Clone API",
    description="亚马逊选品与数据分析工具 - 后端 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(search.router, prefix="/api/v1", tags=["搜索"])
app.include_router(products.router, prefix="/api/v1", tags=["商品"])
app.include_router(market.router, prefix="/api/v1", tags=["市场"])
app.include_router(fba.router, prefix="/api/v1", tags=["FBA估算"])


@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "message": "SellerSprite Clone API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
