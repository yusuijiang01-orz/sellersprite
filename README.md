# SellerSprite Clone - 后端
# 亚马逊选品与数据分析工具 API

## 本地开发

1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接
```

4. 初始化数据库
```bash
python init_db.py
```

5. 启动服务
```bash
# 开发模式
uvicorn main:app --reload --port 8000

# 生产模式
gunicorn main:app -w 4 -b 0.0.0.0:8000
```

6. 启动 Celery Worker
```bash
celery -A celery_app worker --loglevel=info --pool=solo
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 技术栈

- FastAPI: Web 框架
- SQLAlchemy: ORM
- PostgreSQL: 主数据库
- Redis: 缓存 & 任务队列
- Celery: 异步任务
- Playwright: 爬虫
"# sellersprite" 
