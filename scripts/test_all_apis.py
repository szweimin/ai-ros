#!/usr/bin/env python3
"""
完整的ROS文档系统API测试
"""

import requests
import json
import time
import sys
import os

# 服务器地址
BASE_URL = "http://localhost:8000/api/v1/ros"

def print_separator(title=""):
    """打印分隔符"""
    print("\n" + "="*60)
    if title:
        print(f"  {title}")
        print("="*60)

def test_health_check():
    """测试健康检查"""
    print_separator("1. 健康检查测试")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_topics_ingest():
    """测试ROS Topics导入"""
    print_separator("2. ROS Topics导入测试")
    
    test_data = {
        "topics": [
            {
                "topic": "/cmd_vel",
                "type": "geometry_msgs/Twist",
                "description": "Velocity command for AGV movement control",
                "rate": "10Hz",
                "publisher": "move_base",
                "subscribers": ["base_controller", "safety_monitor", "navigation_node"]
            },
            {
                "topic": "/odom",
                "type": "nav_msgs/Odometry", 
                "description": "Odometry information providing pose and velocity",
                "rate": "50Hz",
                "publisher": "wheel_odometry",
                "subscribers": ["localization", "slam_gmapping", "navigation"]
            },
            {
                "topic": "/scan",
                "type": "sensor_msgs/LaserScan",
                "description": "Laser scan data from LiDAR sensor",
                "rate": "20Hz",
                "publisher": "hokuyo_node",
                "subscribers": ["obstacle_detection", "mapping", "navigation"]
            },
            {
                "topic": "/imu/data",
                "type": "sensor_msgs/Imu",
                "description": "Inertial Measurement Unit data (acceleration, orientation)",
                "rate": "100Hz",
                "publisher": "imu_driver",
                "subscribers": ["ekf_localization", "state_estimator"]
            },
            {
                "topic": "/joint_states",
                "type": "sensor_msgs/JointState",
                "description": "Robot joint positions, velocities and efforts",
                "rate": "30Hz",
                "publisher": "robot_state_publisher",
                "subscribers": ["moveit", "controller_manager", "diagnostics"]
            }
        ]
    }
    
    try:
        print(f"发送 {len(test_data['topics'])} 个ROS Topics...")
        response = requests.post(
            f"{BASE_URL}/topics/ingest",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 导入成功")
            print(f"   消息: {result.get('message')}")
            print(f"   chunk数量: {result.get('chunk_count', 0)}")
            
            # 显示详细信息
            details = result.get('details', {})
            if details:
                print(f"   详细信息: {details.get('status')} - {details.get('message')}")
            
            # 等待数据处理完成
            print("等待数据索引完成...")
            time.sleep(2)
            return True
        else:
            print(f"❌ 导入失败")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_urdf_ingest():
    """测试URDF导入"""
    print_separator("3. URDF导入测试")
    
    # 一个简单的机器人URDF示例
    urdf_content = """<?xml version="1.0"?>
<robot name="agv_robot">
  
  <!-- Links (physical parts) -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.6 0.4 0.2"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 0.8 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <box size="0.6 0.4 0.2"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="10.0"/>
      <inertia ixx="0.4" ixy="0.0" ixz="0.0" iyy="0.4" iyz="0.0" izz="0.2"/>
    </inertial>
  </link>
  
  <link name="left_wheel">
    <visual>
      <geometry>
        <cylinder length="0.1" radius="0.1"/>
      </geometry>
      <material name="black">
        <color rgba="0 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <link name="right_wheel">
    <visual>
      <geometry>
        <cylinder length="0.1" radius="0.1"/>
      </geometry>
      <material name="black">
        <color rgba="0 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <!-- Joints (connections between links) -->
  <joint name="base_to_left_wheel" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="0.0 0.2 0.0" rpy="0 1.5708 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="100" velocity="10"/>
  </joint>
  
  <joint name="base_to_right_wheel" type="continuous">
    <parent link="base_link"/>
    <child link="right_wheel"/>
    <origin xyz="0.0 -0.2 0.0" rpy="0 1.5708 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="100" velocity="10"/>
  </joint>
  
  <joint name="camera_mount" type="fixed">
    <parent link="base_link"/>
    <child link="camera_link"/>
    <origin xyz="0.3 0.0 0.15" rpy="0 0 0"/>
  </joint>
  
  <link name="camera_link">
    <visual>
      <geometry>
        <box size="0.05 0.05 0.05"/>
      </geometry>
      <material name="red">
        <color rgba="0.8 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <!-- LiDAR sensor -->
  <joint name="lidar_mount" type="fixed">
    <parent link="base_link"/>
    <child link="lidar_link"/>
    <origin xyz="0.0 0.0 0.25" rpy="0 0 0"/>
  </joint>
  
  <link name="lidar_link">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.08"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
  </link>
  
</robot>"""
    
    test_data = {
        "robot_name": "agv_robot",
        "urdf_content": urdf_content
    }
    
    try:
        print(f"发送AGV机器人URDF...")
        response = requests.post(
            f"{BASE_URL}/urdf/ingest",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ URDF导入成功")
            print(f"   消息: {result.get('message')}")
            print(f"   chunk数量: {result.get('chunk_count', 0)}")
            
            # 等待数据处理完成
            print("等待数据索引完成...")
            time.sleep(2)
            return True
        else:
            print(f"❌ URDF导入失败")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_ros_query():
    """测试ROS知识库查询"""
    print_separator("4. ROS知识库查询测试")
    
    test_queries = [
        {
            "query": "Which ROS topic controls AGV velocity?",
            "top_k": 3,
            "description": "测试速度控制topic查询"
        },
        {
            "query": "What are the joints in the AGV robot?",
            "top_k": 5,
            "description": "测试机器人关节查询"
        },
        {
            "query": "How to get odometry data in ROS?",
            "top_k": 3,
            "description": "测试里程计数据查询"
        },
        {
            "query": "What sensors are available on the AGV?",
            "top_k": 3,
            "description": "测试传感器查询"
        },
        {
            "query": "Tell me about the laser scan topic",
            "top_k": 2,
            "description": "测试激光雷达topic查询"
        },
        {
            "query": "What is the structure of the AGV robot?",
            "top_k": 4,
            "description": "测试机器人结构查询"
        }
    ]
    
    success_count = 0
    total_queries = len(test_queries)
    
    for i, test_query in enumerate(test_queries):
        print(f"\n查询 {i+1}/{total_queries}: {test_query['description']}")
        print(f"问题: {test_query['query']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={
                    "query": test_query["query"],
                    "top_k": test_query["top_k"]
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 查询成功")
                print(f"   回答: {result.get('answer', '')[:150]}...")
                print(f"   置信度: {result.get('confidence', 0):.2f}")
                print(f"   结果数量: {result.get('result_count', 0)}")
                
                # 显示来源信息
                sources = result.get('sources', [])
                if sources:
                    print(f"   来源:")
                    for j, source in enumerate(sources[:2]):  # 只显示前两个来源
                        source_text = source.get('text', '')[:80]
                        category = source.get('metadata', {}).get('category', 'unknown')
                        score = source.get('score', 0)
                        print(f"     [{j+1}] {category} (score: {score:.3f}): {source_text}...")
                
                success_count += 1
            else:
                print(f"❌ 查询失败")
                print(f"   响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    print(f"\n✅ 查询成功率: {success_count}/{total_queries} ({success_count/total_queries*100:.1f}%)")
    return success_count > 0

def test_query_history():
    """测试查询历史"""
    print_separator("5. 查询历史测试")
    
    try:
        response = requests.get(
            f"{BASE_URL}/history?limit=5",
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ 获取到 {len(history)} 条查询历史")
            for i, item in enumerate(history[:3]):  # 只显示前3条
                query_short = item['query'][:50] + "..." if len(item['query']) > 50 else item['query']
                print(f"   {i+1}. {query_short}")
            return True
        else:
            print(f"❌ 获取历史失败")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_error_cases():
    """测试错误情况"""
    print_separator("6. 错误情况测试")
    
    # 测试1: 空的topics列表
    print("\n测试1: 空的topics列表")
    try:
        response = requests.post(
            f"{BASE_URL}/topics/ingest",
            json={"topics": []},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:100]}...")
    except Exception as e:
        print(f"   异常: {e}")
    
    # 测试2: 无效的URDF
    print("\n测试2: 无效的URDF")
    try:
        response = requests.post(
            f"{BASE_URL}/urdf/ingest",
            json={
                "robot_name": "test_robot",
                "urdf_content": "invalid xml content"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:100]}...")
    except Exception as e:
        print(f"   异常: {e}")
    
    # 测试3: 空的查询
    print("\n测试3: 空的查询")
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json={"query": "", "top_k": 5},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:100]}...")
    except Exception as e:
        print(f"   异常: {e}")
    
    return True

def main():
    """主测试函数"""
    print("🚀 ROS文档系统API测试")
    print("="*60)
    
    # 检查服务是否运行
    if not test_health_check():
        print("\n❌ 服务未启动，请先运行:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    test_results = {}
    
    # 运行测试
    test_results['topics_ingest'] = test_topics_ingest()
    test_results['urdf_ingest'] = test_urdf_ingest()
    test_results['ros_query'] = test_ros_query()
    test_results['query_history'] = test_query_history()
    test_results['error_cases'] = test_error_cases()
    
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
        print("\n🎉 所有测试通过！系统运行正常。")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，请检查问题。")

if __name__ == "__main__":
    main()