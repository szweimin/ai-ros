import requests
import json
from datetime import datetime

class EdgeAdapterClient:
    """Edge Adapter 客户端示例"""
    
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def send_snapshot(self, snapshot_data):
        """发送运行时快照"""
        url = f"{self.base_url}/api/v1/runtime/snapshot"
        
        response = requests.post(
            url,
            headers=self.headers,
            json=snapshot_data,
            timeout=10
        )
        
        return response.json()
    
    @staticmethod
    def create_ros_snapshot(robot_id, errors=None, joint_states=None):
        """创建ROS2快照"""
        return {
            "robot_id": robot_id,
            "model": "AGV_X1",
            "firmware": "v2.1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "errors": errors or [],
            "joint_states": joint_states or {"wheel_left": 0.0, "wheel_right": 0.0},
            "active_topics": ["/scan", "/odom", "/cmd_vel"],
            "source": "ros2"
        }

# 使用示例
if __name__ == "__main__":
    client = EdgeAdapterClient(
        base_url="http://localhost:8000",
        api_key="edge-adapter-ros-key"
    )
    
    # 模拟正常状态
    snapshot = client.create_ros_snapshot("agv_01")
    result = client.send_snapshot(snapshot)
    print(f"Normal snapshot: {result}")
    
    # 模拟错误状态
    error_snapshot = client.create_ros_snapshot(
        robot_id="agv_02",
        errors=["E201", "E305"],
        joint_states={"wheel_left": 12.5, "wheel_right": 0.0}
    )
    result = client.send_snapshot(error_snapshot)
    print(f"Error snapshot: {result}")