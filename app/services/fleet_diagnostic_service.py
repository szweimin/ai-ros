"""
车队诊断服务 - 扩展单设备诊断，支持多设备统计分析
"""
from typing import Dict, List, Optional, Any, Tuple
import statistics
from collections import Counter
import asyncio
from datetime import datetime, timedelta

from app.models.fleet import (
    FleetState, RobotState, FleetDiagnosisRequest, 
    FleetDiagnosisResponse, ErrorStatistics
)
from app.services.diagnostic_service import DiagnosticService
from app.services.fleet_analysis import FleetAnalyzer


class FleetDiagnosticService:
    """车队诊断服务"""
    
    def __init__(self, diagnostic_service: DiagnosticService):
        self.diagnostic_service = diagnostic_service
        self.fleet_analyzer = FleetAnalyzer()
    
    async def diagnose_fleet(self, request: FleetDiagnosisRequest) -> FleetDiagnosisResponse:
        """
        诊断整个车队，识别系统性和单机问题
        
        Args:
            request: 车队诊断请求
            
        Returns:
            车队诊断响应
        """
        fleet_state = request.fleet_state
        focus_error = request.focus_error
        
        # 检查车队是否为空
        if not fleet_state.robots:
            return FleetDiagnosisResponse(
                status="completed",
                analysis_type=request.analysis_type,
                summary={
                    "total_robots": 0,
                    "robots_with_errors": 0,
                    "error_rate": 0.0,
                    "unique_errors": 0,
                    "systemic_issue_count": 0,
                    "single_unit_issue_count": 0,
                    "focus_error_analysis": {}
                },
                systemic_issues=[],
                single_unit_issues=[],
                recommendations=["车队为空，请添加设备后重新诊断"],
                detailed_analysis="当前车队为空，无法进行诊断分析。"
            )
        
        # 基本统计
        total_robots = len(fleet_state.robots)
        robots_with_errors = sum(1 for r in fleet_state.robots if r.errors)
        
        # 安全计算错误率
        error_rate = robots_with_errors / total_robots if total_robots > 0 else 0.0
        
        # 分析错误分布
        error_analysis = self._analyze_error_distribution(fleet_state)
        
        # 识别系统性问题
        systemic_issues = self._identify_systemic_issues(fleet_state, error_analysis)
        
        # 识别单机问题
        single_unit_issues = self._identify_single_unit_issues(fleet_state, error_analysis)
        
        # 如果指定了关注错误，进行专项分析
        if focus_error:
            focus_analysis = await self._analyze_specific_error(fleet_state, focus_error)
        else:
            focus_analysis = {}
        
        # 生成建议
        recommendations = self._generate_recommendations(
            systemic_issues, single_unit_issues, fleet_state
        )
        
        # 生成详细分析
        detailed_analysis = ""
        if request.include_detailed_analysis:
            detailed_analysis = self._generate_detailed_analysis(
                fleet_state, systemic_issues, single_unit_issues, error_analysis
            )
        
        return FleetDiagnosisResponse(
            status="completed",
            analysis_type=request.analysis_type,
            summary={
                "total_robots": total_robots,
                "robots_with_errors": robots_with_errors,
                "error_rate": error_rate,
                "unique_errors": len(error_analysis),
                "systemic_issue_count": len(systemic_issues),
                "single_unit_issue_count": len(single_unit_issues),
                "focus_error_analysis": focus_analysis.get(focus_error, {}) if focus_error else {}
            },
            systemic_issues=systemic_issues,
            single_unit_issues=single_unit_issues,
            recommendations=recommendations,
            detailed_analysis=detailed_analysis
        )
    
    async def analyze_specific_error(self, fleet_state: FleetState, error_code: str) -> Dict[str, Any]:
        """
        分析特定错误在车队中的分布情况
        
        Args:
            fleet_state: 车队状态
            error_code: 错误代码
            
        Returns:
            错误分析结果
        """
        # 获取受影响机器人
        affected_robots = fleet_state.get_robots_with_error(error_code)
        total_robots = len(fleet_state.robots)
        
        if not affected_robots:
            return {
                "error_code": error_code,
                "status": "not_found",
                "message": f"错误 {error_code} 在当前车队中未出现"
            }
        
        # 统计信息
        model_counter = Counter([r.model for r in affected_robots])
        firmware_counter = Counter([r.firmware for r in affected_robots])
        
        # 计算发生率
        models_with_error = set(r.model for r in affected_robots)
        
        # 分析是否为系统性问题
        is_systemic = False
        systemic_reasons = []
        
        # 判断标准1：多台机器人出现相同错误
        if len(affected_robots) >= 2:
            is_systemic = True
            systemic_reasons.append(f"多台机器人出现相同错误 ({len(affected_robots)}台)")
        
        # 判断标准2：特定固件版本集中出现
        for firmware, count in firmware_counter.items():
            total_with_firmware = len([r for r in fleet_state.robots if r.firmware == firmware])
            # 安全计算发生率
            rate = count / total_with_firmware if total_with_firmware > 0 else 0
            
            if rate >= 0.3 and count >= 2:  # 发生率30%以上且至少2台
                is_systemic = True
                systemic_reasons.append(f"固件版本 {firmware} 中错误发生率为 {rate:.0%}")
        
        # 判断标准3：是否跨多个型号
        if len(models_with_error) > 1:
            is_systemic = True
            systemic_reasons.append(f"跨多个型号出现: {', '.join(models_with_error)}")
        
        # 获取单设备诊断信息
        individual_diagnoses = []
        for robot in affected_robots[:3]:  # 限制为前3台
            diagnosis = await self.diagnostic_service.diagnose_single_error(
                error_code, robot
            )
            individual_diagnoses.append({
                "robot_id": robot.robot_id,
                "model": robot.model,
                "firmware": robot.firmware,
                "diagnosis": diagnosis
            })
        
        return {
            "error_code": error_code,
            "is_systemic": is_systemic,
            "total_affected": len(affected_robots),
            "affected_robots": [r.robot_id for r in affected_robots],
            "model_distribution": dict(model_counter),
            "firmware_distribution": dict(firmware_counter),
            "systemic_reasons": systemic_reasons if systemic_reasons else ["可能为单机问题"],
            "individual_diagnoses": individual_diagnoses,
            "recommendations": [
                "检查固件版本间的配置差异",
                "分析现场环境条件",
                "查看错误发生时的运行日志",
                "进行批量测试验证"
            ] if is_systemic else [
                "检查单机硬件状态",
                "重新标定传感器",
                "检查设备安装位置"
            ]
        }
    
    def _analyze_error_distribution(self, fleet_state: FleetState) -> Dict[str, ErrorStatistics]:
        """分析错误分布"""
        error_stats = {}
        
        # 如果车队为空，返回空字典
        if not fleet_state.robots:
            return error_stats
        
        # 收集所有错误
        all_errors = []
        for robot in fleet_state.robots:
            for error in robot.errors:
                all_errors.append((error, robot))
        
        # 按错误代码统计
        for error_code, robot in all_errors:
            if error_code not in error_stats:
                affected = fleet_state.get_robots_with_error(error_code)
                total_same_model = len([r for r in fleet_state.robots if r.model == robot.model])
                affected_same_model = len([r for r in affected if r.model == robot.model])
                
                # 安全计算发生率
                rate = affected_same_model / total_same_model if total_same_model > 0 else 0
                
                # 固件分布
                firmware_counter = Counter([r.firmware for r in affected])
                
                # 确定严重程度（基于发生率）
                if rate >= 0.5:
                    severity = "high"
                elif rate >= 0.2:
                    severity = "medium"
                else:
                    severity = "low"
                
                error_stats[error_code] = ErrorStatistics(
                    error_code=error_code,
                    total_occurrences=len(affected),
                    affected_robots=len(affected),
                    models_affected=list(set(r.model for r in affected)),
                    firmware_distribution=dict(firmware_counter),
                    occurrence_rate=rate,
                    severity=severity
                )
        
        return error_stats
    
    def _identify_systemic_issues(self, fleet_state: FleetState, 
                                 error_stats: Dict[str, ErrorStatistics]) -> List[Dict[str, Any]]:
        """识别系统性问题"""
        systemic_issues = []
        
        for error_code, stats in error_stats.items():
            # 判断是否为系统性问题
            if (stats.affected_robots >= 3 or  # 影响3台以上
                stats.occurrence_rate >= 0.4 or  # 发生率40%以上
                len(stats.models_affected) > 1):  # 影响多个型号
                
                # 分析根本原因
                root_cause_analysis = self._analyze_root_cause(fleet_state, error_code)
                
                systemic_issues.append({
                    "error_code": error_code,
                    "affected_robots": stats.affected_robots,
                    "occurrence_rate": stats.occurrence_rate,
                    "models_affected": stats.models_affected,
                    "firmware_distribution": stats.firmware_distribution,
                    "severity": stats.severity,
                    "root_cause_analysis": root_cause_analysis,
                    "confidence": min(0.9, 0.3 + stats.occurrence_rate * 0.7)  # 基于发生率的置信度
                })
        
        # 按严重程度和影响范围排序
        systemic_issues.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}.get(x["severity"], 0),
            x["affected_robots"],
            x["occurrence_rate"]
        ), reverse=True)
        
        return systemic_issues
    
    def _identify_single_unit_issues(self, fleet_state: FleetState,
                                    error_stats: Dict[str, ErrorStatistics]) -> List[Dict[str, Any]]:
        """识别单机问题"""
        single_unit_issues = []
        
        for error_code, stats in error_stats.items():
            if stats.affected_robots == 1:  # 只影响一台设备
                affected_robot = fleet_state.get_robots_with_error(error_code)[0]
                
                single_unit_issues.append({
                    "robot_id": affected_robot.robot_id,
                    "error_code": error_code,
                    "model": affected_robot.model,
                    "firmware": affected_robot.firmware,
                    "location": affected_robot.location,
                    "battery_level": affected_robot.battery_level,
                    "severity": stats.severity,
                    "possible_causes": [
                        "硬件故障",
                        "传感器标定偏移",
                        "设备特定配置错误",
                        "安装位置问题",
                        "环境干扰"
                    ]
                })
        
        # 按严重程度排序
        single_unit_issues.sort(key=lambda x: 
            {"high": 3, "medium": 2, "low": 1}.get(x["severity"], 0), 
            reverse=True
        )
        
        return single_unit_issues
    
    def _analyze_root_cause(self, fleet_state: FleetState, error_code: str) -> Dict[str, Any]:
        """分析根本原因"""
        affected_robots = fleet_state.get_robots_with_error(error_code)
        
        if not affected_robots:
            return {
                "common_features": {"models": [], "firmware_versions": [], "locations": []},
                "possible_root_causes": [],
                "most_likely_cause": {"type": "unknown", "confidence": 0.0}
            }
        
        # 分析共同特征
        common_models = set(r.model for r in affected_robots)
        common_firmware = set(r.firmware for r in affected_robots)
        common_locations = set(r.location for r in affected_robots if r.location)
        
        root_causes = []
        
        # 固件相关
        if len(common_firmware) == 1:
            firmware = next(iter(common_firmware))
            total_with_firmware = len([r for r in fleet_state.robots if r.firmware == firmware])
            affected_with_firmware = len([r for r in affected_robots if r.firmware == firmware])
            # 安全计算发生率
            rate = affected_with_firmware / total_with_firmware if total_with_firmware > 0 else 0
            
            root_causes.append({
                "type": "firmware",
                "firmware_version": firmware,
                "affected_ratio": f"{affected_with_firmware}/{total_with_firmware}",
                "occurrence_rate": rate,
                "confidence": min(0.9, 0.5 + rate * 0.5)
            })
        
        # 型号相关
        if len(common_models) == 1:
            model = next(iter(common_models))
            root_causes.append({
                "type": "model_specific",
                "model": model,
                "description": f"仅影响{model}型号设备",
                "confidence": 0.7
            })
        
        # 位置相关
        if len(common_locations) == 1:
            location = next(iter(common_locations))
            root_causes.append({
                "type": "environmental",
                "location": location,
                "description": f"所有受影响设备都在{location}区域",
                "confidence": 0.6
            })
        
        # 时间模式
        if all(r.last_seen for r in affected_robots):
            timestamps = [r.last_seen for r in affected_robots]
            timestamps.sort()
            
            if timestamps:
                time_diff = max(timestamps) - min(timestamps)
                
                if time_diff < timedelta(hours=1):
                    root_causes.append({
                        "type": "temporal",
                        "description": "错误在短时间内集中出现",
                        "time_window": str(time_diff),
                        "confidence": 0.8
                    })
        
        return {
            "common_features": {
                "models": list(common_models),
                "firmware_versions": list(common_firmware),
                "locations": list(common_locations)
            },
            "possible_root_causes": root_causes,
            "most_likely_cause": root_causes[0] if root_causes else {"type": "unknown", "confidence": 0.3}
        }
    
    def _generate_recommendations(self, systemic_issues: List[Dict[str, Any]],
                                single_unit_issues: List[Dict[str, Any]],
                                fleet_state: FleetState) -> List[str]:
        """生成建议措施"""
        recommendations = []
        
        # 系统性问题建议
        if systemic_issues:
            recommendations.append("🚨 **系统性问题需要立即处理**")
            
            for issue in systemic_issues[:2]:  # 前2个最严重的
                error_code = issue["error_code"]
                affected = issue["affected_robots"]
                
                root_cause = issue.get("root_cause_analysis", {}).get("most_likely_cause", {})
                if root_cause.get("type") == "firmware":
                    firmware_version = root_cause.get("firmware_version", "unknown")
                    rec = f"- 固件相关：建议对{firmware_version}固件版本进行回滚或更新（影响{affected}台设备）"
                elif len(issue.get("models_affected", [])) == 1:
                    model = issue["models_affected"][0]
                    rec = f"- 型号特定：检查{model}型号的设计或配置（影响{affected}台设备）"
                else:
                    rec = f"- 批量处理：针对{error_code}错误制定批量处理方案（影响{affected}台设备）"
                
                recommendations.append(rec)
        
        # 单机问题建议
        if single_unit_issues:
            if len(single_unit_issues) <= 3:
                for issue in single_unit_issues:
                    recommendations.append(
                        f"- 单机检修：检查{issue['robot_id']}的{issue['error_code']}错误"
                    )
            else:
                recommendations.append(f"- 批量检修：安排对{len(single_unit_issues)}台单机问题设备进行集中检修")
        
        # 预防性建议
        total_robots = len(fleet_state.robots)
        if total_robots > 0:
            error_rate = len([r for r in fleet_state.robots if r.errors]) / total_robots
            
            if error_rate > 0.3:
                recommendations.append("📊 **车队整体可靠性需要提升**")
                recommendations.append("- 建立定期维护计划")
                recommendations.append("- 实施固件版本管理策略")
                recommendations.append("- 加强现场环境监控")
        
        if not recommendations:
            recommendations.append("✅ 车队运行状态良好，保持当前维护策略")
        
        return recommendations
    
    def _generate_detailed_analysis(self, fleet_state: FleetState,
                                   systemic_issues: List[Dict[str, Any]],
                                   single_unit_issues: List[Dict[str, Any]],
                                   error_stats: Dict[str, ErrorStatistics]) -> str:
        """生成详细分析报告"""
        parts = []
        
        parts.append("📋 **车队诊断详细报告**")
        parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        parts.append("")
        
        # 如果车队为空
        if not fleet_state.robots:
            parts.append("## 1. 车队概况")
            parts.append("- 设备总数: 0台")
            parts.append("- 异常设备: 0台")
            parts.append("- 异常率: 0.0%")
            parts.append("")
            parts.append("## 2. 分析结论")
            parts.append("当前车队为空，无法进行详细分析。")
            return "\n".join(parts)
        
        # 车队概况
        parts.append("## 1. 车队概况")
        parts.append(f"- 设备总数: {len(fleet_state.robots)}台")
        parts.append(f"- 异常设备: {len([r for r in fleet_state.robots if r.errors])}台")
        
        # 安全计算异常率
        error_rate = len([r for r in fleet_state.robots if r.errors]) / len(fleet_state.robots)
        parts.append(f"- 异常率: {error_rate:.1%}")
        
        # 型号分布
        model_dist = fleet_state.get_robot_count_by_model()
        parts.append(f"- 型号分布: {', '.join([f'{k}({v}台)' for k, v in model_dist.items()])}")
        
        # 固件分布
        from collections import Counter
        firmware_dist = Counter([r.firmware for r in fleet_state.robots])
        parts.append(f"- 固件分布: {', '.join([f'v{v}({c}台)' for v, c in firmware_dist.items()])}")
        
        # 系统性问题
        if systemic_issues:
            parts.append("")
            parts.append("## 2. 系统性问题分析")
            
            for i, issue in enumerate(systemic_issues, 1):
                parts.append(f"### 2.{i} {issue['error_code']}错误")
                parts.append(f"- 影响范围: {issue['affected_robots']}台设备")
                parts.append(f"- 发生率: {issue['occurrence_rate']:.1%}")
                parts.append(f"- 影响型号: {', '.join(issue['models_affected'])}")
                parts.append(f"- 严重程度: {issue['severity'].upper()}")
                
                root_cause = issue.get('root_cause_analysis', {}).get('most_likely_cause', {})
                if root_cause:
                    parts.append(f"- 最可能原因: {root_cause.get('type', 'unknown')} "
                               f"(置信度: {root_cause.get('confidence', 0):.1%})")
        
        # 单机问题
        if single_unit_issues:
            parts.append("")
            parts.append("## 3. 单机问题列表")
            
            for i, issue in enumerate(single_unit_issues[:5], 1):  # 限制前5个
                parts.append(f"### 3.{i} {issue['robot_id']}")
                parts.append(f"- 错误代码: {issue['error_code']}")
                parts.append(f"- 型号/固件: {issue['model']} v{issue['firmware']}")
                parts.append(f"- 严重程度: {issue['severity'].upper()}")
                
                if issue.get('location'):
                    parts.append(f"- 位置: {issue['location']}")
        
        # 统计分析
        parts.append("")
        parts.append("## 4. 统计分析")
        
        if error_stats:
            top_errors = sorted(error_stats.values(), 
                              key=lambda x: x.affected_robots, 
                              reverse=True)[:3]
            
            for i, stat in enumerate(top_errors, 1):
                parts.append(f"{i}. {stat.error_code}: {stat.affected_robots}台设备 "
                           f"(发生率: {stat.occurrence_rate:.1%})")
        
        # 综合建议
        parts.append("")
        parts.append("## 5. 综合建议")
        
        if systemic_issues:
            parts.append("**优先处理系统性问题：**")
            parts.append("1. 针对高频错误制定批量解决方案")
            parts.append("2. 分析固件版本差异，考虑回滚或更新")
            parts.append("3. 建立问题复现和验证机制")
        
        if single_unit_issues:
            parts.append("")
            parts.append("**处理单机问题：**")
            parts.append("1. 按优先级安排现场检修")
            parts.append("2. 记录并分析单机故障模式")
            parts.append("3. 考虑预防性维护措施")
        
        return "\n".join(parts)
    
    async def _analyze_specific_error(self, fleet_state: FleetState, 
                                     error_code: str) -> Dict[str, Any]:
        """分析特定错误"""
        return await self.analyze_specific_error(fleet_state, error_code)