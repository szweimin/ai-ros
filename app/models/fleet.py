"""
车队状态和诊断相关Schema
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class RobotModel(str, Enum):
    """机器人型号枚举"""
    A1 = "A1"
    B2 = "B2"
    C3 = "C3"


class ErrorSeverity(str, Enum):
    """错误严重程度枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RobotState(BaseModel):
    """机器人状态"""
    robot_id: str = Field(..., description="机器人ID")
    model: str = Field(..., description="机器人型号")
    firmware: str = Field(..., description="固件版本")
    errors: List[str] = Field(default_factory=list, description="错误代码列表")
    last_seen: Optional[datetime] = Field(None, description="最后在线时间")
    location: Optional[str] = Field(None, description="当前位置")
    battery_level: Optional[float] = Field(None, description="电池电量")
    active_topics: List[str] = Field(default_factory=list, description="活跃话题")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="运行时参数")
    
    def has_error(self, error_code: str) -> bool:
        """检查是否包含指定错误"""
        return error_code in self.errors


class FleetState(BaseModel):
    """车队状态"""
    robots: List[RobotState] = Field(..., description="机器人列表")
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_robot_count_by_model(self) -> Dict[str, int]:
        """按型号统计机器人数量"""
        counter = {}
        for robot in self.robots:
            counter[robot.model] = counter.get(robot.model, 0) + 1
        return counter
    
    def get_robots_with_error(self, error_code: str) -> List[RobotState]:
        """获取指定错误码的机器人列表"""
        return [robot for robot in self.robots if error_code in robot.errors]
    
    def get_robots_by_model(self, model: str) -> List[RobotState]:
        """获取指定型号的机器人列表"""
        return [robot for robot in self.robots if robot.model == model]
    
    def get_robots_by_firmware(self, firmware: str) -> List[RobotState]:
        """获取指定固件版本的机器人列表"""
        return [robot for robot in self.robots if robot.firmware == firmware]


class FleetDiagnosisRequest(BaseModel):
    """车队诊断请求"""
    fleet_state: FleetState = Field(..., description="车队状态")
    focus_error: Optional[str] = Field(None, description="重点关注错误代码")
    analysis_type: str = Field("systemic", description="分析类型：systemic/single-unit/trend")
    include_detailed_analysis: bool = Field(True, description="是否包含详细分析")


class FleetDiagnosisResponse(BaseModel):
    """车队诊断响应"""
    status: str = Field(..., description="诊断状态")
    analysis_type: str = Field(..., description="分析类型")
    summary: Dict[str, Any] = Field(..., description="诊断摘要")
    systemic_issues: List[Dict[str, Any]] = Field(default_factory=list, description="系统性问题列表")
    single_unit_issues: List[Dict[str, Any]] = Field(default_factory=list, description="单机问题列表")
    recommendations: List[str] = Field(default_factory=list, description="建议措施")
    detailed_analysis: Optional[str] = Field(None, description="详细分析")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorStatistics(BaseModel):
    """错误统计"""
    error_code: str = Field(..., description="错误代码")
    total_occurrences: int = Field(..., description="总发生次数")
    affected_robots: int = Field(..., description="受影响机器人数量")
    models_affected: List[str] = Field(..., description="受影响的型号")
    firmware_distribution: Dict[str, int] = Field(..., description="固件版本分布")
    occurrence_rate: float = Field(..., description="发生率")
    severity: str = Field(..., description="严重程度")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_code": self.error_code,
            "total_occurrences": self.total_occurrences,
            "affected_robots": self.affected_robots,
            "models_affected": self.models_affected,
            "firmware_distribution": self.firmware_distribution,
            "occurrence_rate": self.occurrence_rate,
            "severity": self.severity
        }