[file name]: deploy_diagnostics.sh
#!/bin/bash
# 部署故障诊断树功能

echo "🚀 部署故障诊断树功能"
echo "=" * 70

# 1. 创建目录结构
echo "1. 创建目录结构..."
mkdir -p /home/fishros/ai-ros/app/diagnostics
mkdir -p /home/fishros/ai-ros/app/services

# 2. 复制文件
echo "2. 复制文件..."

# 诊断树文件
# cp /home/fishros/ai-ros/app/diagnostics//fault_tree.py /home/fishros/ai-ros/app/diagnostics/
cp /home/fishros/ai-ros/app/diagnostics//diagnostic_service.py /home/fishros/ai-ros/app/services/
cp /home/fishros/ai-ros/app/diagnostics//prompt_builder_with_diagnosis.py /home/fishros/ai-ros/app/services/
cp /home/fishros/ai-ros/app/diagnostics//query_service_with_diagnosis.py /home/fishros/ai-ros/app/services/
cp /home/fishros/ai-ros/app/diagnostics//diagnostic_api.py /home/fishros/ai-ros/app/api/v1/
cp /home/fishros/ai-ros/app/diagnostics//dependencies_with_diagnosis.py /home/fishros/ai-ros/app/api/dependencies.py
cp /home/fishros/ai-ros/app/diagnostics//main_with_diagnostics.py /home/fishros/ai-ros/app/main.py

# 3. 备份原文件
echo "3. 备份原文件..."
timestamp=$(date +%Y%m%d_%H%M%S)
cp /home/fishros/ai-ros/app/services/query_service.py /home/fishros/ai-ros/app/services/query_service.py.backup_$timestamp
cp /home/fishros/ai-ros/app/main.py /home/fishros/ai-ros/app/main.py.backup_$timestamp

# 4. 测试导入
echo "4. 测试导入..."
cd /home/fishros/ai-ros
python3 -c "
try:
    from app.diagnostics.fault_tree import FAULT_TREES
    print('✅ 故障树导入成功')
    print(f'   错误代码数量: {len(FAULT_TREES)}')
    
    from app.services.diagnostic_service import DiagnosticService
    print('✅ 诊断服务导入成功')
    
    from app.api.v1.diagnostic_api import router
    print('✅ 诊断API导入成功')
    
except Exception as e:
    print(f'❌ 导入失败: {e}')
    import traceback
    traceback.print_exc()
"

# 5. 重启服务
echo "5. 重启服务..."
if pgrep -f "uvicorn" > /dev/null; then
    echo "   重启uvicorn服务..."
    pkill -f "uvicorn"
    sleep 2
fi

echo "   启动新服务..."
cd /home/fishros/ai-ros
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/ros_docs_diagnosis.log 2>&1 &
echo $! > /tmp/ros_docs_diagnosis.pid

# 6. 等待服务启动
echo "6. 等待服务启动..."
sleep 5

# 7. 测试服务
echo "7. 测试服务..."
curl -s http://localhost:8000/health
if [ $? -eq 0 ]; then
    echo "✅ 服务启动成功"
else
    echo "❌ 服务启动失败"
    echo "查看日志: tail -f /tmp/ros_docs_diagnosis.log"
    exit 1
fi

# 8. 运行测试
echo "8. 运行功能测试..."
python3 /home/fishros/ai-ros/app/diagnostics//test_diagnosis.py

echo -e "\n" + "=" * 70
echo "✅ 部署完成!"
echo ""
echo "🌐 访问地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🔧 诊断端点:"
echo "   - POST /api/v1/diagnostics/analyze"
echo "   - GET /api/v1/diagnostics/available"
echo "   - GET /api/v1/diagnostics/tree/{error_code}"
echo ""
echo "📋 查看日志: tail -f /tmp/ros_docs_diagnosis.log"