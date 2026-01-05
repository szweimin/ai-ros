# app/api/v1/__init__.py

# 导出所有模块，便于导入
from .health import router as health_router
from .system_info import router as system_info_router
from .ros import router as ros_router
from .diagnostics import router as diagnostics_router

__all__ = [
    'health_router',
    'system_info_router', 
    'ros_router',
    'diagnostics_router'
]