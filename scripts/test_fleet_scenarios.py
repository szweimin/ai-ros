"""
车队诊断场景测试
"""
import json
from datetime import datetime
import os
import sys
from fastapi.testclient import TestClient
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app

client = TestClient(app)


def create_scenario(name: str) -> dict:
    """创建不同测试场景"""
    now = datetime.now().isoformat()
    
    scenarios = {
        "all_normal": {
            "robots": [
                {
                    "robot_id": f"robot-{i}",
                    "model": "A1",
                    "firmware": "v2.0",
                    "errors": [],
                    "last_seen": now,
                    "battery_level": 90.0
                }
                for i in range(1, 6)  # 5台正常设备
            ]
        },
        "firmware_issue": {
            "robots": [
                *[
                    {
                        "robot_id": f"robot-v2-{i}",
                        "model": "A1",
                        "firmware": "v2.1",
                        "errors": ["E201", "E202"],
                        "last_seen": now,
                        "battery_level": 85.0
                    }
                    for i in range(1, 4)  # 3台v2.1设备都有错误
                ],
                *[
                    {
                        "robot_id": f"robot-v2.0-{i}",
                        "model": "A1",
                        "firmware": "v2.0",
                        "errors": [],
                        "last_seen": now,
                        "battery_level": 95.0
                    }
                    for i in range(1, 3)  # 2台v2.0设备都正常
                ]
            ]
        },
        "model_specific_issue": {
            "robots": [
                *[
                    {
                        "robot_id": f"robot-A1-{i}",
                        "model": "A1",
                        "firmware": "v2.0",
                        "errors": ["E301"],
                        "last_seen": now,
                        "battery_level": 80.0
                    }
                    for i in range(1, 4)  # 3台A1型号有错误
                ],
                *[
                    {
                        "robot_id": f"robot-B2-{i}",
                        "model": "B2",
                        "firmware": "v2.0",
                        "errors": [],
                        "last_seen": now,
                        "battery_level": 90.0
                    }
                    for i in range(1, 3)  # 2台B2型号正常
                ]
            ]
        },
        "mixed_issues": {
            "robots": [
                # 系统性问题：E201在多台设备出现
                {
                    "robot_id": "robot-001",
                    "model": "A1",
                    "firmware": "v2.1",
                    "errors": ["E201", "E101"],
                    "last_seen": now,
                    "battery_level": 85.0
                },
                {
                    "robot_id": "robot-002",
                    "model": "A1",
                    "firmware": "v2.1",
                    "errors": ["E201"],
                    "last_seen": now,
                    "battery_level": 78.0
                },
                # 单机问题
                {
                    "robot_id": "robot-003",
                    "model": "B2",
                    "firmware": "v1.5",
                    "errors": ["E301"],
                    "last_seen": now,
                    "battery_level": 65.0
                },
                # 正常设备
                {
                    "robot_id": "robot-004",
                    "model": "A1",
                    "firmware": "v2.0",
                    "errors": [],
                    "last_seen": now,
                    "battery_level": 92.0
                },
                {
                    "robot_id": "robot-005",
                    "model": "C3",
                    "firmware": "v2.0",
                    "errors": [],
                    "last_seen": now,
                    "battery_level": 88.0
                }
            ]
        }
    }
    
    return scenarios.get(name, scenarios["all_normal"])


def test_scenario(scenario_name: str):
    """测试特定场景"""
    print(f"\n🔍 测试场景: {scenario_name}")
    print("-" * 40)
    
    fleet_data = create_scenario(scenario_name)
    
    # 分析车队
    request_data = {
        "fleet_state": fleet_data,
        "analysis_depth": "standard",
        "include_comparison": True
    }
    
    response = client.post("/api/v1/fleet-diagnostics/analyze-fleet",
                          json=request_data)
    
    assert response.status_code == 200
    result = response.json()
    
    print(f"设备总数: {result['summary']['total_robots']}")
    print(f"异常设备: {result['summary']['robots_with_errors']}")
    print(f"系统性问题: {len(result['systemic_issues'])}个")
    print(f"单机问题: {len(result['single_unit_issues'])}个")
    
    # 根据场景验证预期结果
    if scenario_name == "all_normal":
        assert len(result['systemic_issues']) == 0
        assert len(result['single_unit_issues']) == 0
        print("✅ 验证通过: 所有设备正常")
    
    elif scenario_name == "firmware_issue":
        assert len(result['systemic_issues']) > 0
        # E201/E202应该是系统性问题
        systemic_errors = [issue['error_code'] for issue in result['systemic_issues']]
        assert 'E201' in systemic_errors or 'E202' in systemic_errors
        print("✅ 验证通过: 检测到固件相关问题")
    
    elif scenario_name == "model_specific_issue":
        assert len(result['systemic_issues']) > 0
        # E301应该是系统性问题（仅影响A1型号）
        e301_issues = [issue for issue in result['systemic_issues'] 
                      if issue['error_code'] == 'E301']
        assert len(e301_issues) > 0
        print("✅ 验证通过: 检测到型号特定问题")
    
    elif scenario_name == "mixed_issues":
        # 应该有系统性问题（E201）和单机问题（E301）
        assert len(result['systemic_issues']) > 0
        assert len(result['single_unit_issues']) > 0
        
        # 检查E201是否为系统性问题
        e201_issues = [issue for issue in result['systemic_issues'] 
                      if issue['error_code'] == 'E201']
        assert len(e201_issues) > 0
        
        # 检查E301是否为单机问题
        e301_issues = [issue for issue in result['single_unit_issues'] 
                      if issue['error_code'] == 'E301']
        assert len(e301_issues) > 0
        
        print("✅ 验证通过: 检测到混合问题")


def run_all_scenarios():
    """运行所有场景测试"""
    print("=" * 60)
    print("车队诊断场景测试")
    print("=" * 60)
    
    scenarios = [
        "all_normal",
        "firmware_issue", 
        "model_specific_issue",
        "mixed_issues"
    ]
    
    for scenario in scenarios:
        try:
            test_scenario(scenario)
        except AssertionError as e:
            print(f"❌ 场景 '{scenario}' 失败: {e}")
        except Exception as e:
            print(f"❌ 场景 '{scenario}' 发生错误: {e}")
    
    print("\n" + "=" * 60)
    print("场景测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_scenarios()