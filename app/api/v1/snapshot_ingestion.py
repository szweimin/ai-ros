from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.security import APIKeyHeader
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
from pydantic import BaseModel, Field

# 导入现有的模型
from app.models.runtime_snapshot import RuntimeSnapshot, SnapshotSource

# ========== 硬编码配置 ==========
SNAPSHOT_CONFIG = {
    "valid_api_keys": ["edge-adapter-ros-key", "edge-adapter-plc-key", "edge-adapter-simulator-key"],
    "max_history": 1000,
    "analysis_enabled": True,
    "max_batch_size": 100,
    "processing_timeout": 30
}

# ========== 响应模型定义 ==========
class SnapshotResponse(BaseModel):
    """快照响应模型"""
    status: str
    message: str
    snapshot_id: str
    timestamp: str
    robot_id: str
    errors_count: int
    has_errors: bool

class BatchSnapshotRequest(BaseModel):
    """批量快照请求"""
    snapshots: List[RuntimeSnapshot]

class BatchResponse(BaseModel):
    """批量响应模型"""
    status: str
    message: str
    valid_count: int
    invalid_count: int
    invalid_snapshots: List[Dict[str, Any]]
    timestamp: str

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    service: str
    version: str
    timestamp: str
    snapshot_count: int
    unique_robots: int
    last_snapshot: Optional[str]
    config: Dict[str, Any]

class HistoryItem(BaseModel):
    """历史记录项"""
    robot_id: str
    timestamp: str
    model: str
    firmware: str
    errors: List[str]
    error_count: int
    joint_count: int
    topic_count: int
    source: str
    has_errors: bool

class StatsResponse(BaseModel):
    """统计响应模型"""
    status: str
    timestamp: str
    summary: Dict[str, Any]
    distribution: Dict[str, Any]

class RobotsResponse(BaseModel):
    """机器人列表响应"""
    status: str
    timestamp: str
    summary: Dict[str, Any]
    robots: List[Dict[str, Any]]

class ClearResponse(BaseModel):
    """清空响应模型"""
    status: str
    message: str
    timestamp: str

# ========== 路由和服务 ==========
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 依赖项
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# 简单服务类
class RuntimeService:
    def snapshot_to_context(self, snapshot: RuntimeSnapshot) -> str:
        context = (
            f"[ROBOT SNAPSHOT] {snapshot.timestamp}\n"
            f"Robot: {snapshot.robot_id} | Model: {snapshot.model} | "
            f"Firmware: {snapshot.firmware} | Source: {snapshot.source.value}\n"
            f"Errors: {', '.join(snapshot.errors) if snapshot.errors else 'None'}\n"
            f"Joint States: {json.dumps(snapshot.joint_states, indent=2)}\n"
            f"Active Topics: {', '.join(snapshot.active_topics)}\n"
        )
        return context
    
    def validate_snapshot(self, snapshot: RuntimeSnapshot) -> bool:
        try:
            datetime.fromisoformat(snapshot.timestamp.replace('Z', '+00:00'))
            return bool(snapshot.robot_id and snapshot.timestamp)
        except (ValueError, AttributeError):
            return False

# 初始化服务
runtime_service = RuntimeService()

# 内存存储
snapshot_store = []

def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """验证Edge Adapter API Key"""
    if not api_key or api_key not in SNAPSHOT_CONFIG["valid_api_keys"]:
        raise HTTPException(
            status_code=403, 
            detail="Invalid API key"
        )
    return api_key

async def process_snapshot_async(snapshot: RuntimeSnapshot):
    """异步处理快照"""
    try:
        # 存储快照（检查限制）
        if len(snapshot_store) >= SNAPSHOT_CONFIG["max_history"]:
            snapshot_store.pop(0)
        
        snapshot_store.append(snapshot)
        logger.info(f"Stored snapshot for robot {snapshot.robot_id}")
        
        # 转换为RAG上下文
        context = runtime_service.snapshot_to_context(snapshot)
        logger.info(f"Context generated for {snapshot.robot_id}")
        
        # 这里可以添加AI分析逻辑
        if SNAPSHOT_CONFIG["analysis_enabled"]:
            logger.info(f"AI analysis would be triggered for {snapshot.robot_id}")
        
        return {"stored": True, "context_generated": True}
        
    except Exception as e:
        logger.error(f"Error processing snapshot: {e}")
        return {"error": str(e)}

@router.get("/",
         summary="API 根路径",
         description="快照摄入API基本信息")
async def root():
    """API根路径"""
    return {
        "api": "Runtime Snapshot Ingestion API",
        "version": "1.0.0",
        "description": "接收Edge Adapter的运行时快照数据",
        "endpoints": {
            "GET /": "此页面（API信息）",
            "GET /health": "健康检查",
            "POST /snapshot": "接收单个快照",
            "POST /batch": "批量接收快照",
            "GET /history/{robot_id}": "获取历史快照",
            "GET /stats": "统计信息",
            "GET /robots": "机器人列表",
            "DELETE /clear": "清空快照数据（测试用）"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health",
         summary="健康检查",
         description="快照摄入服务健康检查",
         response_model=HealthResponse)
async def health_check():
    """健康检查"""
    last_snapshot = snapshot_store[-1].timestamp if snapshot_store else None
    unique_robots = len(set(s.robot_id for s in snapshot_store)) if snapshot_store else 0
    
    return HealthResponse(
        status="healthy",
        service="snapshot-ingestion-api",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        snapshot_count=len(snapshot_store),
        unique_robots=unique_robots,
        last_snapshot=last_snapshot,
        config={
            "max_history": SNAPSHOT_CONFIG["max_history"],
            "analysis_enabled": SNAPSHOT_CONFIG["analysis_enabled"],
            "valid_api_keys_count": len(SNAPSHOT_CONFIG["valid_api_keys"])
        }
    )

@router.post("/snapshot", 
          summary="接收单个快照",
          description="从Edge Adapter接收单个运行时快照",
          response_model=SnapshotResponse)
async def ingest_runtime_snapshot(
    snapshot: RuntimeSnapshot,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    接收单个运行时快照
    
    - **snapshot**: 运行时快照数据
    - **api_key**: Edge Adapter身份验证
    
    返回：处理结果
    """
    try:
        # 验证快照
        if not runtime_service.validate_snapshot(snapshot):
            raise HTTPException(status_code=422, detail="Invalid snapshot data")
        
        # 异步处理快照
        background_tasks.add_task(process_snapshot_async, snapshot)
        
        # 返回响应
        return SnapshotResponse(
            status="accepted",
            message="Snapshot received and queued for processing",
            snapshot_id=f"{snapshot.robot_id}_{snapshot.timestamp}",
            timestamp=datetime.utcnow().isoformat(),
            robot_id=snapshot.robot_id,
            errors_count=len(snapshot.errors),
            has_errors=len(snapshot.errors) > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/batch",
         summary="批量接收快照",
         description="批量接收多个运行时快照",
         response_model=BatchResponse)
async def ingest_batch_snapshots(
    request: BatchSnapshotRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    批量接收快照
    
    - **snapshots**: 快照列表
    - **api_key**: Edge Adapter身份验证
    """
    try:
        snapshots = request.snapshots
        
        # 检查批量大小限制
        if len(snapshots) > SNAPSHOT_CONFIG["max_batch_size"]:
            raise HTTPException(
                status_code=400,
                detail=f"Batch size {len(snapshots)} exceeds maximum {SNAPSHOT_CONFIG['max_batch_size']}"
            )
        
        valid_snapshots = []
        invalid_snapshots = []
        
        # 验证每个快照
        for snapshot in snapshots:
            if runtime_service.validate_snapshot(snapshot):
                valid_snapshots.append(snapshot)
                # 异步处理每个快照
                background_tasks.add_task(process_snapshot_async, snapshot)
            else:
                invalid_snapshots.append({
                    "robot_id": snapshot.robot_id,
                    "timestamp": snapshot.timestamp,
                    "error": "Invalid snapshot data"
                })
        
        return BatchResponse(
            status="accepted",
            message=f"Batch processing started: {len(valid_snapshots)} valid, {len(invalid_snapshots)} invalid",
            valid_count=len(valid_snapshots),
            invalid_count=len(invalid_snapshots),
            invalid_snapshots=invalid_snapshots,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{robot_id}",
         summary="获取历史快照",
         description="获取机器人的历史快照记录",
         response_model=List[HistoryItem])
async def get_snapshot_history(
    robot_id: str,
    limit: Optional[int] = Query(10, ge=1, le=100, description="返回数量限制"),
    api_key: str = Depends(verify_api_key)
):
    """获取机器人历史快照"""
    # 筛选指定机器人的快照
    robot_snapshots = [s for s in snapshot_store if s.robot_id == robot_id]
    
    if not robot_snapshots:
        return []
    
    # 按时间戳排序（最新的在前）
    robot_snapshots.sort(key=lambda x: x.timestamp, reverse=True)
    
    # 限制返回数量
    robot_snapshots = robot_snapshots[:limit]
    
    # 转换为响应格式
    result = []
    for snapshot in robot_snapshots:
        result.append(HistoryItem(
            robot_id=snapshot.robot_id,
            timestamp=snapshot.timestamp,
            model=snapshot.model,
            firmware=snapshot.firmware,
            errors=snapshot.errors,
            error_count=len(snapshot.errors),
            joint_count=len(snapshot.joint_states),
            topic_count=len(snapshot.active_topics),
            source=snapshot.source.value,
            has_errors=len(snapshot.errors) > 0
        ))
    
    return result

@router.get("/stats",
         summary="统计信息",
         description="获取快照数据的统计信息",
         response_model=StatsResponse)
async def get_snapshot_stats(
    api_key: str = Depends(verify_api_key)
):
    """获取快照统计信息"""
    if not snapshot_store:
        return StatsResponse(
            status="no_data",
            timestamp=datetime.utcnow().isoformat(),
            summary={"message": "No snapshots available"},
            distribution={}
        )
    
    # 统计计算
    total_snapshots = len(snapshot_store)
    unique_robots = set(s.robot_id for s in snapshot_store)
    snapshots_with_errors = sum(1 for s in snapshot_store if s.errors)
    error_rate = snapshots_with_errors / total_snapshots
    
    # 错误分布
    error_distribution = {}
    for snapshot in snapshot_store:
        for error in snapshot.errors:
            if error not in error_distribution:
                error_distribution[error] = 0
            error_distribution[error] += 1
    
    # 机器人活跃度
    robot_activity = {}
    for snapshot in snapshot_store:
        robot_id = snapshot.robot_id
        if robot_id not in robot_activity:
            robot_activity[robot_id] = 0
        robot_activity[robot_id] += 1
    
    # 源分布
    source_distribution = {}
    for snapshot in snapshot_store:
        source = snapshot.source.value
        if source not in source_distribution:
            source_distribution[source] = 0
        source_distribution[source] += 1
    
    return StatsResponse(
        status="success",
        timestamp=datetime.utcnow().isoformat(),
        summary={
            "total_snapshots": total_snapshots,
            "unique_robots": len(unique_robots),
            "snapshots_with_errors": snapshots_with_errors,
            "error_rate": f"{error_rate:.2%}",
            "time_range": {
                "earliest": min(s.timestamp for s in snapshot_store),
                "latest": max(s.timestamp for s in snapshot_store)
            }
        },
        distribution={
            "errors": dict(sorted(error_distribution.items(), key=lambda x: x[1], reverse=True)[:10]),
            "robots": dict(sorted(robot_activity.items(), key=lambda x: x[1], reverse=True)),
            "sources": source_distribution
        }
    )

@router.get("/robots",
         summary="机器人列表",
         description="获取所有机器人的列表和状态",
         response_model=RobotsResponse)
async def get_robots_list(
    api_key: str = Depends(verify_api_key)
):
    """获取机器人列表"""
    if not snapshot_store:
        return RobotsResponse(
            status="no_data",
            timestamp=datetime.utcnow().isoformat(),
            summary={
                "total_robots": 0,
                "robots_with_errors": 0,
                "error_rate": "0%"
            },
            robots=[]
        )
    
    # 按机器人分组，获取最新状态
    robots = {}
    for snapshot in snapshot_store:
        robot_id = snapshot.robot_id
        if robot_id not in robots or snapshot.timestamp > robots[robot_id]["timestamp"]:
            robots[robot_id] = {
                "robot_id": robot_id,
                "model": snapshot.model,
                "firmware": snapshot.firmware,
                "timestamp": snapshot.timestamp,
                "errors": snapshot.errors,
                "has_errors": len(snapshot.errors) > 0,
                "error_count": len(snapshot.errors),
                "source": snapshot.source.value,
                "status": "error" if snapshot.errors else "normal"
            }
    
    # 转换为列表并按机器人ID排序
    robots_list = sorted(robots.values(), key=lambda x: x["robot_id"])
    
    # 统计
    total_robots = len(robots_list)
    robots_with_errors = sum(1 for r in robots_list if r["has_errors"])
    error_rate = robots_with_errors / total_robots if total_robots > 0 else 0
    
    return RobotsResponse(
        status="success",
        timestamp=datetime.utcnow().isoformat(),
        summary={
            "total_robots": total_robots,
            "robots_with_errors": robots_with_errors,
            "error_rate": f"{error_rate:.2%}"
        },
        robots=robots_list
    )

@router.delete("/clear",
         summary="清空快照",
         description="清空所有存储的快照数据（用于测试）",
         response_model=ClearResponse)
async def clear_snapshots(
    api_key: str = Depends(verify_api_key)
):
    """清空快照数据"""
    global snapshot_store
    count = len(snapshot_store)
    snapshot_store = []
    
    logger.info(f"Cleared {count} snapshots")
    
    return ClearResponse(
        status="success",
        message=f"Cleared {count} snapshots",
        timestamp=datetime.utcnow().isoformat()
    )