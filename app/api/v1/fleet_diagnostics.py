"""
车队诊断API端点 - 最终修复版本
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.fleet_diagnostic_service import FleetDiagnosticService
from app.services.diagnostic_service import DiagnosticService
from app.models.fleet import (
    FleetState, FleetDiagnosisRequest, FleetDiagnosisResponse, RobotState
)
from app.api.dependencies import get_fleet_diagnostic_service

router = APIRouter(tags=["Fleet Diagnostics"])


class FleetAnalysisRequest(BaseModel):
    """车队分析请求"""
    fleet_state: FleetState = Field(..., description="车队状态")
    focus_errors: Optional[List[str]] = Field(None, description="重点关注错误代码列表")
    analysis_depth: str = Field("standard", description="分析深度：quick/standard/deep")
    include_comparison: bool = Field(True, description="是否包含型号对比")


class ErrorAnalysisRequest(BaseModel):
    """错误分析请求"""
    error_code: str = Field(..., description="错误代码")
    fleet_state: FleetState = Field(..., description="车队状态")
    include_trend_analysis: bool = Field(True, description="是否包含趋势分析")


class ComparisonRequest(BaseModel):
    """对比分析请求"""
    fleet_state: FleetState = Field(..., description="车队状态")
    comparison_type: str = Field("model", description="对比类型：model/firmware/location")
    metric: str = Field("error_rate", description="对比指标：error_rate/reliability/avg_errors")


@router.post("/analyze-fleet", response_model=FleetDiagnosisResponse)
async def analyze_fleet(
    request: FleetAnalysisRequest,
    fleet_diagnostic_service: FleetDiagnosticService = Depends(get_fleet_diagnostic_service)
) -> FleetDiagnosisResponse:
    """
    分析整个车队，识别系统性和单机问题
    """
    try:
        # 构建诊断请求
        diagnosis_request = FleetDiagnosisRequest(
            fleet_state=request.fleet_state,
            analysis_type=request.analysis_depth,
            include_detailed_analysis=True
        )
        
        # 执行车队诊断
        response = await fleet_diagnostic_service.diagnose_fleet(diagnosis_request)
        
        # 如果指定了关注错误，添加额外分析
        if request.focus_errors:
            focus_analyses = {}
            for error_code in request.focus_errors[:3]:  # 限制为前3个
                analysis = await fleet_diagnostic_service.analyze_specific_error(
                    request.fleet_state, error_code
                )
                focus_analyses[error_code] = analysis
            
            # 转换为字典并添加额外字段
            response_dict = response.dict()
            response_dict["focus_analyses"] = focus_analyses
            return FleetDiagnosisResponse(**response_dict)
        
        return response
        
    except ZeroDivisionError:
        raise HTTPException(
            status_code=400, 
            detail="Cannot analyze empty fleet. Please provide at least one robot."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing fleet: {str(e)}")


@router.post("/analyze-error")
async def analyze_specific_error(
    request: ErrorAnalysisRequest,
    fleet_diagnostic_service: FleetDiagnosticService = Depends(get_fleet_diagnostic_service)
) -> Dict[str, Any]:
    """
    分析特定错误在车队中的分布情况
    """
    try:
        analysis = await fleet_diagnostic_service.analyze_specific_error(
            request.fleet_state, request.error_code
        )
        
        return {
            "status": "success",
            "analysis": analysis,
            "error_code": request.error_code
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing error: {str(e)}")


@router.post("/compare")
async def compare_analysis(
    request: ComparisonRequest,
    fleet_diagnostic_service: FleetDiagnosticService = Depends(get_fleet_diagnostic_service)
) -> Dict[str, Any]:
    """
    进行对比分析（型号/固件/位置）
    """
    try:
        # 检查车队是否为空
        if not request.fleet_state.robots:
            return {
                "status": "warning",
                "message": "No robots available for comparison",
                "comparison_type": request.comparison_type,
                "metric": request.metric,
                "result": {}
            }
        
        # 获取分析器
        fleet_analyzer = fleet_diagnostic_service.fleet_analyzer
        
        if request.comparison_type == "model":
            result = fleet_analyzer.compare_model_performance(request.fleet_state)
        elif request.comparison_type == "firmware":
            result = fleet_analyzer.analyze_firmware_impact(request.fleet_state)
        elif request.comparison_type == "location":
            # 需要位置信息
            robots_with_location = [r for r in request.fleet_state.robots if r.location]
            if not robots_with_location:
                return {
                    "status": "warning",
                    "message": "No location information available for comparison",
                    "comparison_type": request.comparison_type,
                    "metric": request.metric,
                    "result": {}
                }
            
            # 创建包含位置信息的车队状态
            fleet_with_location = FleetState(robots=robots_with_location)
            result = fleet_analyzer.identify_correlation(
                fleet_with_location, "location", "error_code"
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported comparison type: {request.comparison_type}")
        
        return {
            "status": "success",
            "comparison_type": request.comparison_type,
            "metric": request.metric,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing comparison: {str(e)}")


@router.post("/generate-report")
async def generate_diagnostic_report(
    request: FleetAnalysisRequest,
    fleet_diagnostic_service: FleetDiagnosticService = Depends(get_fleet_diagnostic_service)
) -> Dict[str, Any]:
    """
    生成详细的诊断报告
    """
    try:
        # 检查车队是否为空
        if not request.fleet_state.robots:
            return {
                "status": "warning",
                "message": "Cannot generate report for empty fleet",
                "report": {
                    "report_id": f"FDR-{int(datetime.now().timestamp())}",
                    "generated_at": datetime.now().isoformat(),
                    "fleet_summary": {
                        "total_robots": 0,
                        "models": [],
                        "firmware_versions": [],
                        "error_rate": 0
                    },
                    "executive_summary": {
                        "status": "ℹ️ 无数据",
                        "key_findings": ["车队为空，无法生成诊断报告"]
                    },
                    "detailed_analysis": "当前车队为空，请添加设备后重新生成报告。",
                    "recommendations": ["添加设备到车队"],
                    "priority_actions": []
                },
                "download_url": None
            }
        
        # 执行完整诊断
        diagnosis_request = FleetDiagnosisRequest(
            fleet_state=request.fleet_state,
            analysis_type="deep",
            include_detailed_analysis=True
        )
        
        diagnosis = await fleet_diagnostic_service.diagnose_fleet(diagnosis_request)
        
        # 提取优先行动项
        priority_actions = extract_priority_actions(diagnosis)
        
        # 生成报告
        report = {
            "report_id": f"FDR-{int(datetime.now().timestamp())}",
            "generated_at": datetime.now().isoformat(),
            "fleet_summary": {
                "total_robots": len(request.fleet_state.robots),
                "models": list(set(r.model for r in request.fleet_state.robots)),
                "firmware_versions": list(set(r.firmware for r in request.fleet_state.robots)),
                "error_rate": diagnosis.summary.get("error_rate", 0)
            },
            "executive_summary": {
                "status": "🟢 良好" if diagnosis.summary.get("error_rate", 0) < 0.2 else 
                        "🟡 需关注" if diagnosis.summary.get("error_rate", 0) < 0.5 else 
                        "🔴 紧急",
                "key_findings": [
                    f"{diagnosis.summary.get('systemic_issue_count', 0)}个系统性问题",
                    f"{diagnosis.summary.get('single_unit_issue_count', 0)}个单机问题",
                    f"整体异常率: {diagnosis.summary.get('error_rate', 0):.1%}"
                ]
            },
            "detailed_analysis": diagnosis.detailed_analysis,
            "recommendations": diagnosis.recommendations,
            "priority_actions": priority_actions
        }
        
        return {
            "status": "success",
            "report": report,
            "download_url": f"/api/v1/fleet-diagnostics/reports/{report['report_id']}.pdf"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/health")
async def fleet_diagnostic_health(
    fleet_diagnostic_service: FleetDiagnosticService = Depends(get_fleet_diagnostic_service)
) -> Dict[str, Any]:
    """
    车队诊断服务健康检查
    """
    try:
        # 简单测试服务是否可用
        test_fleet = FleetState(robots=[
            RobotState(
                robot_id="test",
                model="A1",
                firmware="v1.0",
                errors=[],
                last_seen=datetime.now()
            )
        ])
        
        # 尝试调用一个简单的方法
        _ = fleet_diagnostic_service.fleet_analyzer
        
        return {
            "status": "healthy",
            "service": "fleet_diagnostic_service",
            "capabilities": [
                "fleet_analysis",
                "systemic_issue_detection", 
                "single_unit_issue_detection",
                "trend_analysis",
                "comparative_analysis"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "fleet_diagnostic_service",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def extract_priority_actions(diagnosis: FleetDiagnosisResponse) -> List[Dict[str, Any]]:
    """从诊断结果中提取优先行动项"""
    priority_actions = []
    
    # 添加系统性问题行动项
    for issue in diagnosis.systemic_issues:
        priority_actions.append({
            "type": "systemic",
            "priority": "high" if issue.get("severity") == "high" else "medium",
            "description": f"处理{issue['error_code']}系统性问题",
            "affected_robots": issue.get("affected_robots", 0),
            "estimated_effort": "2-4小时",
            "responsible_team": "软件工程"
        })
    
    # 添加单机问题行动项（只取最紧急的3个）
    for issue in diagnosis.single_unit_issues[:3]:
        if issue.get("severity") == "high":
            priority_actions.append({
                "type": "single_unit",
                "priority": "high",
                "description": f"紧急检修{issue['robot_id']}的{issue['error_code']}错误",
                "robot_id": issue["robot_id"],
                "estimated_effort": "1-2小时",
                "responsible_team": "现场支持"
            })
    
    # 按优先级排序
    priority_order = {"high": 3, "medium": 2, "low": 1}
    priority_actions.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
    
    return priority_actions