"""
简化的车队诊断测试 - 不使用pytest
"""
import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.fleet import FleetState, RobotState, FleetDiagnosisRequest
from app.services.diagnostic_service import DiagnosticService
from app.services.fleet_diagnostic_service import FleetDiagnosticService


def create_test_fleet_state() -> FleetState:
    """创建测试用的车队状态"""
    return FleetState(
        robots=[
            RobotState(
                robot_id="test-001",
                model="A1",
                firmware="v2.0",
                errors=["E201", "E101"],
                last_seen=datetime.now()
            ),
            RobotState(
                robot_id="test-002",
                model="A1",
                firmware="v2.0",
                errors=["E201"],
                last_seen=datetime.now()
            ),
            RobotState(
                robot_id="test-003",
                model="A1",
                firmware="v1.0",
                errors=[],
                last_seen=datetime.now()
            ),
            RobotState(
                robot_id="test-004",
                model="B2",
                firmware="v2.0",
                errors=["E301"],
                last_seen=datetime.now()
            ),
        ]
    )


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始车队诊断服务测试")
    print("=" * 60)
    
    # 初始化服务
    diagnostic_service = DiagnosticService()
    fleet_diagnostic_service = FleetDiagnosticService(diagnostic_service)
    fleet_state = create_test_fleet_state()
    
    # 测试1: 车队诊断
    print("\n📋 测试1: 车队诊断")
    print("-" * 40)
    
    request = FleetDiagnosisRequest(
        fleet_state=fleet_state,
        analysis_type="standard",
        include_detailed_analysis=False
    )
    
    response = await fleet_diagnostic_service.diagnose_fleet(request)
    
    print(f"✅ 诊断状态: {response.status}")
    print(f"✅ 系统性问题: {len(response.systemic_issues)}个")
    print(f"✅ 单机问题: {len(response.single_unit_issues)}个")
    
    # 检查E201是否为系统性问题
    systemic_errors = [issue["error_code"] for issue in response.systemic_issues]
    assert "E201" in systemic_errors, "❌ E201应该被识别为系统性问题"
    print("✅ E201被正确识别为系统性问题")
    
    # 检查E301是否为单机问题
    single_unit_errors = [issue["error_code"] for issue in response.single_unit_issues]
    assert "E301" in single_unit_errors, "❌ E301应该被识别为单机问题"
    print("✅ E301被正确识别为单机问题")
    
    # 测试2: 特定错误分析
    print("\n🔍 测试2: 特定错误分析")
    print("-" * 40)
    
    # E201分析
    e201_analysis = await fleet_diagnostic_service.analyze_specific_error(fleet_state, "E201")
    print(f"✅ E201分析完成")
    print(f"   是否为系统性问题: {e201_analysis['is_systemic']}")
    print(f"   影响设备数: {e201_analysis['total_affected']}")
    
    assert e201_analysis["is_systemic"] == True, "❌ E201应该被识别为系统性问题"
    assert e201_analysis["total_affected"] == 2, "❌ E201应该影响2台设备"
    
    # E301分析
    e301_analysis = await fleet_diagnostic_service.analyze_specific_error(fleet_state, "E301")
    print(f"✅ E301分析完成")
    print(f"   是否为系统性问题: {e301_analysis['is_systemic']}")
    print(f"   影响设备数: {e301_analysis['total_affected']}")
    
    assert e301_analysis["is_systemic"] == False, "❌ E301应该被识别为单机问题"
    assert e301_analysis["total_affected"] == 1, "❌ E301应该只影响1台设备"
    
    # 测试3: 不存在的错误
    print("\n❌ 测试3: 不存在的错误分析")
    print("-" * 40)
    
    not_found_analysis = await fleet_diagnostic_service.analyze_specific_error(fleet_state, "E999")
    print(f"✅ 错误E999分析完成")
    print(f"   状态: {not_found_analysis['status']}")
    
    assert not_found_analysis["status"] == "not_found", "❌ 不存在的错误应该返回not_found"
    
    # 测试4: 同步方法测试
    print("\n⚡ 测试4: 同步方法测试")
    print("-" * 40)
    
    error_stats = fleet_diagnostic_service._analyze_error_distribution(fleet_state)
    print(f"✅ 错误分布分析完成")
    print(f"   发现错误类型: {len(error_stats)}种")
    
    systemic_issues = fleet_diagnostic_service._identify_systemic_issues(fleet_state, error_stats)
    print(f"✅ 系统性问题识别完成: {len(systemic_issues)}个")
    
    single_unit_issues = fleet_diagnostic_service._identify_single_unit_issues(fleet_state, error_stats)
    print(f"✅ 单机问题识别完成: {len(single_unit_issues)}个")
    
    # 验证统计结果
    assert len(error_stats) == 3, f"❌ 应该发现3种错误，实际发现{len(error_stats)}种"
    assert len(systemic_issues) >= 1, "❌ 应该至少发现1个系统性问题"
    assert len(single_unit_issues) >= 1, "❌ 应该至少发现1个单机问题"
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)


def test_synchronous_functions():
    """测试同步函数"""
    print("\n⚡ 同步函数测试")
    print("-" * 40)
    
    diagnostic_service = DiagnosticService()
    fleet_diagnostic_service = FleetDiagnosticService(diagnostic_service)
    fleet_state = create_test_fleet_state()
    
    # 测试错误分布分析
    error_stats = fleet_diagnostic_service._analyze_error_distribution(fleet_state)
    print(f"✅ 错误分布分析完成: {len(error_stats)}种错误")
    
    # 测试系统性问题识别
    systemic_issues = fleet_diagnostic_service._identify_systemic_issues(fleet_state, error_stats)
    print(f"✅ 系统性问题识别完成: {len(systemic_issues)}个")
    
    # 测试单机问题识别
    single_unit_issues = fleet_diagnostic_service._identify_single_unit_issues(fleet_state, error_stats)
    print(f"✅ 单机问题识别完成: {len(single_unit_issues)}个")
    
    # 验证结果
    e201_issue = None
    for issue in systemic_issues:
        if issue["error_code"] == "E201":
            e201_issue = issue
            break
    
    assert e201_issue is not None, "❌ E201应该被识别为系统性问题"
    assert e201_issue["affected_robots"] >= 2, f"❌ E201应该影响至少2台设备，实际影响{e201_issue['affected_robots']}台"
    print(f"✅ E201系统性问题验证通过: 影响{e201_issue['affected_robots']}台设备")
    
    e301_issue = None
    for issue in single_unit_issues:
        if issue["error_code"] == "E301":
            e301_issue = issue
            break
    
    assert e301_issue is not None, "❌ E301应该被识别为单机问题"
    assert e301_issue["robot_id"] == "test-004", f"❌ E301应该影响test-004，实际影响{e301_issue['robot_id']}"
    print(f"✅ E301单机问题验证通过: 影响设备{e301_issue['robot_id']}")
    
    print("✅ 所有同步测试通过！")


if __name__ == "__main__":
    print("=" * 60)
    print("车队诊断服务测试")
    print("=" * 60)
    
    try:
        # 先运行同步测试
        test_synchronous_functions()
        
        # 再运行异步测试
        asyncio.run(run_all_tests())
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保项目路径正确，并且所有依赖已安装")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()