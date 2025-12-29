"""
导入测试文档数据，包含错误代码和安全操作
"""
import asyncio
import httpx
import json

async def import_test_documents():
    """导入测试文档到系统"""
    
    base_url = "http://localhost:8000/api/v1/ros"
    
    # 1. 导入安全操作文档（包含错误代码）
    safety_operations = {
        "operations": [
            {
                "title": "Emergency Stop Error E201",
                "content": "Error code E201 indicates an emergency stop condition. When this error is active, all movement is inhibited for safety reasons. Check the emergency stop button, safety gates, and enable switches.",
                "category": "safety",
                "procedure_steps": [
                    "1. Check physical emergency stop button",
                    "2. Verify safety gate sensors",
                    "3. Reset error from controller",
                    "4. Restart AGV system"
                ]
            },
            {
                "title": "Joint Limit Error E301",
                "content": "Error code E301 indicates a joint position limit violation. The joint has exceeded its maximum or minimum allowed position. Check joint calibration and movement parameters.",
                "category": "safety",
                "procedure_steps": [
                    "1. Check current joint position",
                    "2. Verify joint limit parameters",
                    "3. Move joint to safe position",
                    "4. Reset error and restart"
                ]
            },
            {
                "title": "ROS Node Error E101/E102",
                "content": "Error codes E101 and E102 indicate ROS node startup failures. E101: Cannot connect to ROS master. E102: Node name conflict or parameter error.",
                "category": "operation",
                "procedure_steps": [
                    "1. Check ROS master is running",
                    "2. Verify network connectivity",
                    "3. Check for duplicate node names",
                    "4. Review launch file parameters"
                ]
            }
        ]
    }
    
    # 2. 导入ROS Topics
    ros_topics = {
        "topics": [
            {
                "topic": "/cmd_vel",
                "type": "geometry_msgs/Twist",
                "description": "Velocity command topic for robot movement. Publishes linear and angular velocity commands.",
                "rate": "10 Hz",
                "publisher": "move_base",
                "subscribers": ["base_controller", "safety_monitor"]
            },
            {
                "topic": "/odom",
                "type": "nav_msgs/Odometry",
                "description": "Odometry information providing robot position and orientation.",
                "rate": "20 Hz",
                "publisher": "wheel_odometry"
            },
            {
                "topic": "/joint_states",
                "type": "sensor_msgs/JointState",
                "description": "Joint positions, velocities and efforts for robotic arms.",
                "rate": "50 Hz",
                "publisher": "joint_state_publisher"
            }
        ]
    }
    
    # 3. 导入URDF文档
    urdf_example = """<?xml version="1.0"?>
<robot name="agv_robot">
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.5 0.3 0.2"/>
      </geometry>
    </visual>
  </link>
  
  <link name="wheel_left">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.1"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="wheel_left_joint" type="continuous">
    <parent link="base_link"/>
    <child link="wheel_left"/>
    <origin xyz="0.2 0.15 0"/>
  </joint>
  
  <joint name="joint_3" type="revolute">
    <parent link="base_link"/>
    <child link="sensor_mount"/>
    <limit lower="-2.0" upper="2.0" effort="10" velocity="1.0"/>
  </joint>
</robot>"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("📥 开始导入测试文档...")
        
        try:
            # 导入安全操作文档
            print("1. 导入安全操作文档...")
            response = await client.post(
                f"{base_url}/operation/ingest",
                json=safety_operations
            )
            
            if response.status_code == 200:
                print(f"   ✅ 成功导入: {response.json()}")
            else:
                print(f"   ❌ 导入失败: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 发生错误: {e}")
        
        try:
            # 导入ROS Topics
            print("\n2. 导入ROS Topics...")
            response = await client.post(
                f"{base_url}/topics/ingest",
                json=ros_topics
            )
            
            if response.status_code == 200:
                print(f"   ✅ 成功导入: {response.json()}")
            else:
                print(f"   ❌ 导入失败: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 发生错误: {e}")
        
        try:
            # 导入URDF
            print("\n3. 导入URDF文档...")
            urdf_payload = {
                "robot_name": "agv_robot",
                "urdf_content": urdf_example
            }
            
            response = await client.post(
                f"{base_url}/urdf/ingest",
                json=urdf_payload
            )
            
            if response.status_code == 200:
                print(f"   ✅ 成功导入: {response.json()}")
            else:
                print(f"   ❌ 导入失败: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 发生错误: {e}")
        
        print("\n📊 导入完成!")

async def test_after_import():
    """导入后测试查询"""
    
    print("\n🧪 导入后测试查询...")
    
    test_queries = [
        {
            "name": "AGV不动了，有E201错误",
            "payload": {
                "query": "Why is the AGV not moving? What does error E201 mean?",
                "top_k": 5,
                "runtime_state": {
                    "robot_id": "agv_robot_01",
                    "errors": ["E201"],
                    "active_topics": ["/scan", "/odom", "/battery"],
                    "parameters": {"emergency_stop": "active", "speed_limit": "0"}
                }
            }
        },
        {
            "name": "查询/cmd_vel话题",
            "payload": {
                "query": "What is the purpose of the /cmd_vel topic?",
                "top_k": 3
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in test_queries:
            print(f"\n{'='*50}")
            print(f"测试: {test['name']}")
            print(f"{'='*50}")
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/ros/query-with-runtime",
                    json=test["payload"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"查询: {test['payload']['query']}")
                    
                    if 'runtime_state' in test['payload']:
                        print(f"运行时状态: 有 ({len(test['payload']['runtime_state'].get('errors', []))} 个错误)")
                    
                    print(f"\n回答: {result['answer']}")
                    print(f"置信度: {result['confidence']:.2f}")
                    print(f"来源: {len(result['sources'])} 个")
                else:
                    print(f"请求失败: {response.text}")
                    
            except Exception as e:
                print(f"错误: {e}")

async def main():
    """主函数"""
    print("🚀 ROS文档系统 - 数据导入和测试")
    print("=" * 60)
    
    # 导入测试数据
    await import_test_documents()
    
    # 等待一下让数据处理完成
    import asyncio
    await asyncio.sleep(2)
    
    # 测试查询
    await test_after_import()
    
    print("\n✅ 所有测试完成!")

if __name__ == "__main__":
    asyncio.run(main())