"""
更新主路由以包含诊断API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from .api.v1.ros import router as ros_router
from .api.v1.diagnostic_api import router as diagnostic_router
from .core.config import settings
from .repositories.database import DatabaseRepository
from .api.dependencies import get_embedding_service, get_diagnostic_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    db_repo = DatabaseRepository()
    await db_repo.init_db()
    print("Database initialized successfully")
    
    # 预热嵌入模型
    try:
        print("Preloading embedding service...")
        get_embedding_service()
        print("Embedding service preloaded")
    except Exception as e:
        print(f"Warning: failed to preload embedding service: {e}")
    
    # 预热诊断服务
    try:
        print("Loading diagnostic service...")
        diagnostic_service = get_diagnostic_service()
        error_count = len(diagnostic_service.get_available_error_codes())
        print(f"Diagnostic service loaded with {error_count} error codes")
    except Exception as e:
        print(f"Warning: failed to load diagnostic service: {e}")
    
    yield
    
    # 关闭时清理资源
    print("Shutting down...")

app = FastAPI(
    title=settings.app_name + " with Diagnostics",
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
app.include_router(diagnostic_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "ROS Documentation System with Fault Diagnosis",
        "version": "2.0.0",
        "environment": settings.environment,
        "features": {
            "static_knowledge": True,
            "runtime_integration": True,
            "fault_diagnosis_trees": True,
            "engineering_diagnostics": True
        },
        "endpoints": {
            "ingest_ros_topics": "POST /api/v1/ros/topics/ingest",
            "ingest_urdf": "POST /api/v1/ros/urdf/ingest",
            "ingest_safety_ops": "POST /api/v1/ros/operation/ingest",
            "query": "POST /api/v1/ros/query",
            "query_with_runtime": "POST /api/v1/ros/query-with-runtime",
            "diagnostic_analyze": "POST /api/v1/diagnostics/analyze",
            "available_diagnoses": "GET /api/v1/diagnostics/available",
            "get_fault_tree": "GET /api/v1/diagnostics/tree/{error_code}",
            "query_history": "GET /api/v1/ros/history"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
