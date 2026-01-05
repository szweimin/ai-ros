"""
车队诊断示例 - 修复版本
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.fleet import FleetState, RobotState, FleetDiagnosisRequest
from app.services.diagnostic_service import DiagnosticService
from app.services.fleet_diagnostic_service import FleetDiagnosticService


async def main():
    """主函数示例"""
    # 创建诊断服务
    diagnostic_service = DiagnosticService()
    fleet_diagnostic_service = FleetDiagnosticService(diagnostic_service)
    
    # 创建示例车队状态
    fleet_state = create_sample_fleet_state()
    
    print("🚀 AGV车队诊断系统演示")
    print("=" * 60)
    
    # 1. 执行完整车队诊断
    print("\n1. 执行完整车队诊断...")
    request = FleetDiagnosisRequest(
        fleet_state=fleet_state,
        analysis_type="deep",
        include_detailed_analysis=True
    )
    
    response = await fleet_diagnostic_service.diagnose_fleet(request)
    
    print(f"诊断状态: {response.status}")
    print(f"系统性问题: {len(response.systemic_issues)}个")
    print(f"单机问题: {len(response.single_unit_issues)}个")
    print(f"整体异常率: {response.summary.get('error_rate', 0):.1%}")
    
    # 显示系统性问题详情
    if response.systemic_issues:
        print("\n系统性问题详情:")
        for i, issue in enumerate(response.systemic_issues, 1):
            print(f"{i}. {issue['error_code']}: {issue['affected_robots']}台设备受影响")
    
    # 2. 分析特定错误
    print("\n2. 分析E201错误...")
    e201_analysis = await fleet_diagnostic_service.analyze_specific_error(
        fleet_state, "E201"
    )
    
    print(f"E201是否为系统性问题: {e201_analysis.get('is_systemic', False)}")
    print(f"影响设备: {e201_analysis.get('total_affected', 0)}台")
    
    if e201_analysis.get('is_systemic'):
        print("判断依据:")
        for reason in e201_analysis.get('systemic_reasons', []):
            print(f"  - {reason}")
    
    # 3. 显示详细分析（前300字符）
    if response.detailed_analysis:
        print(f"\n3. 详细分析摘要:\n{response.detailed_analysis[:300]}...")
    
    # 4. 显示建议
    print("\n4. 建议措施:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"{i}. {rec}")
    
    return response


def create_sample_fleet_state() -> FleetState:
    """创建示例车队状态"""
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    two_hours_ago = now - timedelta(hours=2)
    
    return FleetState(
        robots=[
            # 系统性问题示例：多台设备出现E201错误（v2.1固件）
            RobotState(
                robot_id="agv-001",
                model="A1",
                firmware="v2.1",
                errors=["E201", "E101"],
                last_seen=now,
                location="Assembly Line A",
                battery_level=85.0
            ),
            RobotState(
                robot_id="agv-002",
                model="A1",
                firmware="v2.1",
                errors=["E201"],
                last_seen=one_hour_ago,
                location="Assembly Line A",
                battery_level=78.0
            ),
            RobotState(
                robot_id="agv-003",
                model="A1",
                firmware="v2.0",
                errors=[],
                last_seen=now,
                location="Warehouse",
                battery_level=92.0
            ),
            # 单机问题示例
            RobotState(
                robot_id="agv-004",
                model="B2",
                firmware="v1.5",
                errors=["E301"],  # 单机特有的错误
                last_seen=two_hours_ago,
                location="Loading Dock",
                battery_level=65.0
            ),
            # 另一个系统性问题设备
            RobotState(
                robot_id="agv-005",
                model="A1",
                firmware="v2.1",
                errors=["E201", "E102"],
                last_seen=one_hour_ago,
                location="Assembly Line B",
                battery_level=88.0
            ),
            # 跨型号出现相同错误
            RobotState(
                robot_id="agv-006",
                model="C3",
                firmware="v2.1",
                errors=["E201"],  # 跨型号出现相同错误
                last_seen=now,
                location="Testing Area",
                battery_level=95.0
            ),
            # 正常设备
            RobotState(
                robot_id="agv-007",
                model="A1",
                firmware="v2.0",
                errors=[],
                last_seen=now,
                location="Parking",
                battery_level=100.0
            ),
            # 更多正常设备
            RobotState(
                robot_id="agv-008",
                model="A1",
                firmware="v2.0",
                errors=[],
                last_seen=now,
                location="Parking",
                battery_level=98.0
            ),
            RobotState(
                robot_id="agv-009",
                model="B2",
                firmware="v1.5",
                errors=[],
                last_seen=now,
                location="Warehouse",
                battery_level=87.0
            ),
            RobotState(
                robot_id="agv-010",
                model="C3",
                firmware="v2.0",
                errors=[],
                last_seen=now,
                location="Testing Area",
                battery_level=91.0
            ),
        ],
        timestamp=now
    )


async def run_e201_analysis():
    """专门运行E201错误分析"""
    print("\n🔍 E201错误专项分析")
    print("=" * 50)
    
    diagnostic_service = DiagnosticService()
    fleet_diagnostic_service = FleetDiagnosticService(diagnostic_service)
    
    # 创建测试场景
    fleet_state = create_e201_test_scenario()
    
    # 分析E201
    analysis = await fleet_diagnostic_service.analyze_specific_error(
        fleet_state, "E201"
    )
    
    print(f"错误代码: {analysis['error_code']}")
    print(f"是否为系统性问题: {analysis['is_systemic']}")
    print(f"影响设备数: {analysis['total_affected']}")
    
    if analysis['is_systemic']:
        print("\n系统性问题判断依据:")
        for reason in analysis.get('systemic_reasons', []):
            print(f"  ✓ {reason}")
        
        print(f"\n固件分布: {analysis.get('firmware_distribution', {})}")
        print(f"型号分布: {analysis.get('model_distribution', {})}")
    
    print(f"\n建议措施:")
    for i, rec in enumerate(analysis.get('recommendations', []), 1):
        print(f"{i}. {rec}")


def create_e201_test_scenario() -> FleetState:
    """创建E201测试场景"""
    now = datetime.now()
    
    return FleetState(
        robots=[
            # v2.1固件的A1型号 - 3台出现E201错误
            RobotState(robot_id="agv-001", model="A1", firmware="v2.1", errors=["E201"]),
            RobotState(robot_id="agv-002", model="A1", firmware="v2.1", errors=["E201"]),
            RobotState(robot_id="agv-003", model="A1", firmware="v2.1", errors=["E201"]),
            # v2.1固件的A1型号 - 1台正常
            RobotState(robot_id="agv-004", model="A1", firmware="v2.1", errors=[]),
            # v2.0固件的A1型号 - 都正常
            RobotState(robot_id="agv-005", model="A1", firmware="v2.0", errors=[]),
            RobotState(robot_id="agv-006", model="A1", firmware="v2.0", errors=[]),
            # 其他型号也出现E201（跨型号）
            RobotState(robot_id="agv-007", model="B2", firmware="v2.1", errors=["E201"]),
            # B2型号正常设备
            RobotState(robot_id="agv-008", model="B2", firmware="v1.5", errors=[]),
        ],
        timestamp=now
    )


if __name__ == "__main__":
    # 运行完整示例
    print("=" * 60)
    print("车队诊断系统示例")
    print("=" * 60)
    
    try:
        # 运行主要示例
        response = asyncio.run(main())
        
        print("\n" + "=" * 60)
        print("诊断完成！")
        
        # 运行专项分析
        asyncio.run(run_e201_analysis())
        
    except NameError as e:
        print(f"\n❌ 错误: {e}")
        print("请检查代码中的变量名是否正确")
    except Exception as e:
        print(f"\n❌ 运行时错误: {e}")
        import traceback
        traceback.print_exc()