import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.lifespan import lifespan

app = FastAPI(
    title="ROS Documentation System with Fault Diagnosis",
    description="ROS 文档系统与故障诊断",
    version="2.0.0",
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 - 使用正确的 prefix
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    
    # 调试：打印所有路由
    print("\n=== 注册的路由 ===")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path}")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)