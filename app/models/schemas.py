from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# ROS Topic 相关模型
class ROSTopic(BaseModel):
    topic: str = Field(..., description="ROS Topic名称")
    type: str = Field(..., description="消息类型")
    description: Optional[str] = Field("", description="Topic描述")
    rate: Optional[str] = Field("unknown", description="发布频率")
    publisher: Optional[str] = Field(None, description="发布者节点")
    subscribers: Optional[List[str]] = Field(None, description="订阅者节点列表")

class ROSTopicsIngestRequest(BaseModel):
    topics: List[ROSTopic]

# URDF 相关模型
class URDFIngestRequest(BaseModel):
    robot_name: str = Field(..., description="机器人名称")
    urdf_content: str = Field(..., description="URDF XML内容")

# Safety/Operation 相关模型
class SafetyOperation(BaseModel):
    title: str = Field(..., description="操作标题")
    content: str = Field(..., description="操作内容")
    category: str = Field("safety", description="类别")
    procedure_steps: Optional[List[str]] = Field(None, description="步骤列表")

class SafetyOperationIngestRequest(BaseModel):
    operations: List[SafetyOperation]

# 查询相关模型
class QueryRequest(BaseModel):
    query: str = Field(..., description="查询问题")
    top_k: int = Field(5, description="返回结果数量")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="回答内容")
    sources: List[Dict[str, Any]] = Field([], description="来源信息")
    confidence: float = Field(0.0, description="置信度")
