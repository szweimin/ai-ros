#!/usr/bin/env python3
"""
URDF文档测试数据
提供各种URDF/Xacro示例，用于测试ROS文档系统
"""

# ===================== 基础URDF示例 =====================

SIMPLE_ROBOT_URDF = """<?xml version="1.0"?>
<robot name="simple_robot">
  
  <!-- Base Link -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.5 0.3 0.2"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 0.8 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <box size="0.5 0.3 0.2"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="5.0"/>
      <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.05"/>
    </inertial>
  </link>
  
  <!-- Wheel Links and Joints -->
  <link name="left_wheel">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.1"/>
      </geometry>
      <material name="black">
        <color rgba="0 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <link name="right_wheel">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.1"/>
      </geometry>
      <material name="black">
        <color rgba="0 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="base_to_left_wheel" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="0.0 0.2 -0.1" rpy="0 1.5708 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="50" velocity="5.0"/>
  </joint>
  
  <joint name="base_to_right_wheel" type="continuous">
    <parent link="base_link"/>
    <child link="right_wheel"/>
    <origin xyz="0.0 -0.2 -0.1" rpy="0 1.5708 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="50" velocity="5.0"/>
  </joint>
  
</robot>"""

# ===================== 工业机械臂URDF =====================

INDUSTRIAL_ARM_URDF = """<?xml version="1.0"?>
<robot name="industrial_arm">
  
  <!-- Base -->
  <link name="base">
    <visual>
      <geometry>
        <cylinder length="0.1" radius="0.15"/>
      </geometry>
    </visual>
  </link>
  
  <!-- Shoulder -->
  <link name="shoulder">
    <visual>
      <geometry>
        <box size="0.1 0.1 0.3"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="base_to_shoulder" type="revolute">
    <parent link="base"/>
    <child link="shoulder"/>
    <origin xyz="0 0 0.05" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="100" velocity="1.0"/>
  </joint>
  
  <!-- Upper Arm -->
  <link name="upper_arm">
    <visual>
      <geometry>
        <box size="0.08 0.08 0.4"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="shoulder_to_upper_arm" type="revolute">
    <parent link="shoulder"/>
    <child link="upper_arm"/>
    <origin xyz="0 0 0.15" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <limit lower="-2.35" upper="2.35" effort="80" velocity="1.5"/>
  </joint>
  
  <!-- Forearm -->
  <link name="forearm">
    <visual>
      <geometry>
        <box size="0.06 0.06 0.35"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="upper_arm_to_forearm" type="revolute">
    <parent link="upper_arm"/>
    <child link="forearm"/>
    <origin xyz="0 0 0.2" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <limit lower="-3.14" upper="0" effort="60" velocity="2.0"/>
  </joint>
  
  <!-- Wrist -->
  <link name="wrist">
    <visual>
      <geometry>
        <cylinder length="0.1" radius="0.05"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="forearm_to_wrist" type="revolute">
    <parent link="forearm"/>
    <child link="wrist"/>
    <origin xyz="0 0 0.175" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="30" velocity="3.0"/>
  </joint>
  
  <!-- End Effector -->
  <link name="end_effector">
    <visual>
      <geometry>
        <box size="0.05 0.05 0.1"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="wrist_to_end_effector" type="fixed">
    <parent link="wrist"/>
    <child link="end_effector"/>
    <origin xyz="0 0 0.05" rpy="0 0 0"/>
  </joint>
  
</robot>"""

# ===================== 无人机URDF =====================

DRONE_URDF = """<?xml version="1.0"?>
<robot name="quadcopter_drone">
  
  <!-- Main Body -->
  <link name="body">
    <visual>
      <geometry>
        <box size="0.3 0.3 0.1"/>
      </geometry>
      <material name="gray">
        <color rgba="0.7 0.7 0.7 1"/>
      </material>
    </visual>
  </link>
  
  <!-- Arms with Motors and Propellers -->
  <link name="arm_front_right">
    <visual>
      <geometry>
        <cylinder length="0.4" radius="0.01"/>
      </geometry>
    </visual>
  </link>
  
  <link name="motor_front_right">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.03"/>
      </geometry>
    </visual>
  </link>
  
  <link name="propeller_front_right">
    <visual>
      <geometry>
        <mesh filename="package://drone_description/meshes/propeller.dae"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="body_to_arm_front_right" type="fixed">
    <parent link="body"/>
    <child link="arm_front_right"/>
    <origin xyz="0.15 0.15 0" rpy="0 0 0.7854"/>
  </joint>
  
  <joint name="arm_to_motor_front_right" type="fixed">
    <parent link="arm_front_right"/>
    <child link="motor_front_right"/>
    <origin xyz="0.2 0 0" rpy="0 0 0"/>
  </joint>
  
  <joint name="motor_to_propeller_front_right" type="continuous">
    <parent link="motor_front_right"/>
    <child link="propeller_front_right"/>
    <origin xyz="0 0 0.025" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>
  
  <!-- Repeat for other arms... -->
  
  <!-- Sensors -->
  <link name="camera">
    <visual>
      <geometry>
        <box size="0.03 0.04 0.02"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="body_to_camera" type="fixed">
    <parent link="body"/>
    <child link="camera"/>
    <origin xyz="0 0 0.05" rpy="0 0 0"/>
  </joint>
  
  <link name="imu">
    <visual>
      <geometry>
        <box size="0.01 0.01 0.005"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="body_to_imu" type="fixed">
    <parent link="body"/>
    <child link="imu"/>
    <origin xyz="0 0 -0.05" rpy="0 0 0"/>
  </joint>
  
</robot>"""

# ===================== 带传感器的移动机器人URDF =====================

MOBILE_ROBOT_WITH_SENSORS_URDF = """<?xml version="1.0"?>
<robot name="mobile_robot_with_sensors">
  
  <!-- Chassis -->
  <link name="chassis">
    <visual>
      <geometry>
        <box size="0.6 0.4 0.15"/>
      </geometry>
    </visual>
    <collision>
      <geometry>
        <box size="0.6 0.4 0.15"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="20.0"/>
      <inertia ixx="0.4" ixy="0.0" ixz="0.0" iyy="0.4" iyz="0.0" izz="0.2"/>
    </inertial>
  </link>
  
  <!-- Wheels -->
  <link name="front_left_wheel">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.1"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="chassis_to_front_left_wheel" type="continuous">
    <parent link="chassis"/>
    <child link="front_left_wheel"/>
    <origin xyz="0.2 0.25 -0.075" rpy="1.5708 0 0"/>
    <axis xyz="0 0 1"/>
    <limit effort="100" velocity="10.0"/>
  </joint>
  
  <!-- Repeat for other wheels... -->
  
  <!-- LiDAR Sensor -->
  <link name="lidar">
    <visual>
      <geometry>
        <cylinder length="0.08" radius="0.05"/>
      </geometry>
      <material name="red">
        <color rgba="0.8 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="chassis_to_lidar" type="fixed">
    <parent link="chassis"/>
    <child link="lidar"/>
    <origin xyz="0.3 0 0.15" rpy="0 0 0"/>
  </joint>
  
  <!-- Camera -->
  <link name="camera">
    <visual>
      <geometry>
        <box size="0.05 0.05 0.03"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 0.8 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="chassis_to_camera" type="fixed">
    <parent link="chassis"/>
    <child link="camera"/>
    <origin xyz="0.25 0 0.1" rpy="0 0.2618 0"/>
  </joint>
  
  <!-- IMU -->
  <link name="imu">
    <visual>
      <geometry>
        <box size="0.02 0.02 0.01"/>
      </geometry>
      <material name="green">
        <color rgba="0 0.8 0 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="chassis_to_imu" type="fixed">
    <parent link="chassis"/>
    <child link="imu"/>
    <origin xyz="0 0 0.05" rpy="0 0 0"/>
  </joint>
  
  <!-- GPS Antenna -->
  <link name="gps">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.02"/>
      </geometry>
    </visual>
  </link>
  
  <joint name="chassis_to_gps" type="fixed">
    <parent link="chassis"/>
    <child link="gps"/>
    <origin xyz="0 0 0.25" rpy="0 0 0"/>
  </joint>
  
</robot>"""

# ===================== 复杂的Xacro示例（包含宏） =====================

XACRO_WITH_MACROS = """<?xml version="1.0"?>
<robot name="complex_robot" xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- Macros for common elements -->
  <xacro:macro name="default_inertial" params="mass">
    <inertial>
      <mass value="${mass}"/>
      <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.05"/>
    </inertial>
  </xacro:macro>
  
  <xacro:macro name="wheel" params="name parent xyz">
    <link name="${name}_wheel">
      <visual>
        <geometry>
          <cylinder length="0.05" radius="0.1"/>
        </geometry>
      </visual>
    </link>
    
    <joint name="${parent}_to_${name}_wheel" type="continuous">
      <parent link="${parent}"/>
      <child link="${name}_wheel"/>
      <origin xyz="${xyz}" rpy="0 1.5708 0"/>
      <axis xyz="0 1 0"/>
      <limit effort="50" velocity="5.0"/>
    </joint>
  </xacro:macro>
  
  <xacro:macro name="sensor" params="name type parent xyz rpy:=0 0 0">
    <link name="${name}_${type}">
      <visual>
        <geometry>
          <box size="0.05 0.05 0.05"/>
        </geometry>
        <material name="${type}_color"/>
      </visual>
    </link>
    
    <joint name="${parent}_to_${name}_${type}" type="fixed">
      <parent link="${parent}"/>
      <child link="${name}_${type}"/>
      <origin xyz="${xyz}" rpy="${rpy}"/>
    </joint>
  </xacro:macro>
  
  <!-- Main robot structure using macros -->
  <link name="base">
    <visual>
      <geometry>
        <box size="0.5 0.3 0.2"/>
      </geometry>
    </visual>
    <xacro:default_inertial mass="5.0"/>
  </link>
  
  <!-- Add wheels using macro -->
  <xacro:wheel name="front_left" parent="base" xyz="0.2 0.15 -0.1"/>
  <xacro:wheel name="front_right" parent="base" xyz="0.2 -0.15 -0.1"/>
  <xacro:wheel name="rear_left" parent="base" xyz="-0.2 0.15 -0.1"/>
  <xacro:wheel name="rear_right" parent="base" xyz="-0.2 -0.15 -0.1"/>
  
  <!-- Add sensors using macro -->
  <xacro:sensor name="front" type="lidar" parent="base" xyz="0.25 0 0.15"/>
  <xacro:sensor name="top" type="camera" parent="base" xyz="0 0 0.25" rpy="0 0.3 0"/>
  <xacro:sensor name="center" type="imu" parent="base" xyz="0 0 0.1"/>
  
</robot>"""

# ===================== 测试查询问题 =====================

URDF_TEST_QUERIES = [
    {
        "query": "What joints are in the simple robot?",
        "expected_keywords": ["joint", "base_to_left_wheel", "base_to_right_wheel", "continuous"]
    },
    {
        "query": "Tell me about the industrial arm joints and their limits",
        "expected_keywords": ["revolute", "limit", "shoulder", "wrist", "effort"]
    },
    {
        "query": "What sensors are on the mobile robot?",
        "expected_keywords": ["lidar", "camera", "imu", "gps", "sensor"]
    },
    {
        "query": "How is the drone structured?",
        "expected_keywords": ["propeller", "motor", "arm", "body", "quadcopter"]
    },
    {
        "query": "What type of joints connect wheels to the chassis?",
        "expected_keywords": ["continuous", "wheel", "joint", "chassis"]
    },
    {
        "query": "Describe the robot's base link properties",
        "expected_keywords": ["mass", "inertia", "visual", "geometry", "box"]
    },
    {
        "query": "What are the limits for the industrial arm's shoulder joint?",
        "expected_keywords": ["lower", "upper", "effort", "velocity", "shoulder"]
    }
]

def get_test_urdf_cases():
    """返回所有URDF测试用例"""
    return {
        "simple_robot": {
            "name": "Simple Mobile Robot",
            "urdf": SIMPLE_ROBOT_URDF,
            "description": "一个简单的移动机器人，包含底盘和两个轮子"
        },
        "industrial_arm": {
            "name": "Industrial Robotic Arm",
            "urdf": INDUSTRIAL_ARM_URDF,
            "description": "工业机械臂，包含基座、肩部、上臂、前臂、腕部和末端执行器"
        },
        "drone": {
            "name": "Quadcopter Drone",
            "urdf": DRONE_URDF,
            "description": "四旋翼无人机，包含机身、臂、电机、螺旋桨和传感器"
        },
        "mobile_robot_with_sensors": {
            "name": "Mobile Robot with Sensors",
            "urdf": MOBILE_ROBOT_WITH_SENSORS_URDF,
            "description": "带多种传感器的移动机器人（LiDAR、相机、IMU、GPS）"
        },
        "xacro_with_macros": {
            "name": "Complex Robot with Xacro Macros",
            "urdf": XACRO_WITH_MACROS,
            "description": "使用Xacro宏定义复杂机器人结构"
        }
    }

def print_urdf_summary():
    """打印URDF测试用例摘要"""
    test_cases = get_test_urdf_cases()
    
    print("🚀 URDF测试用例摘要")
    print("="*60)
    
    for key, data in test_cases.items():
        print(f"\n📦 {data['name']} ({key})")
        print(f"   描述: {data['description']}")
        
        # 统计URDF内容
        lines = data['urdf'].split('\n')
        print(f"   行数: {len(lines)}")
        print(f"   大小: {len(data['urdf'])} 字符")
        
        # 统计关键元素
        joint_count = data['urdf'].count('<joint')
        link_count = data['urdf'].count('<link')
        print(f"   Links: {link_count}, Joints: {joint_count}")
    
    print(f"\n📝 测试查询: {len(URDF_TEST_QUERIES)} 个")
    for i, query in enumerate(URDF_TEST_QUERIES[:3]):  # 只显示前3个
        print(f"   {i+1}. {query['query']}")

if __name__ == "__main__":
    print_urdf_summary()