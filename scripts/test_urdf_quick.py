#!/usr/bin/env python3
"""
URDF快速测试脚本
"""

import requests
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_urdf_data import SIMPLE_ROBOT_URDF

BASE_URL = "http://localhost:8000/api/v1/ros"

def quick_test():
    """快速测试URDF功能"""
    print("🚀 URDF快速测试")
    print("-"*40)
    
    # 1. 导入一个简单的URDF
    print("\n1. 导入简单机器人URDF...")
    payload = {
        "robot_name": "test_simple_robot",
        "urdf_content": SIMPLE_ROBOT_URDF
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/urdf/ingest",
            json=payload,
            timeout=60
        )
        
        print(f"   状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   结果: {result.get('message')}")
            print(f"   Chunks: {result.get('chunk_count')}")
        else:
            print(f"   错误: {response.text[:100]}")
            return
    except Exception as e:
        print(f"   异常: {e}")
        return
    
    # 等待处理
    import time
    time.sleep(1)
    
    # 2. 测试查询
    print("\n2. 测试URDF查询...")
    queries = [
        "Describe the structure of simple_robot with links and joints",
        "What are all the links in simple_robot?",
        "How is simple_robot constructed? List all components."
    ]
    
    for i, query in enumerate(queries):
        print(f"\n   查询 {i+1}: {query}")
        
        payload = {
            "query": query,
            "top_k": 7
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                print(f"   回答: {answer}...")
                print(f"   置信度: {result.get('confidence', 0):.2f}")
            else:
                print(f"   错误: {response.text[:100]}")
                
        except Exception as e:
            print(f"   异常: {e}")
    
    print("\n✅ 快速测试完成！")

if __name__ == "__main__":
    quick_test()