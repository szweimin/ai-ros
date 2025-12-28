#!/bin/bash
echo "🚀 运行所有URDF测试"
echo "================================"

# 检查服务是否运行
echo -e "\n1. 检查服务状态..."
curl -s http://localhost:8000/health | jq .

# 运行快速测试
echo -e "\n2. 运行快速测试..."
python test_urdf_quick.py

# 运行完整测试
echo -e "\n3. 运行完整API测试..."
python test_urdf_api.py

# 测试命令行工具
echo -e "\n4. 测试命令行工具..."
echo -e "\n  导入测试URDF..."
python urdf_tester.py ingest test_urdf_data.py --name "test_data"

echo -e "\n  查询测试..."
python urdf_tester.py query "What is in the test URDF data?"

echo -e "\n  查看历史..."
python urdf_tester.py history --limit 5

echo -e "\n✅ 所有测试完成！"