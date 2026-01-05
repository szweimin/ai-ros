"""
车队分析工具类 - 修复版本
"""
from typing import Dict, List, Tuple, Any
from collections import Counter
import statistics
from datetime import datetime, timedelta

from app.models.fleet import FleetState, RobotState


class FleetAnalyzer:
    """车队分析器"""
    
    def analyze_error_trends(self, fleet_state: FleetState, 
                            error_code: str) -> Dict[str, Any]:
        """分析错误趋势"""
        affected_robots = fleet_state.get_robots_with_error(error_code)
        
        if not affected_robots:
            return {"trend": "stable", "message": "No occurrences"}
        
        # 按时间分析趋势（如果有时间信息）
        if all(r.last_seen for r in affected_robots):
            timestamps = [r.last_seen for r in affected_robots]
            timestamps.sort()
            
            # 判断是否在短时间内集中出现
            if len(timestamps) >= 3:
                time_diffs = []
                for i in range(1, len(timestamps)):
                    diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # 小时
                    time_diffs.append(diff)
                
                avg_diff = statistics.mean(time_diffs) if time_diffs else 0
                
                if avg_diff < 1:  # 平均间隔小于1小时
                    trend = "clustered"
                    trend_desc = f"错误在短时间内集中出现（平均间隔{avg_diff:.1f}小时）"
                elif avg_diff < 24:  # 平均间隔小于1天
                    trend = "increasing"
                    trend_desc = f"错误频率呈上升趋势（平均间隔{avg_diff:.1f}小时）"
                else:
                    trend = "sporadic"
                    trend_desc = f"错误零星出现（平均间隔{avg_diff:.1f}小时）"
            else:
                trend = "insufficient_data"
                trend_desc = "数据不足判断趋势"
        else:
            trend = "unknown"
            trend_desc = "缺少时间信息，无法分析趋势"
        
        return {
            "trend": trend,
            "description": trend_desc,
            "affected_count": len(affected_robots),
            "first_seen": min(r.last_seen for r in affected_robots if r.last_seen).isoformat() 
                         if affected_robots and all(r.last_seen for r in affected_robots) 
                         else "unknown",
            "last_seen": max(r.last_seen for r in affected_robots if r.last_seen).isoformat() 
                        if affected_robots and all(r.last_seen for r in affected_robots) 
                        else "unknown"
        }
    
    def analyze_firmware_impact(self, fleet_state: FleetState) -> Dict[str, Any]:
        """分析固件版本的影响"""
        firmware_stats = {}
        
        for robot in fleet_state.robots:
            firmware = robot.firmware
            if firmware not in firmware_stats:
                firmware_stats[firmware] = {
                    "total_robots": 0,
                    "robots_with_errors": 0,
                    "error_codes": Counter(),
                    "models": Counter()
                }
            
            stats = firmware_stats[firmware]
            stats["total_robots"] += 1
            stats["models"][robot.model] += 1
            
            if robot.errors:
                stats["robots_with_errors"] += 1
                for error in robot.errors:
                    stats["error_codes"][error] += 1
        
        # 计算错误率
        for firmware, stats in firmware_stats.items():
            total = stats["total_robots"]
            if total > 0:
                stats["error_rate"] = stats["robots_with_errors"] / total
                stats["most_common_error"] = stats["error_codes"].most_common(1)
            else:
                stats["error_rate"] = 0
                stats["most_common_error"] = []
        
        return firmware_stats
    
    def compare_model_performance(self, fleet_state: FleetState) -> Dict[str, Any]:
        """比较不同型号的性能"""
        model_stats = {}
        
        for robot in fleet_state.robots:
            model = robot.model
            if model not in model_stats:
                model_stats[model] = {
                    "total_robots": 0,
                    "robots_with_errors": 0,
                    "total_errors": 0,
                    "firmware_versions": Counter(),
                    "common_errors": Counter()
                }
            
            stats = model_stats[model]
            stats["total_robots"] += 1
            stats["firmware_versions"][robot.firmware] += 1
            
            if robot.errors:
                stats["robots_with_errors"] += 1
                stats["total_errors"] += len(robot.errors)
                for error in robot.errors:
                    stats["common_errors"][error] += 1
        
        # 计算指标
        for model, stats in model_stats.items():
            total = stats["total_robots"]
            if total > 0:
                stats["error_rate"] = stats["robots_with_errors"] / total
                stats["avg_errors_per_robot"] = stats["total_errors"] / total if total > 0 else 0
                stats["reliability_score"] = 1 - stats["error_rate"]
            else:
                stats["error_rate"] = 0
                stats["avg_errors_per_robot"] = 0
                stats["reliability_score"] = 0
        
        # 按可靠性排序
        sorted_models = sorted(
            model_stats.items(),
            key=lambda x: x[1]["reliability_score"],
            reverse=True
        )
        
        return {
            "statistics": model_stats,
            "ranking": [
                {
                    "model": model,
                    "reliability_score": stats["reliability_score"],
                    "error_rate": stats["error_rate"],
                    "total_robots": stats["total_robots"]
                }
                for model, stats in sorted_models
            ]
        }
    
    def identify_correlation(self, fleet_state: FleetState, 
                           factor1: str, factor2: str) -> Dict[str, Any]:
        """识别两个因素之间的相关性
        
        Args:
            factor1: 第一个因素（model/firmware/location）
            factor2: 第二个因素（error_code/battery_level/etc）
        """
        # 构建交叉表
        cross_table = {}
        
        for robot in fleet_state.robots:
            # 获取因子1的值
            if factor1 == "model":
                val1 = robot.model
            elif factor1 == "firmware":
                val1 = robot.firmware
            elif factor1 == "location" and robot.location:
                val1 = robot.location
            else:
                continue
            
            # 获取因子2的值
            if factor2 == "error_code":
                val2 = robot.errors[0] if robot.errors else "no_error"
            elif factor2 == "battery_level" and robot.battery_level is not None:
                if robot.battery_level < 20:
                    val2 = "low"
                elif robot.battery_level < 50:
                    val2 = "medium"
                else:
                    val2 = "high"
            else:
                continue
            
            if val1 not in cross_table:
                cross_table[val1] = Counter()
            
            cross_table[val1][val2] += 1
        
        # 分析相关性
        correlation_analysis = {}
        for val1, counter in cross_table.items():
            total = sum(counter.values())
            if total > 0:
                most_common = counter.most_common(1)
                if most_common:
                    most_common_val, count = most_common[0]
                    percentage = count / total
                    
                    correlation_analysis[val1] = {
                        "most_common": most_common_val,
                        "percentage": percentage,
                        "total_samples": total,
                        "distribution": dict(counter)
                    }
        
        # 找出强相关性
        strong_correlations = []
        for val1, analysis in correlation_analysis.items():
            if analysis["percentage"] > 0.7:  # 70%以上认为是强相关
                strong_correlations.append({
                    "factor1_value": val1,
                    "factor2_value": analysis["most_common"],
                    "strength": analysis["percentage"],
                    "samples": analysis["total_samples"]
                })
        
        return {
            "factors": f"{factor1} vs {factor2}",
            "cross_table": cross_table,
            "correlation_analysis": correlation_analysis,
            "strong_correlations": strong_correlations
        }