#!/usr/bin/env python3
"""
URDF文档API测试脚本
测试 /api/v1/ros/urdf/ingest 和查询功能
"""

import requests
import json
import time
import sys
import os

# 添加测试数据路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_urdf_data import get_test_urdf_cases, URDF_TEST_QUERIES

BASE_URL = "http://localhost:8000/api/v1/ros"

def print_separator(title=""):
    """打印分隔符"""
    print("\n" + "="*60)
    if title:
        print(f"  {title}")
        print("="*60)

def test_health():
    """测试健康检查"""
    print_separator("1. 健康检查")
    try:
        response = requests.get(f"http://localhost:8000/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def ingest_single_urdf(robot_name: str, urdf_content: str) -> bool:
    """
    导入单个URDF文档
    
    Args:
        robot_name: 机器人名称
        urdf_content: URDF内容
        
    Returns:
        是否成功
    """
    print(f"导入机器人: {robot_name}")
    
    payload = {
        "robot_name": robot_name,
        "urdf_content": urdf_content
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/urdf/ingest",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 成功")
            print(f"     消息: {result.get('message')}")
            print(f"     chunk数量: {result.get('chunk_count', 0)}")
            return True
        else:
            print(f"   ❌ 失败")
            print(f"     响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

def test_urdf_ingestion():
    """测试URDF导入"""
    print_separator("2. URDF文档导入测试")
    
    test_cases = get_test_urdf_cases()
    success_count = 0
    
    print(f"开始导入 {len(test_cases)} 个URDF文档...")
    
    for i, (key, data) in enumerate(test_cases.items()):
        print(f"\n[{i+1}/{len(test_cases)}] {data['name']}")
        
        success = ingest_single_urdf(data['name'], data['urdf'])
        
        if success:
            success_count += 1
            
        # 等待一下，避免请求过快
        if i < len(test_cases) - 1:
            time.sleep(1)
    
    print(f"\n✅ 导入完成: {success_count}/{len(test_cases)} 成功")
    return success_count > 0

def test_urdf_queries():
    """测试URDF相关查询"""
    print_separator("3. URDF知识查询测试")
    
    success_count = 0
    total_queries = len(URDF_TEST_QUERIES)
    
    print(f"开始执行 {total_queries} 个URDF相关查询...")
    
    for i, test_query in enumerate(URDF_TEST_QUERIES):
        print(f"\n[{i+1}/{total_queries}] 查询: {test_query['query']}")
        
        payload = {
            "query": test_query["query"],
            "top_k": 3
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                confidence = result.get('confidence', 0)
                
                print(f"   ✅ 查询成功")
                print(f"     回答: {answer[:150]}...")
                print(f"     置信度: {confidence:.3f}")
                print(f"     结果数: {result.get('result_count', 0)}")
                
                # 检查是否包含期望的关键词
                expected_keywords = test_query['expected_keywords']
                found_keywords = []
                for keyword in expected_keywords:
                    if keyword.lower() in answer.lower():
                        found_keywords.append(keyword)
                
                if found_keywords:
                    print(f"     找到关键词: {', '.join(found_keywords)}")
                else:
                    print(f"     ⚠️  未找到期望关键词: {', '.join(expected_keywords)}")
                
                success_count += 1
            else:
                print(f"   ❌ 查询失败")
                print(f"     响应: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    print(f"\n✅ 查询完成: {success_count}/{total_queries} 成功 ({success_count/total_queries*100:.1f}%)")
    return success_count > 0

def test_specific_urdf_analysis():
    """测试特定的URDF结构分析"""
    print_separator("4. 特定URDF结构分析")
    
    specific_queries = [
        {
            "query": "Count the number of joints in the industrial arm",
            "description": "统计工业机械臂的关节数量"
        },
        {
            "query": "What is the mass of the mobile robot chassis?",
            "description": "查询移动机器人底盘的质量"
        },
        {
            "query": "List all sensor types on the mobile robot with sensors",
            "description": "列出带传感器移动机器人的所有传感器类型"
        },
        {
            "query": "What are the different joint types used in these robots?",
            "description": "查询机器人中使用的不同关节类型"
        },
        {
            "query": "How are the drone propellers connected to the motors?",
            "description": "无人机螺旋桨如何连接到电机"
        }
    ]
    
    success_count = 0
    
    for i, query in enumerate(specific_queries):
        print(f"\n[{i+1}/{len(specific_queries)}] {query['description']}")
        print(f"   查询: {query['query']}")
        
        payload = {
            "query": query["query"],
            "top_k": 5
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 回答: {result.get('answer', '')[:120]}...")
                success_count += 1
            else:
                print(f"   ❌ 失败")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    print(f"\n✅ 特定分析完成: {success_count}/{len(specific_queries)} 成功")
    return success_count > 0

def test_error_cases():
    """测试URDF错误情况"""
    print_separator("5. 错误情况测试")
    
    error_cases = [
        {
            "name": "空的URDF内容",
            "payload": {
                "robot_name": "empty_robot",
                "urdf_content": ""
            },
            "expected_error": True
        },
        {
            "name": "无效的XML格式",
            "payload": {
                "robot_name": "invalid_robot",
                "urdf_content": "This is not valid XML"
            },
            "expected_error": True
        },
        {
            "name": "缺少robot_name",
            "payload": {
                "urdf_content": "<robot></robot>"
            },
            "expected_error": True
        },
        {
            "name": "有效的URDF但没有joints",
            "payload": {
                "robot_name": "no_joints_robot",
                "urdf_content": "<?xml version='1.0'?><robot name='no_joints'><link name='base'/></robot>"
            },
            "expected_error": False  # 应该成功，只是没有joints
        }
    ]
    
    for case in error_cases:
        print(f"\n测试: {case['name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/urdf/ingest",
                json=case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   状态码: {response.status_code}")
            
            if case['expected_error']:
                if response.status_code >= 400:
                    print(f"   ✅ 如预期般失败")
                else:
                    print(f"   ⚠️  预期失败但成功")
            else:
                if response.status_code == 200:
                    print(f"   ✅ 如预期般成功")
                else:
                    print(f"   ⚠️  预期成功但失败: {response.text[:100]}")
                    
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    return True

def test_query_history():
    """测试查询历史"""
    print_separator("6. 查询历史测试")
    
    try:
        response = requests.get(
            f"{BASE_URL}/history?limit=10",
            timeout=10
        )
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ 获取到 {len(history)} 条查询历史")
            
            # 显示URDF相关的查询
            urdf_queries = []
            for item in history:
                query = item.get('query', '').lower()
                if any(keyword in query for keyword in ['joint', 'link', 'urdf', 'robot', 'sensor']):
                    urdf_queries.append(item)
            
            if urdf_queries:
                print(f"   其中 {len(urdf_queries)} 条是URDF相关查询:")
                for i, item in enumerate(urdf_queries[:3]):
                    query_short = item['query'][:50] + "..." if len(item['query']) > 50 else item['query']
                    print(f"   {i+1}. {query_short}")
            
            return True
        else:
            print(f"❌ 获取历史失败: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 URDF文档系统测试套件")
    print("="*60)
    
    # 检查服务是否运行
    if not test_health():
        print("\n❌ 服务未启动，请先运行:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print("\n等待服务准备...")
    time.sleep(2)
    
    test_results = {}
    
    # 运行测试
    test_results['urdf_ingestion'] = test_urdf_ingestion()
    test_results['urdf_queries'] = test_urdf_queries()
    test_results['specific_analysis'] = test_specific_urdf_analysis()
    test_results['error_cases'] = test_error_cases()
    test_results['query_history'] = test_query_history()
    
    # 汇总结果
    print_separator("测试结果汇总")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"总测试数: {total_tests}")
    print(f"通过数: {passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有URDF测试通过！系统运行正常。")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，请检查问题。")

if __name__ == "__main__":
    main()