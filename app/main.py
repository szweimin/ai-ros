from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from .api.v1.ros import router as ros_router
from .core.config import settings
from .repositories.database import DatabaseRepository
from .api.dependencies import get_embedding_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    db_repo = DatabaseRepository()
    await db_repo.init_db()
    print("Database initialized successfully")
    # 预热嵌入模型（如果使用本地模型，加载可能会花费一些时间）
    try:
        print("Preloading embedding service...")
        # 调用依赖以触发模型加载并缓存实例
        get_embedding_service()
        print("Embedding service preloaded")
    except Exception as e:
        print(f"Warning: failed to preload embedding service: {e}")
    
    yield
    
    # 关闭时清理资源
    print("Shutting down...")

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ros_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "ROS Documentation System API",
        "version": "1.0.0",
        "environment": settings.environment,
        "database": "PostgreSQL",
        "embedding_model": settings.embedding_model,
        "llm_model": "Ollama" if not settings.openai_api_key else "OpenAI",
        "endpoints": {
            "ingest_ros_topics": "POST /api/v1/ros/topics/ingest",
            "ingest_urdf": "POST /api/v1/ros/urdf/ingest",
            "ingest_safety_ops": "POST /api/v1/ros/operation/ingest",
            "query": "POST /api/v1/ros/query",
            "query_history": "GET /api/v1/ros/history"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)