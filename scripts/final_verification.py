
import asyncio
from os import name
import httpx
import json

async def verify_requirements():
    print("✅ Week7/Tue 功能完成验证")
    print("=" * 70)
    
    requirements = [
        {
            "id": "REQ-1",
            "description": "API支持runtime_state参数",
            "test_payload": {
                "query": "Test query",
                "top_k": 3,
                "runtime_state": {
                    "robot_id": "test_robot",
                    "errors": ["TEST001"]
                }
            },
            "expected": "API接受请求并返回200状态码"
        },
        {
            "id": "REQ-2",
            "description": "Runtime state进入prompt",
            "test_payload": {
                "query": "What does error TEST001 mean?",
                "top_k": 3,
                "runtime_state": {
                    "robot_id": "test_robot",
                    "errors": ["TEST001"],
                    "parameters": {"test": "value"}
                }
            },
            "expected": "回答中包含运行时状态信息"
        },
        {
            "id": "REQ-3",
            "description": "RAG结合error/topic给出解释",
            "test_payload": {
                "query": "Why is there a problem?",
                "top_k": 5,
                "runtime_state": {
                    "robot_id": "agv_01",
                    "errors": ["E201"],
                    "active_topics": ["/odom", "/emergency"],
                    "parameters": {"emergency_stop": "active"}
                }
            },
            "expected": "回答结合错误代码和话题状态进行解释"
        },
        {
            "id": "REQ-4",
            "description": "回答包含citation + confidence",
            "test_payload": {
                "query": "Explain error E201",
                "top_k": 3,
                "runtime_state": {
                    "robot_id": "test_bot",
                    "errors": ["E201"]
                }
            },
            "expected": "回答包含引用和置信度分数"
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for req in requirements:
            print(f"\n🔍 验证: {req['id']} - {req['description']}")
            print(f"   期望: {req['expected']}")
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/ros/query-with-runtime",
                    json=req["test_payload"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 检查具体要求
                    passed = True
                    checks = []
                    
                    # REQ-1: API接受请求
                    checks.append(("API返回200", response.status_code == 200))
                    
                    # REQ-2: 运行时状态在回答中
                    if req["id"] == "REQ-2":
                        answer_lower = result["answer"].lower()
                        has_runtime_ref = any([
                            "test001" in answer_lower,
                            "runtime" in answer_lower,
                            "robot" in answer_lower
                        ])
                        checks.append(("回答引用运行时状态", has_runtime_ref))
                    
                    # REQ-3: 结合error/topic解释
                    if req["id"] == "REQ-3":
                        answer_lower = result["answer"].lower()
                        has_error_ref = "e201" in answer_lower
                        has_explanation = any(word in answer_lower for word in ["because", "reason", "cause", "due to"])
                        checks.append(("提及错误E201", has_error_ref))
                        checks.append(("提供解释", has_explanation))
                    
                    # REQ-4: 包含citation和confidence
                    if req["id"] == "REQ-4":
                        has_citation = "context" in result["answer"].lower() or "source" in result["answer"].lower()
                        has_confidence = "confidence" in result
                        checks.append(("包含引用", has_citation))
                        checks.append(("包含置信度", has_confidence))
                        checks.append(("置信度有效", 0 <= result["confidence"] <= 1))
                    
                    # 显示检查结果
                    all_passed = all(check[1] for check in checks)
                    
                    if all_passed:
                        print(f"   ✅ 通过")
                        for check_name, check_result in checks:
                            print(f"      ✓ {check_name}")
                    else:
                        print(f"   ❌ 部分失败")
                        for check_name, check_result in checks:
                            status = "✓" if check_result else "✗"
                            print(f"      {status} {check_name}")
                    
                    results.append({
                        "requirement": req["id"],
                        "passed": all_passed,
                        "confidence": result.get("confidence", 0),
                        "answer_length": len(result["answer"]),
                        "sources_count": len(result.get("sources", []))
                    })
                    
                else:
                    print(f"   ❌ API请求失败: {response.status_code}")
                    print(f"      错误: {response.text[:100]}")
                    results.append({
                        "requirement": req["id"],
                        "passed": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"   ❌ 发生异常: {e}")
                results.append({
                    "requirement": req["id"],
                    "passed": False,
                    "error": str(e)
                })
    
    # 生成总结报告
    print(f"\n" + "="*70)
    print("📊 验证总结报告")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    print(f"总计要求: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if passed == total:
        print(f"\n🎉 恭喜！所有Week7/Tue要求都已满足！")
    else:
        print(f"\n⚠️  部分要求未通过，需要进一步调试")
    
    # 详细结果
    print(f"\n📋 详细结果:")
    for result in results:
        status = "✅" if result["passed"] else "❌"
        print(f"  {status} {result['requirement']}", end="")
        if result["passed"]:
            print(f" - 置信度: {result.get('confidence', 0):.3f}, 回答长度: {result.get('answer_length', 0)}")
        else:
            print(f" - 错误: {result.get('error', 'Unknown')}")

async def test_real_world_scenarios():
    """测试真实世界场景"""
    
    print(f"\n" + "="*70)
    print("🌍 真实世界场景测试")
    print("="*70)
    
    scenarios = [
        {
            "name": "现场问题: AGV不动了",
            "description": "工程师发现AGV停止不动，控制台显示E201错误",
            "query": "AGV不动了，可能原因是什么？应该怎么处理？",
            "runtime_state": {
                "robot_id": "车间AGV-03",
                "errors": ["E201"],
                "active_topics": ["/emergency_status", "/battery", "/motor_status"],
                "parameters": {
                    "location": "装载站A",
                    "task": "物料搬运",
                    "emergency_button": "pressed"
                }
            }
        },
        {
            "name": "现场问题: 关节超限报警",
            "description": "机械臂操作时触发关节限位报警",
            "query": "当前joint_3超限了吗？怎么解决？",
            "runtime_state": {
                "robot_id": "焊接机械臂-01",
                "errors": ["E301"],
                "active_topics": ["/joint_states", "/collision_warning", "/tool_forces"],
                "parameters": {
                    "joint_3_position": "2.3",
                    "joint_3_limit": "2.0",
                    "operation_mode": "自动焊接"
                }
            }
        },
        {
            "name": "现场问题: ROS节点启动失败",
            "description": "系统启动时ROS核心节点无法启动",
            "query": "为什么ROS节点启动失败？E101报错代表什么？",
            "runtime_state": {
                "robot_id": "自主导航机器人",
                "errors": ["E101", "E102"],
                "active_topics": ["/rosout", "/tf_static"],
                "parameters": {
                    "master_uri": "http://10.0.0.1:11311",
                    "hostname": "robot-main",
                    "network_status": "unstable"
                }
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=40.0) as client:
        for scenario in scenarios:
            print(f"\n🔧 场景: {scenario['name']}")
            print(f"   描述: {scenario['description']}")
            print(f"   查询: {scenario['query']}")
            
            payload = {
                "query": scenario["query"],
                "top_k": 5,
                "runtime_state": scenario["runtime_state"]
            }
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/ros/query-with-runtime",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 分析回答质量
                    answer = result["answer"]
                    
                    # 检查关键要素
                    quality_indicators = {
                        "错误代码提及": any(error.lower() in answer.lower() for error in scenario["runtime_state"]["errors"]),
                        "提供解决方案": any(word in answer.lower() for word in ["step", "solution", "fix", "resolve", "check", "verify"]),
                        "引用文档": "context" in answer.lower() or "source" in answer.lower() or "[" in answer,
                        "具体建议": len(answer) > 200,  # 回答有一定长度
                        "置信度合理": 0.3 <= result["confidence"] <= 1.0
                    }
                    
                    print(f"   📊 质量指标:")
                    for indicator, value in quality_indicators.items():
                        status = "✅" if value else "⚠️ "
                        print(f"      {status} {indicator}")
                    
                    print(f"   🔍 回答摘要:")
                    if len(answer) > 300:
                        print(f"      {answer[:300]}...")
                    else:
                        print(f"      {answer}")
                        
                    print(f"   📈 置信度: {result['confidence']:.3f}")
                    print(f"   📚 来源数: {len(result.get('sources', []))}")
                    
                else:
                    print(f"   ❌ 请求失败: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 异常: {e}")

async def test_api_endpoints():
    """测试所有API端点"""
    
    print(f"\n" + "="*70)
    print("🌐 API端点测试")
    print("="*70)
    
    endpoints = [
        ("GET", "/", "根端点"),
        ("GET", "/health", "健康检查"),
        ("GET", "/api/v1/ros/history", "查询历史"),
        ("POST", "/api/v1/ros/query", "普通查询"),
        ("POST", "/api/v1/ros/query-with-runtime", "运行时查询"),
        ("POST", "/api/v1/ros/topics/ingest", "导入ROS Topics"),
        ("POST", "/api/v1/ros/urdf/ingest", "导入URDF"),
        ("POST", "/api/v1/ros/operation/ingest", "导入安全操作")
    ]
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        for method, endpoint, description in endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"http://localhost:8000{endpoint}")
                else:  # POST
                    # 对于POST端点，发送简单测试数据或检查端点是否存在
                    if "query" in endpoint:
                        test_data = {"query": "test", "top_k": 1}
                        if "runtime" in endpoint:
                            test_data["runtime_state"] = {"robot_id": "test"}
                        response = await client.post(
                            f"http://localhost:8000{endpoint}",
                            json=test_data
                        )
                    else:
                        # 其他POST端点只检查是否存在
                        response = await client.get(f"http://localhost:8000{endpoint}")
                
                status = "✅" if response.status_code in [200, 405] else "❌"
                print(f"{status} {method} {endpoint:30} - {description:15} (状态码: {response.status_code})")
                
            except Exception as e:
                print(f"❌ {method} {endpoint:30} - {description:15} (错误: {e})")

async def generate_documentation():
    """生成使用文档"""
    
    print(f"\n" + "="*70)
    print("📚 系统使用文档")
    print("="*70)
    
    docs = """
        🎯 系统功能概述
        ---------------
        ROS文档系统现在支持运行时状态查询，能够结合：
        1. 静态知识（ROS文档、URDF、安全操作指南）
        2. 动态状态（错误代码、活跃话题、运行参数）
        3. 实时推理（基于当前状态的诊断和建议）

        🚀 核心端点
        ----------
        1. 普通查询: POST /api/v1/ros/query
        - 仅基于静态文档的查询
        
        2. 运行时查询: POST /api/v1/ros/query-with-runtime
        - 结合运行时状态的增强查询
        - 支持故障诊断和实时建议

        📋 请求格式示例
        ---------------
        普通查询:
        ```json
        {
        "query": "What is error E201?",
        "top_k": 5
        }"""
    print(docs)

async def main():
    print("🎯 ROS文档系统 - Week7/Tue 完成验证")
    print("=" * 70)
    # 运行验证
    await verify_requirements()

    # 测试真实场景
    await test_real_world_scenarios()

    # 测试API端点
    await test_api_endpoints()

    # 生成文档
    await generate_documentation()

    print(f"\n" + "="*70)
    print("🏆 验证完成总结")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main()) 