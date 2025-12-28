#!/usr/bin/env python3
"""
测试URDF解析器的实际输出
"""

import sys
import os
from test_urdf_data import SIMPLE_ROBOT_URDF
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from app.services.parsers.urdf_parser import URDFParser

# 首先直接查看URDF内容
print("URDF原始内容分析:")
print("="*60)

lines = SIMPLE_ROBOT_URDF.split('\n')
for i, line in enumerate(lines):
    if '<joint' in line or '<link' in line:
        print(f"行 {i+1}: {line.strip()}")

# 尝试使用解析器
try:
    
    parser = URDFParser()
    
    print(f"\n解析器输出:")
    print("="*60)
    
    chunks = parser.parse_urdf(SIMPLE_ROBOT_URDF, "test_robot")
    
    print(f"生成的chunks数量: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\n=== Chunk {i+1} ===")
        print(f"文本: {chunk.get('text', '')}")
        print(f"元数据: {chunk.get('metadata', {})}")
        
except ImportError as e:
    print(f"导入解析器失败: {e}")
    
    # 手动解析
    import xml.etree.ElementTree as ET
    
    print(f"\n手动解析URDF:")
    root = ET.fromstring(SIMPLE_ROBOT_URDF)
    
    # 查找所有关节
    joints = root.findall('joint')
    print(f"关节数量: {len(joints)}")
    for joint in joints:
        name = joint.get('name')
        jtype = joint.get('type')
        print(f"  关节: {name}, 类型: {jtype}")
    
    # 查找所有链接
    links = root.findall('link')
    print(f"链接数量: {len(links)}")
    for link in links:
        name = link.get('name')
        print(f"  链接: {name}")