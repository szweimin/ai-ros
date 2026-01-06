from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import APIKeyHeader
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from app.models.runtime_snapshot import RuntimeSnapshot, SnapshotSource
from app.services.runtime_service import RuntimeService
from app.services.ai_processor import AIProcessor
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["快照摄入"])

# 依赖项
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# 初始化服务（使用依赖注入）
runtime_service = RuntimeService()
ai_processor = AIProcessor()

# 内存存储（生产环境用数据库）
snapshot_store = []

from app.core.config import settings

def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """验证Edge Adapter API Key"""
    valid_keys = settings.snapshot_valid_api_keys_list  # 使用属性获取列表
    if not api_key or api_key not in valid_keys:
        raise HTTPException(
            status_code=403, 
            detail=f"Invalid API key. Valid keys count: {len(valid_keys)}"
        )
    return api_key

# 修改背景任务处理函数
async def process_snapshot_async(snapshot: RuntimeSnapshot):
    """异步处理快照"""
    try:
        # 检查分析是否启用
        if not settings.snapshot_analysis_enabled:
            logger.info(f"AI analysis disabled for snapshot from {snapshot.robot_id}")
        
        # 检查存储限制
        if len(snapshot_store) >= settings.snapshot_max_history:
            # 清理旧快照
            snapshot_store.pop(0)
            logger.warning(f"Snapshot store reached limit, removed oldest snapshot")
        
        # 存储快照
        snapshot_store.append(snapshot)
        logger.info(f"Stored snapshot for robot {snapshot.robot_id}")
        
        # 转换为RAG上下文
        context = runtime_service.snapshot_to_context(snapshot)
        
        # 如果分析启用，执行AI分析
        analysis = None
        if settings.snapshot_analysis_enabled:
            try:
                analysis = await ai_processor.analyze_snapshot(snapshot)
                logger.info(f"AI analysis completed for {snapshot.robot_id}")
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
        
        # 生成审计日志
        audit_log = runtime_service.to_audit_log(snapshot)
        
        return {
            "stored": True,
            "context_generated": True,
            "ai_analysis_performed": bool(analysis),
            "audit_log": audit_log
        }
        
    except Exception as e:
        logger.error(f"Error processing snapshot: {e}")
        return {"error": str(e)}
    
@router.post("/snapshot", 
          summary="接收运行时快照",
          description="从Edge Adapter接收不可变运行时快照",
          response_model=Dict[str, str])
async def ingest_runtime_snapshot(
    snapshot: RuntimeSnapshot,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    接收运行时快照
    
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
        
        # 立即返回响应
        return {
            "status": "accepted",
            "message": "Snapshot received and queued for processing",
            "snapshot_id": f"{snapshot.robot_id}_{snapshot.timestamp}",
            "timestamp": datetime.utcnow().isoformat(),
            "robot_id": snapshot.robot_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/{robot_id}",
         summary="获取历史快照",
         description="获取机器人历史快照（用于回放和审计）",
         response_model=List[RuntimeSnapshot])
async def get_snapshot_history(
    robot_id: str,
    limit: Optional[int] = 10,
    api_key: str = Depends(verify_api_key)
):
    """获取机器人历史快照"""
    history = [s for s in snapshot_store if s.robot_id == robot_id]
    
    # 按时间戳排序（最新的在前）
    history.sort(key=lambda x: x.timestamp, reverse=True)
    
    return history[:limit] if limit else history


@router.get("/{robot_id}/latest",
         summary="获取最新快照",
         description="获取机器人最新快照",
         response_model=RuntimeSnapshot)
async def get_latest_snapshot(
    robot_id: str,
    api_key: str = Depends(verify_api_key)
):
    """获取机器人最新快照"""
    robot_snapshots = [s for s in snapshot_store if s.robot_id == robot_id]
    if not robot_snapshots:
        raise HTTPException(status_code=404, detail="No snapshots found")
    
    # 按时间戳排序，取最新的
    latest = max(robot_snapshots, key=lambda x: x.timestamp)
    return latest


# 在批量接收端点添加限制检查
@router.post("/batch",
         summary="批量接收快照",
         description="批量接收多个运行时快照",
         response_model=Dict[str, Any])
async def ingest_batch_snapshots(
    snapshots: List[RuntimeSnapshot],
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    批量接收快照
    
    - **snapshots**: 快照列表
    - **api_key**: Edge Adapter身份验证
    """
    try:
        # 检查批量大小限制
        if len(snapshots) > settings.snapshot_max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Batch size {len(snapshots)} exceeds maximum {settings.snapshot_max_batch_size}"
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
        
        return {
            "status": "accepted",
            "message": f"Batch processing started: {len(valid_snapshots)} valid, {len(invalid_snapshots)} invalid",
            "valid_count": len(valid_snapshots),
            "invalid_count": len(invalid_snapshots),
            "invalid_snapshots": invalid_snapshots,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats",
         summary="快照统计",
         description="获取快照摄入统计信息",
         response_model=Dict[str, Any])
async def get_snapshot_stats(
    api_key: str = Depends(verify_api_key)
):
    """获取快照统计信息"""
    try:
        robots = {}
        error_counts = {}
        source_counts = {}
        
        for snapshot in snapshot_store:
            # 机器人统计
            if snapshot.robot_id not in robots:
                robots[snapshot.robot_id] = 0
            robots[snapshot.robot_id] += 1
            
            # 错误统计
            for error in snapshot.errors:
                if error not in error_counts:
                    error_counts[error] = 0
                error_counts[error] += 1
            
            # 来源统计
            source = snapshot.source.value
            if source not in source_counts:
                source_counts[source] = 0
            source_counts[source] += 1
        
        # 计算错误率
        total_snapshots = len(snapshot_store)
        snapshots_with_errors = sum(1 for s in snapshot_store if s.errors)
        error_rate = snapshots_with_errors / total_snapshots if total_snapshots > 0 else 0
        
        return {
            "status": "success",
            "stats": {
                "total_snapshots": total_snapshots,
                "unique_robots": len(robots),
                "snapshots_with_errors": snapshots_with_errors,
                "error_rate": error_rate,
                "top_robots": dict(sorted(robots.items(), key=lambda x: x[1], reverse=True)[:5]),
                "common_errors": dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "sources": source_counts
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{robot_id}/replay",
         summary="快照回放",
         description="回放机器人的历史快照",
         response_model=Dict[str, Any])
async def replay_snapshots(
    robot_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    speed: float = 1.0,
    api_key: str = Depends(verify_api_key)
):
    """
    回放历史快照
    
    - **robot_id**: 机器人ID
    - **start_time**: 开始时间（ISO格式）
    - **end_time**: 结束时间（ISO格式）
    - **speed**: 回放速度倍数
    """
    try:
        # 筛选机器人快照
        robot_snapshots = [s for s in snapshot_store if s.robot_id == robot_id]
        
        if not robot_snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found for this robot")
        
        # 按时间过滤
        if start_time:
            robot_snapshots = [s for s in robot_snapshots if s.timestamp >= start_time]
        if end_time:
            robot_snapshots = [s for s in robot_snapshots if s.timestamp <= end_time]
        
        # 按时间戳排序
        robot_snapshots.sort(key=lambda x: x.timestamp)
        
        if not robot_snapshots:
            raise HTTPException(
                status_code=404, 
                detail="No snapshots found in the specified time range"
            )
        
        # 生成回放序列
        replay_data = []
        for snapshot in robot_snapshots:
            replay_data.append({
                "timestamp": snapshot.timestamp,
                "context": runtime_service.snapshot_to_context(snapshot),
                "has_errors": len(snapshot.errors) > 0,
                "error_count": len(snapshot.errors),
                "joint_count": len(snapshot.joint_states)
            })
        
        return {
            "status": "success",
            "robot_id": robot_id,
            "replay_config": {
                "speed": speed,
                "snapshot_count": len(replay_data),
                "time_range": {
                    "start": robot_snapshots[0].timestamp,
                    "end": robot_snapshots[-1].timestamp
                }
            },
            "replay_data": replay_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replaying snapshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# 在健康检查端点添加配置信息
@router.get("/health",
         summary="健康检查",
         description="快照摄入服务健康检查")
async def health_check():
    """健康检查"""
    config_summary = {
        "snapshot_count": len(snapshot_store),
        "unique_robots": len(set(s.robot_id for s in snapshot_store)),
        "last_snapshot": snapshot_store[-1].timestamp if snapshot_store else None,
        "analysis_enabled": settings.snapshot_analysis_enabled,
        "max_history": settings.snapshot_max_history,
        "storage_type": settings.snapshot_storage_type
    }
    
    return {
        "status": "healthy",
        "service": "snapshot-ingestion-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "config": config_summary
    }