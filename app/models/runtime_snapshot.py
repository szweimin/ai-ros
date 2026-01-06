from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class SnapshotSource(str, Enum):
    ROS2 = "ros2"
    PLC = "plc"
    CONTROLLER = "controller"
    SIMULATOR = "simulator"


class RuntimeSnapshot(BaseModel):
    """运行时不可变快照 - 事实数据"""
    robot_id: str = Field(..., description="机器人唯一标识")
    model: str = Field(..., description="机器人型号")
    firmware: str = Field(..., description="固件版本")
    timestamp: str = Field(..., description="ISO 8601时间戳")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    joint_states: Dict[str, float] = Field(default_factory=dict, description="关节状态")
    active_topics: List[str] = Field(default_factory=list, description="活跃话题")
    
    # 可选字段
    source: SnapshotSource = Field(default=SnapshotSource.ROS2, description="数据来源")
    metadata: Dict[str, str] = Field(default_factory=dict, description="元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "robot_id": "agv_01",
                "model": "A1",
                "firmware": "v2.1",
                "timestamp": "2026-01-05T10:12:00Z",
                "errors": ["E201"],
                "joint_states": {"wheel_left": 0.0, "wheel_right": 0.0},
                "active_topics": ["/scan", "/odom"],
                "source": "ros2"
            }
        }