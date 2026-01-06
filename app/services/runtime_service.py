from typing import Dict, Any, List
import json
from datetime import datetime
import logging

from app.models.runtime_snapshot import RuntimeSnapshot
from app.core.config import settings

logger = logging.getLogger(__name__)


class RuntimeService:
    """运行时快照服务层"""
    
    def __init__(self, rag_service=None):
        self.rag_service = rag_service
        self.max_history = settings.snapshot_max_history
        
    def snapshot_to_context(self, snapshot: RuntimeSnapshot) -> str:
        """
        将快照转换为RAG上下文文本
        遵循原则：快照是事实，不embedding，只做格式化
        """
        # 简化的上下文格式，便于LLM处理
        context_lines = [
            f"时间戳: {snapshot.timestamp}",
            f"机器人ID: {snapshot.robot_id}",
            f"型号: {snapshot.model}",
            f"固件版本: {snapshot.firmware}",
            f"数据来源: {snapshot.source.value}",
        ]
        
        if snapshot.errors:
            context_lines.append(f"错误代码: {', '.join(snapshot.errors)}")
        else:
            context_lines.append("错误代码: 无")
            
        if snapshot.joint_states:
            joints_str = ", ".join([f"{k}: {v}" for k, v in snapshot.joint_states.items()])
            context_lines.append(f"关节状态: {joints_str}")
            
        if snapshot.active_topics:
            context_lines.append(f"活跃话题: {', '.join(snapshot.active_topics[:5])}")  # 限制长度
            
        if snapshot.metadata:
            context_lines.append(f"元数据: {json.dumps(snapshot.metadata)[:100]}...")  # 限制长度
            
        return "\n".join(context_lines)
    
    def validate_snapshot(self, snapshot: RuntimeSnapshot) -> bool:
        """验证快照数据完整性"""
        try:
            # 验证必要字段
            if not snapshot.robot_id or not snapshot.timestamp:
                logger.warning(f"Missing required fields: robot_id={snapshot.robot_id}, timestamp={snapshot.timestamp}")
                return False
            
            # 验证时间戳格式
            try:
                datetime.fromisoformat(snapshot.timestamp.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid timestamp format: {snapshot.timestamp}")
                return False
            
            # 验证关节状态值
            for joint_name, value in snapshot.joint_states.items():
                if not isinstance(value, (int, float)):
                    logger.warning(f"Invalid joint state value for {joint_name}: {value}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def to_audit_log(self, snapshot: RuntimeSnapshot) -> Dict[str, Any]:
        """转换为审计日志格式"""
        return {
            "id": f"snapshot_{snapshot.robot_id}_{snapshot.timestamp}",
            "robot_id": snapshot.robot_id,
            "timestamp": snapshot.timestamp,
            "model": snapshot.model,
            "firmware": snapshot.firmware,
            "has_errors": len(snapshot.errors) > 0,
            "error_count": len(snapshot.errors),
            "errors": snapshot.errors,
            "joint_count": len(snapshot.joint_states),
            "topic_count": len(snapshot.active_topics),
            "source": snapshot.source.value,
            "metadata_keys": list(snapshot.metadata.keys()) if snapshot.metadata else []
        }