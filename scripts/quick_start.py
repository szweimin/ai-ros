
#!/usr/bin/env python3
"""
ROS文档系统快速使用示例
"""

import requests
import json

def print_section(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def quick_demo():
    """快速演示"""
    
    base_url = "http://localhost:8000"
    
    print_section("ROS文档系统快速演示")
    
    # 1. 检查服务状态
    print("1. 检查服务状态...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print(f"   ✅ 服务正常: {response.json()}")
        else:
            print(f"   ❌ 服务异常: {response.status_code}")
            return
    except:
        print("   ❌ 无法连接到服务")
        print("   请先启动服务: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # 2. 演示运行时查询
    print_section("2. 运行时状态查询演示")
    
    examples = [
        {
            "name": "AGV紧急停止",
            "query": "AGV突然停止不动了，可能是什么原因？",
            "runtime": {
                "robot_id": "agv_01",
                "errors": ["E201"],
                "parameters": {"emergency_stop": "active"}
            }
        },
        {
            "name": "关节超限",
            "query": "机械臂关节超限报警怎么办？",
            "runtime": {
                "robot_id": "arm_01",
                "errors": ["E301"],
                "parameters": {"joint_position": "2.3", "joint_limit": "2.0"}
            }
        }
    ]
    
    for example in examples:
        print(f"\n🔧 {example['name']}:")
        print(f"   查询: {example['query']}")
        
        payload = {
            "query": example["query"],
            "top_k": 3,
            "runtime_state": example["runtime"]
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/v1/ros/query-with-runtime",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 简洁显示结果
                print(f"   💡 回答摘要: {result['answer'][:150]}...")
                print(f"   📊 置信度: {result['confidence']:.2f}")
                print(f"   📚 来源: {len(result['sources'])} 个")
                
            else:
                print(f"   ❌ 查询失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
    
    # 3. 显示API信息
    print_section("3. API端点信息")
    
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            info = response.json()
            print("可用端点:")
            for name, endpoint in info.get("endpoints", {}).items():
                print(f"  • {name}: {endpoint}")
    except:
        pass
    
    # 4. 使用建议
    print_section("4. 使用建议")
    print("💡 最佳实践:")
    print("  1. 提供完整的运行时状态信息")
    print("  2. 明确描述问题现象")
    print("  3. 包含相关错误代码")
    print("  4. 设置合适的top_k值（3-10）")
    
    print("\n🚀 快速测试命令:")
    print("""  curl -X POST http://localhost:8000/api/v1/ros/query-with-runtime \\
    -H "Content-Type: application/json" \\
    -d '{
      "query": "机器人不动了怎么办？",
      "top_k": 3,
      "runtime_state": {
        "robot_id": "test_robot",
        "errors": ["E201"]
      }
    }'""")

if __name__ == "__main__":
    quick_demo()
