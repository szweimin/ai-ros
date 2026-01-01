"""
诊断服务 - 基于故障树进行工程诊断
"""
from typing import Dict, List, Optional, Any
import asyncio
from ..diagnostics.fault_tree import (
    get_fault_tree, 
    get_all_fault_trees,
    get_related_fault_trees,
    format_fault_tree_for_prompt,
    FaultTree
)
from ..models.schemas import RuntimeState

class DiagnosticService:
    def __init__(self):
        self.fault_trees = get_all_fault_trees()
    
    async def diagnose_single_error(self, error_code: str, 
                                   runtime_state: Optional[RuntimeState] = None) -> Dict[str, Any]:
        """
        诊断单个错误代码
        
        Args:
            error_code: 错误代码
            runtime_state: 运行时状态（用于增强诊断）
            
        Returns:
            诊断结果
        """
        tree = get_fault_tree(error_code)
        
        if not tree:
            return {
                "error_code": error_code,
                "status": "unknown",
                "message": f"No diagnostic tree available for error {error_code}",
                "suggested_action": "Check system logs and documentation"
            }
        
        # 基础诊断信息
        result = {
            "error_code": error_code,
            "status": "diagnosed",
            "description": tree.description,
            "category": tree.category,
            "severity": tree.severity,
            "possible_causes": [
                {
                    "id": cause.id,
                    "description": cause.description,
                    "check": cause.check,
                    "probability": cause.probability,
                    "adjusted_probability": cause.probability  # 初始值，后面会根据运行时状态调整
                }
                for cause in tree.causes
            ],
            "recovery_steps": tree.recovery_steps or [],
            "formatted_for_prompt": format_fault_tree_for_prompt(tree)
        }
        
        # 如果提供了运行时状态，调整概率
        if runtime_state:
            result = self._adjust_probabilities_with_runtime(result, runtime_state)
        
        return result
    
    def _adjust_probabilities_with_runtime(self, diagnosis: Dict[str, Any], 
                                         runtime_state: RuntimeState) -> Dict[str, Any]:
        """
        根据运行时状态调整故障原因概率
        
        Args:
            diagnosis: 诊断结果
            runtime_state: 运行时状态
            
        Returns:
            调整后的诊断结果
        """
        adjusted_causes = []
        
        for cause in diagnosis["possible_causes"]:
            adjusted_probability = cause["probability"]
            
            # 根据活跃话题调整概率
            if runtime_state.active_topics:
                # 如果错误与激光安全相关，且提到了激光话题
                if "laser" in cause["description"].lower() and any("laser" in topic.lower() for topic in runtime_state.active_topics):
                    adjusted_probability *= 1.3  # 增加30%
                
                # 如果错误与电池相关，且提到了电池话题
                if "battery" in cause["description"].lower() and any("battery" in topic.lower() for topic in runtime_state.active_topics):
                    adjusted_probability *= 1.2  # 增加20%
            
            # 根据参数调整概率
            if runtime_state.parameters:
                params = runtime_state.parameters
                
                # 如果提到了紧急停止且参数中有相关标记
                if "emergency" in cause["description"].lower() and any("emergency" in key.lower() or "stop" in key.lower() for key in params.keys()):
                    adjusted_probability *= 1.4  # 增加40%
                
                # 如果提到了关节限制且参数中有位置信息
                if "joint" in cause["description"].lower() and any("joint" in key.lower() or "position" in key.lower() for key in params.keys()):
                    adjusted_probability *= 1.3  # 增加30%
            
            # 确保概率在合理范围内
            adjusted_probability = min(max(adjusted_probability, 0.1), 0.9)
            
            adjusted_causes.append({
                **cause,
                "adjusted_probability": adjusted_probability
            })
        
        # 按调整后的概率排序
        adjusted_causes.sort(key=lambda x: x["adjusted_probability"], reverse=True)
        
        diagnosis["possible_causes"] = adjusted_causes
        diagnosis["runtime_enhanced"] = True
        
        return diagnosis
    
    async def diagnose_multiple_errors(self, error_codes: List[str], 
                                      runtime_state: Optional[RuntimeState] = None) -> Dict[str, Any]:
        """
        诊断多个错误代码
        
        Args:
            error_codes: 错误代码列表
            runtime_state: 运行时状态
            
        Returns:
            综合诊断结果
        """
        if not error_codes:
            return {
                "status": "no_errors",
                "message": "No error codes provided for diagnosis"
            }
        
        # 诊断每个错误
        diagnoses = []
        for error_code in error_codes:
            diagnosis = await self.diagnose_single_error(error_code, runtime_state)
            diagnoses.append(diagnosis)
        
        # 确定主要错误（按严重程度）
        severity_order = {"high": 3, "medium": 2, "low": 1}
        primary_diagnosis = max(diagnoses, key=lambda d: severity_order.get(d.get("severity", "low"), 0))
        
        # 综合所有诊断信息
        combined_causes = []
        for diagnosis in diagnoses:
            if "possible_causes" in diagnosis:
                combined_causes.extend(diagnosis["possible_causes"])
        
        # 去重并合并概率
        unique_causes = {}
        for cause in combined_causes:
            cause_id = cause["id"]
            if cause_id not in unique_causes:
                unique_causes[cause_id] = cause
            else:
                # 如果已经存在，取较高的概率
                unique_causes[cause_id]["adjusted_probability"] = max(
                    unique_causes[cause_id]["adjusted_probability"],
                    cause["adjusted_probability"]
                )
        
        # 按概率排序
        sorted_causes = sorted(unique_causes.values(), 
                              key=lambda x: x["adjusted_probability"], 
                              reverse=True)
        
        return {
            "status": "diagnosed",
            "error_count": len(error_codes),
            "primary_error": primary_diagnosis["error_code"],
            "primary_severity": primary_diagnosis["severity"],
            "combined_causes": sorted_causes[:5],  # 只取前5个最可能的原因
            "individual_diagnoses": diagnoses,
            "summary": self._generate_diagnosis_summary(diagnoses, runtime_state)
        }
    
    def _generate_diagnosis_summary(self, diagnoses: List[Dict[str, Any]], 
                                   runtime_state: Optional[RuntimeState]) -> str:
        """生成诊断摘要"""
        if not diagnoses:
            return "No diagnoses available."
        
        error_codes = [d["error_code"] for d in diagnoses]
        
        summary_parts = [
            f"Diagnosed {len(error_codes)} error(s): {', '.join(error_codes)}"
        ]
        
        # 如果有运行时状态
        if runtime_state:
            summary_parts.append(f"Robot: {runtime_state.robot_id}")
            
            if runtime_state.active_topics:
                summary_parts.append(f"Active topics: {', '.join(runtime_state.active_topics[:3])}")
                if len(runtime_state.active_topics) > 3:
                    summary_parts[-1] += f" and {len(runtime_state.active_topics) - 3} more"
        
        # 主要建议
        all_causes = []
        for diagnosis in diagnoses:
            if diagnosis.get("possible_causes"):
                all_causes.extend(diagnosis["possible_causes"][:2])  # 每个诊断取前2个原因
        
        if all_causes:
            summary_parts.append("Most likely causes:")
            for i, cause in enumerate(sorted(all_causes, key=lambda x: x["adjusted_probability"], reverse=True)[:3], 1):
                summary_parts.append(f"  {i}. {cause['description']} ({cause['adjusted_probability']:.0%})")
        
        return "\n".join(summary_parts)
    
    def get_diagnostic_context_for_prompt(self, diagnosis: Dict[str, Any]) -> str:
        """
        为提示词生成诊断上下文
        
        Args:
            diagnosis: 诊断结果
            
        Returns:
            格式化的诊断上下文
        """
        if diagnosis.get("status") != "diagnosed":
            return f"Diagnostic info: {diagnosis.get('message', 'No diagnosis available')}"
        
        parts = [
            f"📋 DIAGNOSTIC TREE ANALYSIS",
            f"Error Code: {diagnosis['error_code']}",
            f"Description: {diagnosis['description']}",
            f"Severity: {diagnosis['severity'].upper()} | Category: {diagnosis['category']}",
            "",
            "🔍 MOST LIKELY CAUSES (sorted by probability):"
        ]
        
        for i, cause in enumerate(diagnosis.get("possible_causes", [])[:3], 1):
            prob = cause.get("adjusted_probability", cause.get("probability", 0))
            parts.append(f"  {i}. {cause['description']}")
            parts.append(f"     ✅ Check: {cause['check']}")
            parts.append(f"     📊 Probability: {prob:.0%}")
            parts.append("")
        
        if diagnosis.get("recovery_steps"):
            parts.append("🚀 RECOMMENDED RECOVERY STEPS:")
            for i, step in enumerate(diagnosis["recovery_steps"][:3], 1):
                parts.append(f"  {i}. {step}")
        
        if diagnosis.get("runtime_enhanced"):
            parts.append("")
            parts.append("ℹ️  Diagnosis enhanced with runtime state information")
        
        return "\n".join(parts)
    
    async def generate_diagnosis_plan(self, error_codes: List[str], 
                                     runtime_state: RuntimeState) -> Dict[str, Any]:
        """
        生成详细的诊断计划
        
        Args:
            error_codes: 错误代码列表
            runtime_state: 运行时状态
            
        Returns:
            诊断计划
        """
        # 获取诊断结果
        diagnosis = await self.diagnose_multiple_errors(error_codes, runtime_state)
        
        if diagnosis["status"] != "diagnosed":
            return diagnosis
        
        # 生成检查步骤
        check_steps = []
        for cause in diagnosis.get("combined_causes", [])[:5]:
            check_steps.append({
                "id": cause["id"],
                "description": cause["description"],
                "action": cause["check"],
                "priority": "HIGH" if cause["adjusted_probability"] > 0.6 else "MEDIUM",
                "estimated_time": "5-10 minutes"
            })
        
        # 生成恢复计划
        recovery_plan = []
        for diag in diagnosis.get("individual_diagnoses", []):
            if diag.get("recovery_steps"):
                recovery_plan.extend(diag["recovery_steps"])
        
        # 去重恢复步骤
        unique_recovery_steps = list(dict.fromkeys(recovery_plan))
        
        return {
            "status": "plan_generated",
            "diagnosis_summary": diagnosis["summary"],
            "check_steps": check_steps,
            "recovery_plan": unique_recovery_steps[:5],
            "safety_notes": self._generate_safety_notes(diagnosis),
            "estimated_resolution_time": self._estimate_resolution_time(diagnosis)
        }
    
    def _generate_safety_notes(self, diagnosis: Dict[str, Any]) -> List[str]:
        """生成安全注意事项"""
        safety_notes = []
        
        if diagnosis.get("primary_severity") == "high":
            safety_notes.append("⚠️  HIGH SEVERITY ERROR: Exercise extreme caution")
            safety_notes.append("Do not attempt to bypass safety systems")
            safety_notes.append("Follow lockout-tagout procedures if working on electrical systems")
        
        if any("safety" in str(d.get("category", "")).lower() for d in diagnosis.get("individual_diagnoses", [])):
            safety_notes.append("🔒 Safety system intervention required")
            safety_notes.append("Verify all safety circuits before resetting")
        
        if not safety_notes:
            safety_notes.append("Follow standard safety procedures")
        
        return safety_notes
    
    def _estimate_resolution_time(self, diagnosis: Dict[str, Any]) -> str:
        """估计解决时间"""
        error_count = diagnosis.get("error_count", 1)
        severity = diagnosis.get("primary_severity", "medium")
        
        if severity == "high":
            base_time = 30  # 分钟
        elif severity == "medium":
            base_time = 15
        else:
            base_time = 5
        
        total_time = base_time * error_count
        
        if total_time < 60:
            return f"{total_time} minutes"
        else:
            hours = total_time // 60
            minutes = total_time % 60
            return f"{hours} hour{'s' if hours > 1 else ''} {minutes} minutes"
    
    def get_available_error_codes(self) -> List[str]:
        """获取可诊断的错误代码列表"""
        return list(self.fault_trees.keys())
