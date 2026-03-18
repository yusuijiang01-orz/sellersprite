"""
SellerSprite Clone - 数据库初始化脚本
初始化数据库表结构和基础数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import engine, Base
from app.models import (
    Keyword, Product, KeywordProduct, ProductHistory,
    FbaEstimate, ScrapeTask, MarketOverview, Skill, UserProgress
)


async def init_database():
    """初始化数据库"""
    print("=" * 50)
    print("SellerSprite Clone - 数据库初始化")
    print("=" * 50)

    async with engine.begin() as conn:
        # 删除所有表（谨慎使用！）
        print("\n[1/3] 删除旧表...")
        await conn.run_sync(Base.metadata.drop_all)
        print("  ✓ 所有表已删除")

        # 创建所有表
        print("\n[2/3] 创建新表...")
        await conn.run_sync(Base.metadata.create_all)
        print("  ✓ 所有表已创建")

        # 插入基础数据
        print("\n[3/3] 插入基础数据...")

        # 初始化技能数据
        skills = [
            {
                "skill_id": "double_jump",
                "name": "二段跳",
                "description": "在空中进行第二次跳跃",
                "skill_type": "jump",
                "unlock_score": 0,
                "cost": 0,
                "is_active": True
            },
            {
                "skill_id": "gravity_boots",
                "name": "重力靴",
                "description": "减少下落速度，更容易命中目标",
                "skill_type": "gravity",
                "unlock_score": 500,
                "cost": 100
            },
            {
                "skill_id": "sticky_feet",
                "name": "粘性脚掌",
                "description": "在平台上停留时间延长50%",
                "skill_type": "special",
                "unlock_score": 1000,
                "cost": 200
            },
            {
                "skill_id": "wind_control",
                "name": "风之掌控",
                "description": "可以利用风向辅助跳跃",
                "skill_type": "special",
                "unlock_score": 2000,
                "cost": 300
            },
            {
                "skill_id": "safe_landing",
                "name": "安全着陆",
                "description": "掉落时有一次免死机会",
                "skill_type": "special",
                "unlock_score": 1500,
                "cost": 250
            },
        ]

        for skill_data in skills:
            skill = Skill(**skill_data)
            conn.add(skill)

        print(f"  ✓ 已插入 {len(skills)} 个技能")

        await conn.commit()
        print("\n" + "=" * 50)
        print("✅ 数据库初始化完成！")
        print("=" * 50)


async def check_database():
    """检查数据库连接"""
    print("\n检查数据库连接...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("  ✓ 数据库连接正常")
            return True
    except Exception as e:
        print(f"  ✗ 数据库连接失败: {e}")
        return False


if __name__ == "__main__":
    async def main():
        if await check_database():
            await init_database()
        else:
            print("\n请检查数据库配置，确保 PostgreSQL 已启动")
            print("配置文件: .env")

    asyncio.run(main())
