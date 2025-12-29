
"""
API使用示例：如何结合运行时状态进行查询
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/ros"

def query_with_runtime_example():
    """示例：结合运行时状态查询AGV不动的原因"""
    
    payload = {
        "query": "Why is the AGV not moving?",
        "top_k": 5,
        "runtime_state": {
            "robot_id": "agv_robot_01",
            "errors": ["E201"],
            "active_topics": ["/scan", "/odom", "/battery"],
            "parameters": {
                "emergency_stop": "active",
                "speed_limit": "0",
                "battery_level": "15"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/query-with-runtime",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("=== 查询结果 ===")
            print(f"问题: {payload['query']}")
            print(f"运行时状态: {json.dumps(payload['runtime_state'], indent=2)}")
            print(f"回答: {result['answer']}")
            print(f"置信度: {result['confidence']}")
            print(f"来源数量: {len(result['sources'])}")
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"错误: {e}")

def query_joint_limit_example():
    """示例：检查关节是否超限"""
    
    payload = {
        "query": "Is joint_3 exceeding its limits? What should I do?",
        "top_k": 3,
        "runtime_state": {
            "robot_id": "industrial_arm",
            "errors": ["E301"],
            "active_topics": ["/joint_states", "/wrench"],
            "parameters": {
                "joint_3_position": "2.15",
                "joint_3_limit_max": "2.0",
                "joint_3_limit_min": "-2.0"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/query-with-runtime",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n=== 关节超限分析 ===")
            print(f"回答: {result['answer']}")
            print(f"置信度: {result['confidence']}")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    query_with_runtime_example()
    query_joint_limit_example()
