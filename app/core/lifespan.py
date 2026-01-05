from contextlib import asynccontextmanager

from app.repositories.database import DatabaseRepository
from app.api.dependencies import get_embedding_service, get_diagnostic_service


@asynccontextmanager
async def lifespan(app):
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
        diag_service = get_diagnostic_service()
        print(f"Diagnostic service loaded with {len(diag_service.get_available_error_codes())} error codes")
    except Exception as e:
        print(f"Warning: failed to load diagnostic service: {e}")
    
    yield
    
    # 关闭时清理资源
    print("Shutting down...")