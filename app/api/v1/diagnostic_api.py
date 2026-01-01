"""
诊断相关的API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.diagnostic_service import DiagnosticService
from app.services.query_service import QueryService
from app.models.schemas import RuntimeState
from app.api.dependencies import get_query_service, get_diagnostic_service

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])

class DiagnosticRequest(BaseModel):
    """诊断请求"""
    error_codes: List[str] = Field(..., description="错误代码列表")
    runtime_state: RuntimeState = Field(..., description="运行时状态")
    include_detailed_analysis: bool = Field(True, description="是否包含详细分析")

class DiagnosticResponse(BaseModel):
    """诊断响应"""
    status: str = Field(..., description="诊断状态")
    error_codes: List[str] = Field(..., description="处理的错误代码")
    diagnosis_plan: Optional[Dict[str, Any]] = Field(None, description="诊断计划")
    detailed_analysis: Optional[str] = Field(None, description="详细分析")
    robot_id: str = Field(..., description="机器人ID")
    timestamp: float = Field(..., description="时间戳")

class AvailableDiagnosesResponse(BaseModel):
    """可用诊断响应"""
    available_error_codes: List[str] = Field(..., description="可诊断的错误代码")
    total_diagnoses: int = Field(..., description="总数")
    diagnoses_info: List[Dict[str, Any]] = Field(..., description="诊断信息")

@router.post("/analyze", response_model=DiagnosticResponse)
async def analyze_errors(
    request: DiagnosticRequest,
    query_service: QueryService = Depends(get_query_service)
) -> DiagnosticResponse:
    """
    分析错误代码并生成诊断计划
    """
    try:
        result = await query_service.diagnostic_query(
            error_codes=request.error_codes,
            runtime_state=request.runtime_state
        )
        
        return DiagnosticResponse(
            status=result["status"],
            error_codes=result.get("error_codes", []),
            diagnosis_plan=result.get("diagnosis_plan"),
            detailed_analysis=result.get("detailed_analysis") if request.include_detailed_analysis else None,
            robot_id=request.runtime_state.robot_id,
            timestamp=result.get("timestamp", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing errors: {str(e)}")

@router.get("/available", response_model=AvailableDiagnosesResponse)
async def get_available_diagnoses(
    query_service: QueryService = Depends(get_query_service)
) -> AvailableDiagnosesResponse:
    """
    获取可用的诊断信息
    """
    try:
        result = await query_service.get_available_diagnoses()
        
        return AvailableDiagnosesResponse(
            available_error_codes=result["available_error_codes"],
            total_diagnoses=result["total_diagnoses"],
            diagnoses_info=result["diagnoses_info"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available diagnoses: {str(e)}")

@router.get("/tree/{error_code}")
async def get_fault_tree(
    error_code: str,
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service)
) -> Dict[str, Any]:
    """
    获取指定错误代码的故障树
    """
    try:
        tree = diagnostic_service.fault_trees.get(error_code)
        
        if not tree:
            raise HTTPException(status_code=404, detail=f"No fault tree found for error code: {error_code}")
        
        # 转换为字典
        tree_dict = {
            "error_code": tree.error_code,
            "description": tree.description,
            "category": tree.category,
            "severity": tree.severity,
            "causes": [
                {
                    "id": cause.id,
                    "description": cause.description,
                    "check": cause.check,
                    "probability": cause.probability,
                    "prerequisites": cause.prerequisites
                }
                for cause in tree.causes
            ],
            "recovery_steps": tree.recovery_steps,
            "related_codes": tree.related_codes
        }
        
        return {
            "status": "success",
            "error_code": error_code,
            "fault_tree": tree_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting fault tree: {str(e)}")

@router.post("/single-error")
async def diagnose_single_error(
    error_code: str,
    runtime_state: RuntimeState,
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service)
) -> Dict[str, Any]:
    """
    诊断单个错误代码
    """
    try:
        diagnosis = await diagnostic_service.diagnose_single_error(error_code, runtime_state)
        
        return {
            "status": "success",
            "diagnosis": diagnosis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error diagnosing error {error_code}: {str(e)}")

@router.get("/health")
async def diagnostic_health(
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service)
) -> Dict[str, Any]:
    """
    诊断服务健康检查
    """
    try:
        error_codes = diagnostic_service.get_available_error_codes()
        
        return {
            "status": "healthy",
            "service": "diagnostic_service",
            "available_error_codes": len(error_codes),
            "sample_codes": error_codes[:5] if error_codes else []
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "diagnostic_service",
            "error": str(e)
        }
