from typing import Dict, Any, List
import logging
from app.models.runtime_snapshot import RuntimeSnapshot

logger = logging.getLogger(__name__)


class AIProcessor:
    """AI分析处理器 - 遵循原则：不订阅实时数据，只分析快照"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.analysis_rules = self._load_analysis_rules()
    
    def _load_analysis_rules(self) -> List[Dict]:
        """加载分析规则（代码逻辑，不依赖embedding）"""
        return [
            {
                "name": "error_detection",
                "condition": lambda snap: len(snap.errors) > 0,
                "action": "trigger_error_analysis",
                "severity": "high"
            },
            {
                "name": "joint_anomaly",
                "condition": lambda snap: any(abs(v) > 10.0 for v in snap.joint_states.values()),
                "action": "check_joint_limits",
                "severity": "medium"
            },
            {
                "name": "topic_missing",
                "condition": lambda snap: len(snap.active_topics) < 2,
                "action": "check_communication",
                "severity": "low"
            }
        ]
    
    async def analyze_snapshot(self, snapshot: RuntimeSnapshot) -> Dict[str, Any]:
        """
        分析运行时快照
        原则：推理发生在服务层，LLM只是分析器
        """
        # 1. 基于规则的初步分析
        rule_results = []
        for rule in self.analysis_rules:
            if rule["condition"](snapshot):
                rule_results.append({
                    "rule": rule["name"],
                    "action": rule["action"],
                    "severity": rule["severity"],
                    "triggered_at": snapshot.timestamp
                })
        
        # 2. 如果有错误，准备LLM分析上下文
        llm_analysis = None
        if snapshot.errors and self.llm_client:
            try:
                analysis_context = {
                    "robot_id": snapshot.robot_id,
                    "model": snapshot.model,
                    "firmware": snapshot.firmware,
                    "errors": snapshot.errors,
                    "joint_states": snapshot.joint_states,
                    "active_topics": snapshot.active_topics,
                    "source": snapshot.source.value
                }
                
                # 调用LLM进行诊断（异步）
                llm_analysis = await self._call_llm_for_diagnosis(analysis_context)
                
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}")
                llm_analysis = {"error": str(e)}
        
        # 3. 生成分析报告
        analysis_report = {
            "snapshot_id": f"{snapshot.robot_id}_{snapshot.timestamp}",
            "timestamp": snapshot.timestamp,
            "rule_based_findings": rule_results,
            "llm_analysis": llm_analysis,
            "recommendations": self._generate_recommendations(rule_results, llm_analysis),
            "summary": self._generate_summary(rule_results)
        }
        
        return analysis_report
    
    async def _call_llm_for_diagnosis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """调用LLM进行诊断分析"""
        # 这里根据您的LLM客户端实现进行调整
        prompt = f"""
        分析机器人故障：
        - 机器人ID: {context['robot_id']}
        - 型号: {context['model']}
        - 固件: {context['firmware']}
        - 错误代码: {context['errors']}
        - 关节状态: {context['joint_states']}
        - 活跃话题: {context['active_topics']}
        - 数据源: {context['source']}
        
        请提供：
        1. 可能的故障原因
        2. 建议的排查步骤
        3. 紧急程度评估
        """
        
        # 假设您的LLM客户端有一个query方法
        if hasattr(self.llm_client, 'query'):
            response = await self.llm_client.query(prompt)
            return {
                "analysis": response,
                "confidence": 0.85,  # 示例置信度
                "suggested_actions": self._extract_actions_from_response(response)
            }
        else:
            return {
                "analysis": "LLM analysis not available",
                "confidence": 0.0,
                "suggested_actions": []
            }
    
    def _generate_recommendations(self, rule_results, llm_analysis):
        """基于分析结果生成建议"""
        recommendations = []
        
        # 基于规则的建议
        for finding in rule_results:
            if finding["rule"] == "error_detection":
                recommendations.append("检查机器人错误代码手册")
            elif finding["rule"] == "joint_anomaly":
                recommendations.append("检查关节限位和校准")
            elif finding["rule"] == "topic_missing":
                recommendations.append("验证ROS2节点连接状态")
        
        # 基于LLM分析的建议
        if llm_analysis and "suggested_actions" in llm_analysis:
            recommendations.extend(llm_analysis["suggested_actions"])
        
        return list(set(recommendations))  # 去重
    
    def _generate_summary(self, rule_results):
        """生成分析摘要"""
        if not rule_results:
            return "✅ 一切正常"
        
        high_issues = sum(1 for r in rule_results if r["severity"] == "high")
        medium_issues = sum(1 for r in rule_results if r["severity"] == "medium")
        low_issues = sum(1 for r in rule_results if r["severity"] == "low")
        
        return f"⚠️ 发现{high_issues}个高优先级、{medium_issues}个中优先级、{low_issues}个低优先级问题"
    
    def _extract_actions_from_response(self, response: str) -> List[str]:
        """从LLM响应中提取行动项"""
        # 简单的关键词匹配，您可以根据需要扩展
        actions = []
        if "calibrate" in response.lower():
            actions.append("执行校准程序")
        if "restart" in response.lower():
            actions.append("重启相关服务")
        if "check connection" in response.lower():
            actions.append("检查网络连接")
        if "update firmware" in response.lower():
            actions.append("检查固件更新")
        
        return actions if actions else ["按照标准故障排除流程检查"]