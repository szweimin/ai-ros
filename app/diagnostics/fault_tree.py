"""
故障诊断树数据结构
包含预定义的工程诊断知识
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class FaultCause(BaseModel):
    """故障原因"""
    id: str = Field(..., description="原因ID")
    description: str = Field(..., description="原因描述")
    check: str = Field(..., description="检查步骤")
    probability: float = Field(1.0, description="基础概率（0-1）")
    prerequisites: Optional[List[str]] = Field(None, description="前提条件")
    
class FaultTree(BaseModel):
    """故障树"""
    error_code: str = Field(..., description="错误代码")
    description: str = Field(..., description="错误描述")
    category: str = Field("safety", description="错误类别")
    severity: str = Field("high", description="严重程度")
    causes: List[FaultCause] = Field(..., description="可能原因列表")
    recovery_steps: Optional[List[str]] = Field(None, description="恢复步骤")
    related_codes: Optional[List[str]] = Field(None, description="相关错误代码")

# 预定义的故障诊断树
FAULT_TREES: Dict[str, FaultTree] = {
    "E201": FaultTree(
        error_code="E201",
        description="Safety stop active - All movement inhibited",
        category="safety",
        severity="high",
        causes=[
            FaultCause(
                id="laser_triggered",
                description="Safety laser scanner detected obstacle in protection field",
                check="Check laser scanner field status and clear any obstacles",
                probability=0.6,
                prerequisites=["laser_scanner_connected"]
            ),
            FaultCause(
                id="emergency_stop_pressed",
                description="Emergency stop button pressed",
                check="Inspect all physical emergency stop buttons and release if pressed",
                probability=0.3,
                prerequisites=["emergency_circuit_active"]
            ),
            FaultCause(
                id="safety_plc_fault",
                description="Safety PLC not in ready state",
                check="Verify safety PLC status LEDs and reset if necessary",
                probability=0.2,
                prerequisites=["plc_powered"]
            ),
            FaultCause(
                id="safety_gate_open",
                description="Safety gate or door interlock open",
                check="Ensure all safety gates are properly closed",
                probability=0.4
            )
        ],
        recovery_steps=[
            "Clear any obstacles from safety zones",
            "Reset emergency stop buttons",
            "Cycle safety PLC power",
            "Perform safety system test"
        ]
    ),
    "E301": FaultTree(
        error_code="E301",
        description="Joint limit violation - Joint position exceeds allowed range",
        category="motion",
        severity="medium",
        causes=[
            FaultCause(
                id="software_limit_exceeded",
                description="Software joint limit exceeded due to incorrect parameters",
                check="Check joint limit parameters in configuration files",
                probability=0.5
            ),
            FaultCause(
                id="hardware_limit_triggered",
                description="Hardware limit switch triggered",
                check="Inspect physical limit switches and wiring",
                probability=0.4
            ),
            FaultCause(
                id="calibration_error",
                description="Joint calibration incorrect or lost",
                check="Re-calibrate joint zero position",
                probability=0.3
            ),
            FaultCause(
                id="controller_fault",
                description="Motion controller internal error",
                check="Check controller error logs and reset",
                probability=0.2
            )
        ],
        recovery_steps=[
            "Move joint to safe position manually",
            "Verify and adjust joint limits",
            "Re-calibrate joint",
            "Reset motion controller"
        ]
    ),
    "E101": FaultTree(
        error_code="E101",
        description="ROS master connection failure",
        category="communication",
        severity="high",
        causes=[
            FaultCause(
                id="network_issue",
                description="Network connectivity problem",
                check="Check network cables, switches, and firewall settings",
                probability=0.6
            ),
            FaultCause(
                id="master_not_running",
                description="ROS master process not running",
                check="Verify roscore is running on the correct machine",
                probability=0.5
            ),
            FaultCause(
                id="host_config_error",
                description="Incorrect hostname or IP configuration",
                check="Check ROS_MASTER_URI and /etc/hosts configuration",
                probability=0.4
            ),
            FaultCause(
                id="port_blocked",
                description="Required ports blocked by firewall",
                check="Ensure ports 11311 (ROS master) are open",
                probability=0.3
            )
        ],
        recovery_steps=[
            "Restart roscore on master machine",
            "Verify network connectivity",
            "Check ROS environment variables",
            "Restart affected nodes"
        ]
    ),
    "E102": FaultTree(
        error_code="E102",
        description="ROS node initialization failure",
        category="system",
        severity="medium",
        causes=[
            FaultCause(
                id="parameter_error",
                description="Required parameters missing or invalid",
                check="Check launch files and parameter server",
                probability=0.5
            ),
            FaultCause(
                id="resource_conflict",
                description="Resource conflict (port, device, file)",
                check="Check for duplicate node names or resource usage",
                probability=0.4
            ),
            FaultCause(
                id="dependency_missing",
                description="Required dependency or package not available",
                check="Verify all ROS packages are installed and sourced",
                probability=0.3
            ),
            FaultCause(
                id="permission_issue",
                description="Permission denied for required resources",
                check="Check file permissions and user privileges",
                probability=0.2
            )
        ],
        recovery_steps=[
            "Verify parameter values",
            "Check for naming conflicts",
            "Install missing dependencies",
            "Adjust permissions"
        ]
    ),
    "W001": FaultTree(
        error_code="W001",
        description="Low battery warning",
        category="power",
        severity="low",
        causes=[
            FaultCause(
                id="battery_depleted",
                description="Battery charge level critically low",
                check="Check battery voltage and state of charge",
                probability=0.8
            ),
            FaultCause(
                id="charging_fault",
                description="Charger not functioning properly",
                check="Verify charger connection and output",
                probability=0.3
            ),
            FaultCause(
                id="battery_fault",
                description="Battery cell or management system fault",
                check="Check battery management system diagnostics",
                probability=0.2
            ),
            FaultCause(
                id="high_power_drain",
                description="Excessive power consumption",
                check="Monitor current draw during operation",
                probability=0.4
            )
        ],
        recovery_steps=[
            "Connect to charger immediately",
            "Reduce power consumption",
            "Check charging system",
            "Replace battery if necessary"
        ]
    )
}

def get_fault_tree(error_code: str) -> Optional[FaultTree]:
    """获取指定错误代码的故障树"""
    return FAULT_TREES.get(error_code)

def get_all_fault_trees() -> Dict[str, FaultTree]:
    """获取所有故障树"""
    return FAULT_TREES

def get_related_fault_trees(error_code: str) -> List[FaultTree]:
    """获取相关故障树"""
    tree = get_fault_tree(error_code)
    if not tree or not tree.related_codes:
        return []
    
    related = []
    for code in tree.related_codes:
        related_tree = get_fault_tree(code)
        if related_tree:
            related.append(related_tree)
    
    return related

def format_fault_tree_for_prompt(tree: FaultTree) -> str:
    """将故障树格式化为提示词"""
    if not tree:
        return ""
    
    formatted = [
        f"Error Code: {tree.error_code}",
        f"Description: {tree.description}",
        f"Category: {tree.category} | Severity: {tree.severity}",
        "",
        "Possible Causes (sorted by probability):"
    ]
    
    # 按概率排序
    sorted_causes = sorted(tree.causes, key=lambda x: x.probability, reverse=True)
    
    for i, cause in enumerate(sorted_causes, 1):
        formatted.append(f"  {i}. {cause.description}")
        formatted.append(f"     Check: {cause.check}")
        formatted.append(f"     Probability: {cause.probability:.1%}")
        if cause.prerequisites:
            formatted.append(f"     Prerequisites: {', '.join(cause.prerequisites)}")
        formatted.append("")
    
    if tree.recovery_steps:
        formatted.append("Recommended Recovery Steps:")
        for i, step in enumerate(tree.recovery_steps, 1):
            formatted.append(f"  {i}. {step}")
    
    return "\n".join(formatted)
