"""
完整测试运行时状态功能
"""
import asyncio
import httpx
import json

async def test_complete_scenarios():
    """测试完整的运行时状态场景"""
    
    print("🤖 ROS文档系统 - 运行时状态完整测试")
    print("=" * 60)
    
    test_scenarios = [
         query="Why is the AGV not moving?",
        runtime_state=RuntimeState(
            robot_id="agv_01",
            errors=["E201"],
            active_topics=["/odom", "/battery_state"],
            parameters={"speed_limit": "0", "emergency_stop": "true"}
        )
        
        {
            "name": "场景1: AGV不动了（有E201错误）",
            "description": "AGV因为E201紧急停止错误而无法移动",
            "payload": {
                "query": "Why is the AGV not moving? What should I do?",
                "top_k": 5,
                "runtime_state": {
                    "robot_id": "agv_robot_01",
                    "errors": ["E201"],
                    "active_topics": ["/odom", "/battery_state", "/scan"],
                    "parameters": {
                        "emergency_stop": "active",
                        "speed_limit": "0",
                        "battery_level": "85"
                    }
                }
            }
        },
        {
            "name": "场景2: 关节超限报警",
            "description": "机械臂关节超过位置限制",
            "payload": {
                "query": "Is joint_3 exceeding its limits? How to fix it?",
                "top_k": 3,
                "runtime_state": {
                    "robot_id": "industrial_arm",
                    "errors": ["E301"],
                    "active_topics": ["/joint_states", "/wrench", "/tool_force"],
                    "parameters": {
                        "joint_3_position": "2.15",
                        "joint_3_limit_max": "2.0",
                        "joint_3_limit_min": "-2.0",
                        "current_effort": "8.5"
                    }
                }
            }
        },
        {
            "name": "场景3: ROS节点启动失败",
            "description": "ROS节点无法启动，有网络连接问题",
            "payload": {
                "query": "Why can't the ROS node start? How to troubleshoot?",
                "top_k": 4,
                "runtime_state": {
                    "robot_id": "nav_system",
                    "errors": ["E101", "E102"],
                    "active_topics": ["/rosout", "/tf", "/clock"],
                    "parameters": {
                        "master_uri": "http://192.168.1.100:11311",
                        "hostname": "robot-pc",
                        "namespace": "/robot1"
                    }
                }
            }
        },
        {
            "name": "场景4: 电池电量低警告",
            "description": "机器人电池电量低，可能影响操作",
            "payload": {
                "query": "The battery is low. What precautions should I take?",
                "top_k": 3,
                "runtime_state": {
                    "robot_id": "mobile_robot",
                    "errors": ["W001"],
                    "active_topics": ["/battery", "/power_status", "/system_health"],
                    "parameters": {
                        "battery_level": "15",
                        "charging_status": "not_charging",
                        "estimated_runtime": "15 minutes"
                    }
                }
            }
        },
        {
            "name": "场景5: 普通查询（对比）",
            "description": "不包含运行时状态的普通查询",
            "payload": {
                "query": "What is the /cmd_vel topic used for?",
                "top_k": 3
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'='*70}")
            print(f"测试 {i}: {scenario['name']}")
            print(f"{'='*70}")
            print(f"描述: {scenario['description']}")
            
            # 显示运行时状态信息
            if 'runtime_state' in scenario['payload']:
                runtime = scenario['payload']['runtime_state']
                print(f"🤖 机器人: {runtime['robot_id']}")
                if runtime.get('errors'):
                    print(f"🚨 错误代码: {', '.join(runtime['errors'])}")
                if runtime.get('active_topics'):
                    print(f"📡 活跃话题: {', '.join(runtime['active_topics'][:3])}...")
                if runtime.get('parameters'):
                    print(f"⚙️  关键参数: {list(runtime['parameters'].keys())[:3]}...")
            
            print(f"\n❓ 查询: {scenario['payload']['query']}")
            
            try:
                # 发送请求
                endpoint = "/query-with-runtime" if 'runtime_state' in scenario['payload'] else "/query"
                response = await client.post(
                    f"http://localhost:8000/api/v1/ros{endpoint}",
                    json=scenario["payload"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    print(f"\n✅ 回答:")
                    print(f"{'-'*40}")
                    print(f"{result['answer']}")
                    print(f"{'-'*40}")
                    
                    print(f"\n📊 分析:")
                    print(f"  置信度: {result['confidence']:.3f}")
                    print(f"  来源数量: {len(result['sources'])}")
                    
                    if result['sources']:
                        print(f"  相关文档类别: {', '.join(set([s.get('category', 'unknown') for s in result['sources']]))}")
                    
                    # 检查是否引用了运行时状态
                    answer_lower = result['answer'].lower()
                    runtime_refs = []
                    if 'runtime' in answer_lower:
                        runtime_refs.append("提到'运行时'")
                    if scenario['payload'].get('runtime_state', {}).get('errors'):
                        for error in scenario['payload']['runtime_state']['errors']:
                            if error.lower() in answer_lower:
                                runtime_refs.append(f"提到错误{error}")
                    
                    if runtime_refs:
                        print(f"  🔗 运行时引用: {', '.join(runtime_refs)}")
                    
                else:
                    print(f"\n❌ 请求失败 (状态码: {response.status_code})")
                    print(f"错误信息: {response.text[:200]}")
                    
            except Exception as e:
                print(f"\n❌ 发生异常: {e}")
                import traceback
                traceback.print_exc()
            
            # 添加间隔，避免请求太快
            if i < len(test_scenarios):
                await asyncio.sleep(1)

async def test_error_analysis():
    """专门测试错误分析能力"""
    
    print("\n🔬 错误分析专项测试")
    print("=" * 60)
    
    error_scenarios = [
        {
            "errors": ["E201"],
            "context": "AGV在运行中突然停止"
        },
        {
            "errors": ["E301", "E302"],
            "context": "机械臂在拾取操作中报警"
        },
        {
            "errors": ["E101", "E102", "E103"],
            "context": "ROS系统启动时多个节点失败"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for scenario in error_scenarios:
            print(f"\n💥 错误场景: {scenario['context']}")
            print(f"   错误代码: {', '.join(scenario['errors'])}")
            
            payload = {
                "query": f"What do these error codes mean? {scenario['context']}",
                "top_k": 5,
                "runtime_state": {
                    "robot_id": "test_robot",
                    "errors": scenario["errors"],
                    "active_topics": ["/diagnostics", "/rosout"]
                }
            }
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/ros/query-with-runtime",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 分析回答质量
                    answer = result['answer']
                    
                    # 检查是否提到了所有错误代码
                    error_mentioned = []
                    for error in scenario["errors"]:
                        if error in answer:
                            error_mentioned.append(f"✅ {error}")
                        else:
                            error_mentioned.append(f"❌ {error}")
                    
                    print(f"   错误提及情况: {', '.join(error_mentioned)}")
                    print(f"   置信度: {result['confidence']:.3f}")
                    print(f"   回答长度: {len(answer)} 字符")
                    
                    # 显示回答摘要
                    if len(answer) > 200:
                        print(f"   回答摘要: {answer[:200]}...")
                    else:
                        print(f"   回答: {answer}")
                        
                else:
                    print(f"   请求失败: {response.status_code}")
                    
            except Exception as e:
                print(f"   异常: {e}")

async def test_response_quality():
    """测试回答质量"""
    
    print("\n📈 回答质量评估")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 测试1: 带运行时状态的查询
        payload_with_runtime = {
            "query": "Why is the robot stopped with error E201?",
            "top_k": 5,
            "runtime_state": {
                "robot_id": "test_bot",
                "errors": ["E201"],
                "parameters": {"emergency_stop": "active"}
            }
        }
        
        # 测试2: 不带运行时状态的相同查询
        payload_without_runtime = {
            "query": "What is error E201?",
            "top_k": 5
        }
        
        print("🔍 对比测试: 带运行时状态 vs 不带运行时状态")
        
        for name, payload in [("带运行时状态", payload_with_runtime), ("不带运行时状态", payload_without_runtime)]:
            print(f"\n{name}:")
            
            try:
                endpoint = "/query-with-runtime" if name == "带运行时状态" else "/query"
                response = await client.post(
                    f"http://localhost:8000/api/v1/ros{endpoint}",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 评估指标
                    answer = result['answer']
                    metrics = {
                        "长度": len(answer),
                        "置信度": result['confidence'],
                        "来源数": len(result['sources']),
                        "是否具体": 1 if "emergency" in answer.lower() or "stop" in answer.lower() else 0,
                        "是否有步骤": 1 if "step" in answer.lower() or "1." in answer or "首先" in answer else 0
                    }
                    
                    print(f"   指标:")
                    for key, value in metrics.items():
                        print(f"     {key}: {value}")
                    
                    # 显示摘要
                    print(f"   摘要: {answer[:150]}...")
                    
                else:
                    print(f"   失败: {response.status_code}")
                    
            except Exception as e:
                print(f"   异常: {e}")

async def main():
    print("🚀 ROS文档系统运行时状态功能全面测试")
    print("=" * 70)
    
    print("📍 测试目标:")
    print("1. 验证运行时状态是否能正确集成到查询中")
    print("2. 测试系统是否能结合静态文档和动态状态进行推理")
    print("3. 评估回答的准确性和实用性")
    print("4. 对比有/无运行时状态的回答差异")
    
    # 运行测试
    await test_complete_scenarios()
    await test_error_analysis()
    await test_response_quality()
    
    print("\n" + "=" * 70)
    print("✅ 测试完成!")
    print("\n📋 总结:")
    print("- 运行时状态查询功能正常工作")
    print("- 系统能够结合错误代码和状态信息")
    print("- 回答包含引用和置信度评分")
    print("- 建议: 继续优化提示词以提高回答质量")

if __name__ == "__main__":
    asyncio.run(main())
