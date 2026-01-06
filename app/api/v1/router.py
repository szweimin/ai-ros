
from fastapi import APIRouter
from app.api.v1 import (
    ros,
    diagnostics,
    health,
    system_info,
    fleet_diagnostics ,
    snapshot_ingestion 
)

router = APIRouter()

# 统一设置前缀
router.include_router(health.router, prefix="/health", tags=["健康检查"])
router.include_router(system_info.router, prefix="/system", tags=["系统信息"])
router.include_router(ros.router, prefix="/ros", tags=["ROS 文档"])
router.include_router(diagnostics.router, prefix="/diagnostics", tags=["故障诊断"])
router.include_router(fleet_diagnostics.router, prefix="/fleet-diagnostics", tags=["车队诊断"])  
router.include_router(snapshot_ingestion.router, prefix="/snapshot-ingestion", tags=["快照摄入"])
