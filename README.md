## 一 github上创建仓库

## 二 设置 UV 和 Python 3.11 环境

### 1 安装 UV

```
 打开终端，执行以下命令来安装 UV。UV 是一个快速的 Python 包管理器和项目环境管理工具。
    curl -LsSf https://astral.sh/uv/install.sh | sh
    安装完成后，需要重新启动终端或者执行 source ~/.bashrc 来确保 UV 命令可用。
```

### 2 确保 Python 3.11 可用

    uv python list  # 查看当前可用的 Python 版本
    uv python install 3.11  # 安装 Python 3.11

    3 为项目创建并配置环境
    git clone https://github.com/<your-username>/ai-infra-base.git
    cd ai-infra-base
    # 使用UV 初始化项目， 并固定使用 Python 3.11in/
     uv init  生成 pyproject.toml
     uv venv --python 3.11   命令会在项目目录下创建虚拟环境（通常是 .venv 文件夹）并安装python3.11

    4 激活虚拟环境（可选）
    你可以激活虚拟环境，这样后续的命令都会在这个隔离的环境中执行。
    source .venv/bin/activate
    5 uv常用命令
        # 添加依赖
        uv add package-name
        # 添加开发依赖
        uv add --dev package-name
        # 同步依赖（根据 pyproject.toml 安装）
        uv sync
        # 查看已安装的包
        uv tree

三 创建FASTAPI骨架
    1. 添加 FastAPI 依赖
        首先在项目目录中安装 FastAPI 和 Uvicorn：
        bash
        # 确保在项目目录中
        cd ~/ai-infra-base
        # 添加 FastAPI 和 Uvicorn 依赖
        uv add "fastapi[all]"
        #后续要用到这个依赖
        uv add sentence-transformers
    2. 创建项目结构
        创建以下目录和文件：
        bash
        # 创建 app 目录
        mkdir -p app
        # 创建 main.py 文件
        touch app/main.py
        项目结构应该是：
        text
        ai-infra-base/
            ├── app/
            │   └── main.py
            ├── .venv/
            ├── pyproject.toml
            ├── uv.lock
            └── README.md
    3. 编写 FastAPI 代码
        编辑 app/main.py 文件

    4. 运行 FastAPI 应用
        现在启动 Uvicorn 服务器：
        bash
        # 方式一：直接运行（推荐）
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

        # 方式二：使用 uv run（如果虚拟环境没激活）
        uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

    5. 测试 API
        服务器启动后，打开浏览器访问：
        http://localhost:8000/health
        http://localhost:8000/ - 根端点
        http://localhost:8000/health/detailed - 详细健康检查
        http://localhost:8000/docs - 自动生成的 API 文档（Swagger UI）
        http://localhost:8000/redoc - 另一种 API 文档

    6. 创建启动脚本（可选）
        为了方便，可以创建一个启动脚本 run.sh：
        bash
        #!/bin/bash
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        然后给执行权限：
        bash
        chmod +x run.sh
    8. 提交代码到 Git
        bash
        # 添加文件到 Git
        git add app/main.py pyproject.toml uv.lock
        # 提交更改
        git commit -m "feat: add FastAPI minimal skeleton with health endpoint"
        # 推送到 GitHub
        git push origin main

四  配置 ruff 和 mypy
    1. 安装开发依i
    bash
    # 安装 ruff 和 mypy    uv add --dev ruff mypy
    # 或者分别安装          uv add ruff   uv add mypy
    2. 配置 Ruff
    创建 .ruff.toml 文件：
    3. 配置 Mypy
    创建 .mypy.ini 文件：
    5. 运行检查
    # 运行 ruff 检查
    ruff check .
    # 运行 ruff 自动修复
    ruff check . --fix
    # 运行 ruff 格式化
    ruff format .
    # 运行 mypy 检查
    mypy .
    # 同时运行两个检查
    ruff check . && mypy .
    6. 添加便捷脚本
    在 pyproject.toml 中添加脚本命令：
    toml
    # 在 pyproject.toml 的 [tool] 部分添加
    [tool.ruff]
    # ruff 配置可以放在这里，或者使用 .ruff.toml

    [tool.mypy]
    # mypy 配置可以放在这里，或者使用 .mypy.ini

    [project.scripts]
    lint = "ruff check ."
    type-check = "mypy ."
    format = "ruff format ."
    fix = "ruff check . --fix"
    check-all = "ruff check . && mypy ."
    然后你可以运行：

    bash
    # 使用 uv run 运行检查
    uv run lint
    uv run type-check
    uv run check-all
    7. 创建测试脚本
    创建 scripts/check.py 进行更全面的检查：

    python
    #!/usr/bin/env python3
    """代码质量检查脚本"""
    import subprocess
    import sys


    def run_command(command: str) -> bool:
        """运行命令并返回是否成功"""
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ {command} - 成功")
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {command} - 失败")
            print(f"错误输出: {e.stderr}")
            if e.stdout:
                print(f"标准输出: {e.stdout}")
            return False


    def main() -> None:
        """主函数"""
        print("🚀 开始代码质量检查...")

        checks = [
            "ruff check .",
            "ruff format . --check",
            "mypy ."
        ]

        all_passed = True
        for check in checks:
            if not run_command(check):
                all_passed = False

        if all_passed:
            print("\n🎉 所有检查通过！")
            sys.exit(0)
        else:
            print("\n💥 有些检查未通过，请修复后重试")
            sys.exit(1)
    if __name__ == "__main__":
        main()
    运行测试脚本：

    bash
    uv run python scripts/check.pyscr

五  安装 pytest 并测试
    1 安装 pytest 和异步支持
    uv add --dev pytest pytest-asyncio httpx
    2. 创建测试目录和文件
    bash
    # 创建测试目录
    mkdir -p tests
    # 创建测试文件
    touch tests/__init__.py
    touch tests/test_health.py
    touch tests/test_app.py
    3. 配置 pytest
    # 在 pyproject.toml 中添加以下内容
    [tool.pytest.ini_options]
    testpaths = ["tests"]
    python_files = ["test_*.py"]
    python_classes = ["Test*"]
    python_functions = ["test_*"]
    addopts = [
        "--verbose",
        "--strict-markers",
        "--strict-config",
        "--asyncio-mode=auto"
    ]
    asyncio_mode = "auto"

    markers = [
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
        "integration: marks tests as integration tests",
        "unit: marks tests as unit tests",
    ]
    4. 编写测试代码
    tests/test_health.py
    tests/test_app.py

    5. 运行测试
       # 运行所有测试
        pytest

        # 运行测试并显示详细输出
        pytest -v

        # 运行特定文件中的测试
        pytest tests/test_health.py -v

        # 运行特定类的测试
        pytest tests/test_health.py::TestHealthEndpoints -v

        # 运行特定测试方法
        pytest tests/test_health.py::TestHealthEndpoints::test_health_status_is_ok -v

        # 显示测试覆盖率（需要安装 pytest-cov）
        uv add --dev pytest-cov
        pytest --cov=app --cov-report=term-missing

六  引入pre-commit hook集成ruff + mypy + pytest
    1. 安装 pre-commit
    uv add --dev pre-commit
    # 或者使用 pip
    pip install pre-commit

    2. 创建 .pre-commit-config.yaml 文件

    3. 初始化 pre-commit
    pre-commit install

    4. 验证安装
    pre-commit --version

    5. 在 pyproject.toml 中添加配置
        # 在 pyproject.toml 中添加 pre-commit 配置
        [tool.pre-commit]
        verbose = true
        fail_fast = false

        [project.scripts]
        pre-commit-install = "pre-commit install"
        pre-commit-run = "pre-commit run --all-files"
        pre-commit-autoupdate = "pre-commit autoupdate"

    6. 运行 pre-commit
        # 手动对所有文件运行 pre-commit
        pre-commit run --all-files

        # 运行特定的 hook
        pre-commit run ruff --all-files
        pre-commit run mypy --all-files
        pre-commit run pytest --all-files

        # 自动更新 pre-commit hooks 到最新版本
        pre-commit autoupdate

    7. 提交配置
        bash
        git add .pre-commit-config.yaml pyproject.toml scripts/verify.sh
        git commit -m "feat: add pre-commit hooks with ruff, mypy, pytest"
        git push origin main
        验证设置
        现在每次你运行 git commit 时，都会自动执行：
        ✅ ruff - 代码格式化和检查
        ✅ mypy - 类型检查
        ✅ pytest - 运行测试
        ✅ 其他代码质量检查
        如果任何检查失败，提交会被阻止，确保只有高质量的代码才能进入仓库

七  创建 Makefile
`    1 根目录下创建Makefile文件
    2 使用说明
        # 显示所有可用命令   make help
        # 运行代码检查   make lint
        # 运行测试      make test
        # 运行所有检查   make all
        # 格式化代码    make format
        # 清理生成的文件 make clean
        # 安装依赖      make install
        # 开发模式运行   make run`

八 创建 GitHub Actions工作流

1. 创建 GitHub Actions 工作流目录
   mkdir -p .github/workflows

2. 创建 CI 工作流文件
   创建 .github/workflows/ci.yml：

3. 更新 pyproject.toml 添加测试配置

4. 提交并推送代码

   # 添加 GitHub Actions 文件

   git add .github/workflows/ ci.yml pyproject.toml

   # 提交更改

   git commit -m "feat: add GitHub Actions CI with lint and test"

   # 推送到 GitHub（这会触发 Actions）

   git push origin main
   5 确保不容易出错的解决方案

   # 提交前手动运行修复

   pre-commit run --all-files

   # 添加所有修复后的文件

   git add .
   # 提交（这次应该能成功）
   git commit -m "你的提交信息"   触发pre-commit
   git commit --no-verify -m "提交信息" 不触发pre-commit, 应用于无法更改代码的状况。

   # 推送
   git push origin main
   6 解决当前某个文件在工作区和缓存区不一致的问题
   # 重置当前状态
   git restore --staged .github/workflows/test.yml
   git restore .github/workflows/test.yml
   # 重新添加和提交（跳过hooks）
   git add .github/workflows/test.yml
   git commit -m "ci: switch from uv to pip in GitHub Actions" --no-verify
   git push origin main
   九  PostgreSQL 16 + pgvector 0.7+ 环境安装
   1 创建 docker-compose.yml
      cat > docker-compose.yml << 'EOF'
      version: '3.8'
      services:
      postgres:
          image: pgvector/pgvector:pg16
          environment:
          POSTGRES_DB: ai_infra
          POSTGRES_USER: ai_user
          POSTGRES_PASSWORD: ai_password
          ports:
          - "5432:5432"
          volumes:
          - postgres_data:/var/lib/postgresql/data
          command: postgres -c shared_preload_libraries=vector
      volumes:
      postgres_data:
      EOF

   2 启动服务
      docker-compose up -d

   3 验证安装

   # 可用navicat 测试连接和 pgvector 功能

      CREATE EXTENSION IF NOT EXISTS vector; 的意图是启用 pgvector 扩展，让 PostgreSQL 具备处理向量数据的能力。
      -- 测试向量功能
      CREATE TABLE test_vectors (id serial PRIMARY KEY, embedding vector(3));
      INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');
      SELECT * FROM test_vectors;
      "
   4 项目配置
    在项目中添加依赖 添加 PostgreSQL 驱动
      uv add "psycopg[binary]"  # 或 asyncpg
      uv add sqlalchemy
      uv add pgvector
      
   10  Week5 / Fri 目标
   curl -X POST http://localhost:8000/api/v1/rag/query \
   -H "Content-Type: application/json" \
   -d '{"query": "Explain AGV safety requirements", "top_k": 5}'
   Fri 完成：RAG 系统本地 LLM + Docker E2E 运行成功


 十一   Week6 / Mon：Structured RAG（加入表格/字段解析）
        表结构
        CREATE TABLE documents (
        id TEXT PRIMARY KEY,  -- 或 UNIQUE
        text TEXT NOT NULL,
        embedding VECTOR(384),  -- PostgreSQL 向量扩展
        metadata JSONB );

    1 存储测试文档
    curl -X POST "http://localhost:8000/documents/ingest" \
    -H "Content-Type: application/json" \
    -d '{
        "id": "agv_safety_1",
        "text": "AGV safety requires emergency stop buttons, laser scanners, and safety zones around operating areas.",
        "metadata": {
        "category": "safety",
        "robot_type": "AGV",
        "priority": "high"
        }
    }'

    curl -X POST "http://localhost:8000/documents/ingest" \
    -H "Content-Type: application/json" \
    -d '{
        "id": "robot_maintenance_1",
        "text": "Regular maintenance includes battery checks, sensor calibration, and software updates.",
        "metadata": {
        "category": "maintenance",
        "robot_type": "general",
        "frequency": "monthly"
        }
    }'

    2. 测试基础查询
    curl -X POST "http://localhost:8000/documents/query" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "AGV safety emergency",
        "top_k": 3
    }'

    3. 测试 Hybrid Query
     # 基础 hybrid 查询
    curl -X POST "http://localhost:8000/documents/hybrid-query" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "AGV safety battery maintenance",
        "top_k": 3
    }'

    # 自定义权重 hybrid 查询
    curl -X POST "http://localhost:8000/documents/hybrid-query" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "AGV safety",
        "top_k": 3,
        "keyword_weight": 0.4,
        "vector_weight": 0.6
    }'

    # 带 metadata 过滤的 hybrid 查询
    curl -X POST "http://localhost:8000/documents/hybrid-query" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "safety",
        "top_k": 3,
        "metadata_filter": {
        "robot_type": "AGV"
        }
    }'

    # 带 metadata boost 的 hybrid 查询
    curl -X POST "http://localhost:8000/documents/hybrid-query" \
    -H "Content-Type: application/json" \
    -d {
       "query": "AGV safety",
       "top_k": 3,
       "metadata_boost": {
       "category": 0.05,
       "robot_type": 0.03
       }}

12  Week6 / Tue
    12.1 描述
    自动 Chunking + Metadata 生成（工业文档 Ingestion Pipeline）
    今天一句话目标:把“机器人 / 工业文档”自动变成可检索、可理解、可约束的知识，而不是手工粘贴文本。这是企业级 RAG 的生死线。
    Raw document
    → Chunk
    → 自动 metadata
    → Embedding
    → Vector DB
    12.2 设计目标（今天不追求复杂）
     我们做一个工程可接受、面试可讲、未来可扩展的版本。支持：
        文本自动切 chunk
        每个 chunk 自动生成：
        chunk_id
        source_doc_id
        chunk_index
        category（简单规则）
        自动写入 pgvector

    12.3Chunking 模块设计
        📁 新增目录：
        app/ingestion/
        chunker.py
        metadata.py
        pipeline.py

13  Week6 /WED Hybrid Retrieval（Vector + Metadata Filter）
    13.1  Hybrid Retrieval设计
        向量相似度（基础）
        Metadata Filter（硬约束）
        Metadata Boost（软权重）
    13.2 代码改进
        集中配置管理：创建了 core/BoostConfig 类来统一管理权重和规则；
        支持配置化的自动提升规则支持中英文触发词；可配置权重参数
        消除重复：移除了端点层v1/point/document.py中的重复处理代码
        逻辑复用：将过滤和加权逻辑提取到 DocumentProcessor 类中,并把该逻辑转移到service/rag_document.py中

14  Week6/Thu Answer Attribution + Confidence Scoring
    14.1 功能
         答案基于哪些文档？每个文档贡献了多少？系统对这个答案有多自信
    14.2 设计目标
         Context Attribution（来源标注）
         Answer Confidence Scoring（置信度）
         Response Schema 升级
    14.3 完成标准
        ✅ 回答中带 context citation
        ✅ response 中包含 confidence
        ✅ confidence 可解释、非 LLM 生成
        ✅ 系统在 context 不足时会拒答
   14.4 代码
        合并了api/v1/endpints/rag.py,services/rag_prompt.py,service/rag_service.py
        新增了service/confidence.py. scripts/test_confidence_rag.py
    14.5 测试
         http://localhost:8000/rag/query
         {
            "query": "robot_safety_general",
            "top_k": 5,
            "min_confidence": 0.3
            }
        或者 python3 scripts/test_confidence_rag.py

15 Week6 / Fri  工业 AI 项目总结 + 欧洲岗位对标 + 面试话术
            工业文档
        → 自动 Chunking
        → 自动 Metadata 推断
        → Embedding
        → pgvector 存储
        → Hybrid Retrieval（Vector + Filter + Boost）
        → 可控 Prompt
        → 本地 LLM（Ollama）
        → 回答溯源
        → 置信度评估
        → API 服务化
        → Docker Compose 部署
        
16  week7/mon 把 ROS 的“工程知识”变成 RAG 可用的结构化知识。 (AI-ROS)   
一 安装和运行
    1   安装模块 
       cd ai-ros
       uv venv --python 3.11   命令会在项目目录下创建虚拟环境（通常是 .venv 文件夹）并安装python3.11
       source .venv/bin/activate
       uv pip install -r requirements.txt
    2  创建数据表（ros_document_chunks）
        终端输入： python3 init_db_native.py
        终端输入：
        psql postgresql://ai_user:ai_password@182.61.39.44:5432/ai_infra
        \d ros_document_chunks  获取表结构
         
       
                    Column      |            Type             | Collation | Nullable |                     Default                     
        ------------------+-----------------------------+-----------+----------+-------------------------------------------------
        id               | integer                     |           | not null | nextval('ros_document_chunks_id_seq'::regclass)
        chunk_id         | character varying(100)      |           | not null | 
        text             | text                        |           | not null | 
        embedding        | jsonb                       |           |          | 
        embedding_vector | vector(384)                 |           |          | 
        doc_metadata     | jsonb                       |           | not null | 
        category         | character varying(50)       |           | not null | 
        source_id        | character varying(100)      |           | not null | 
        created_at       | timestamp without time zone |           | not null | CURRENT_TIMESTAMP
        updated_at       | timestamp without time zone |           |          | CURRENT_TIMESTAMP
        Indexes:
            "ros_document_chunks_pkey" PRIMARY KEY, btree (id)
            "idx_category" btree (category)
            "idx_category_source" btree (category, source_id)
            "idx_chunk_id" btree (chunk_id)

    3  启动服务
       uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    4  API调用示例
            1. 导入ROS Topic
            bash

            curl -X POST "http://localhost:8000/api/v1/ros/topics/ingest" \
            -H "Content-Type: application/json" \
            -d '{
                "topics": [
                {
                    "topic": "/cmd_vel",
                    "type": "geometry_msgs/Twist",
                    "description": "Velocity command for AGV movement control",
                    "rate": "10Hz"
                }
                ]
            }'

            2. 查询示例
            bash

            curl -X POST "http://localhost:8000/api/v1/ros/query" \
            -H "Content-Type: application/json" \
            -d '{
                "query": "Which ROS topic controls AGV velocity?",
                "top_k": 3
            }'
            预期响应：
            {
                "answer":"The provided context indicates that the ROS Topic \"/cmd_vel\" is used for controlling the velocity of an AGV (Automated   Guided Vehicle). So, the answer to your question is \"/cmd_vel\".\n\nReferences: [Source 1]",
                "sources":[
                    {
                        "id":"ros_topic_c52437d9_0000",
                        "text":"ROS Topic: /cmd_vel. Message Type: geometry_msgs/Twist.Description: Velocity command for AGV movement control. Publish Rate: 10Hz.",
                        "category":"ros_topic",
                        "score":0.7017938254125327,
                        "metadata":{
                            "rate":"10Hz",
                            "topic":"/cmd_vel",
                            "category":"ros_topic",
                            "msg_type":"geometry_msgs/Twist",
                            "source_id":"ros_topic_c52437d9",
                            "description":"Velocity command for AGV movement control",
                            "has_subscribers":false
                            }
                            }
                ],
                "confidence":0.7017938254125327
                }
    整体测试 
       ./run_all_urdf+tests.sh ,里面包含了不同的测试函数，可以单独进行测试了解细节
       
    5 主要优化点：
            本地嵌入模型支持：使用 sentence-transformers 库，完全离线运行
            多模型支持：支持 local、OpenAI、Ollama 三种嵌入服务
            pgvector集成：支持向量相似度搜索，提高检索精度
            降级机制：当向量搜索失败时，自动降级到文本相似度搜索
            类型安全：添加了完整的类型注解
            配置灵活：通过环境变量轻松切换不同嵌入服务
            性能优化：使用异步处理和批处理，提高处理效率
    
17  Week7 / Tue  RAG + Runtime Robot State（参数 / 状态 / 报错）
     1 目标： 让 RAG 不仅能查“文档”，还能结合“机器人当前状态”来回答问题。

     2 今天要解决的真实问题（你一定遇到过）
        工程现场常见问题：
        “AGV 不动了，可能原因是什么？”“当前 joint_3 超限了吗？” “为什么 ROS 节点启动失败？” “E201 报错代表什么，要怎么处理？”
        👉 这些问题 必须结合：
        静态知识（文档 / URDF / Topic）
        动态状态（参数 / topic 状态 / error code）
    
    3 完成标准
        ✅ API 支持 runtime_state 
        ✅ Runtime state 进入 prompt
        ✅ RAG 结合 error / topic 给出解释
        ✅ 回答仍有 citation + confidence
    4 测试  
        4.0  python3 scripts/load_data.py   #导入数据到数据库
        4.1 普通查询: POST /api/v1/ros/query 仅基于静态文档的查询
          
            curl -X POST "http://localhost:8000/api/v1/ros/query" \
            -H "Content-Type: application/json" \
            -d '{
            "query": "What is error E201?",
            "top_k": 5
            }'
        4.2运行时查询: POST /api/v1/ros/query-with-runtime
        {
            "query": "Why is the AGV not moving?",
            "top_k": 5,
            "runtime_state": {
                "robot_id": "agv_01",
                "errors": ["E201"],
                "active_topics": ["/odom", "/battery"],
                "parameters": {
                "emergency_stop": "active",
                "speed_limit": "0"
                }
            }
            }
        4.3 提供完整的运行时状态信息;明确描述问题现象;包含相关错误代码;指定机器人类型和上下文;设置合适的top_k值（3-10）
           # 诊断AGV问题
            curl -X POST http://localhost:8000/api/v1/ros/query-with-runtime \
            -H "Content-Type: application/json" \
            -d '{
                "query": "AGV不动了，可能原因是什么？",
                "top_k": 5,
                "runtime_state": {
                "robot_id": "agv_01",
                "errors": ["E201"],
                "parameters": {"emergency_stop": "active"}
                }
            }'

            # 检查关节超限
            curl -X POST http://localhost:8000/api/v1/ros/query-with-runtime \
            -H "Content-Type: application/json" \
            -d '{
                "query": "关节超限怎么处理？",
                "top_k": 3,
                "runtime_state": {
                "robot_id": "arm_01",
                "errors": ["E301"],
                "parameters": {"joint_position": "2.3"}
                }
            }'

18  Week7 / Wed  RAG + Fault Diagnosis Tree（工程逻辑 × AI）
     18.1 目标 
        让 AI 不只是回答“是什么”，而是能按工程逻辑给出“可能原因 + 排查顺序”。工程逻辑如下树状
         
     18.2 二、设计目标（工程优先，AI 辅助）
        Fault Tree 用 结构化 JSON
        Error E201
                    ├─ Safety laser triggered
                    ├─ Emergency stop pressed
                    ├─ Safety PLC not ready
        AI 只负责：结合 runtime state，结合文档 context，给出 最可能的路径
    18.3  完成标准（Week7 / Wed）
        ✅ Fault Tree 用结构化数据
        ✅ DiagnosticService 可独立测试
        ✅ RAG 输出包含排查步骤
        ✅ AI 不“猜原因”，而是“走树”
    18.4 测试
        测试1: 带错误诊断的查询"
        curl -X POST http://localhost:8000/api/v1/ros/query-with-runtime \
        -H "Content-Type: application/json" \
        -d '{
            "query": "机器人安全停止了怎么办",
            "top_k": 3,
            "runtime_state": {
            "robot_id": "test_robot",
            "errors": ["E201"]
            }
        }' 
        测试2: 诊断分析API"
        curl -X POST http://localhost:8000/api/v1/diagnostics/analyze \
        -H "Content-Type: application/json" \
        -d '{
            "error_codes": ["E201"],
            "runtime_state": {
            "robot_id": "test_robot",
            "errors": ["E201"],
            "active_topics": ["/scan", "/cmd_vel"],
            "parameters": {"emergency_stop": true}
            },
            "include_detailed_analysis": true
        }' 
        测试3: 基础查询功能"
        curl -X POST http://localhost:8000/api/v1/ros/query \
        -H "Content-Type: application/json" \
        -d '{
            "query": "什么是ROS安全系统",
            "top_k": 2
        }'
    
    19 Week7 / Thu Multi-Robot / Fleet-Level Knowledge & Diagnosis
        19.1目标   
           让系统能跨机器人、跨型号、跨状态做对比与诊断。这是 AGV / AMR / 机器人公司真实需要的能力。
    
        19.2工业场景需求：
           同一型号20台AGV，其中 3 台频繁报 E201，固件版本不一致。工程师想知道：是单机问题？设计缺陷？现场环境问题？
       
        19.3 完成标准
            ✅ Fleet schema 定义完成
            ✅ FleetDiagnosticService 可测试
            ✅ RAG 能区分单机 / 系统问题
            ✅ 回答体现统计与工程逻辑
        
        19.4 测试
          python3 test_fleet_example.py , python3  test_fleet_simple.py
          python3 scripts/test_fleet_scenarios.py  python3 scripts/test_fleet_diagnostics_api.py
    
    20  Week8/Mon Runtime Integration 架构（ROS / OPC-UA / Edge → AI）
        20.1  目标
            把“真实机器人运行状态”接入你现有的 RAG 系统，但保持工程边界清晰
            [ Robot / PLC / ROS2 ]
                    |
            (Edge Adapter)
                    |
            Runtime Snapshot API
                    |
            AI Knowledge & Diagnosis System
                    |
            Engineer / Dashboard / Ticket System

        20.2  完成标准
            ✅ RuntimeSnapshot schema 完成
            ✅ Snapshot API 可接收数据
            ✅ Snapshot 能转成 RAG context
            ✅ 不破坏现有 RAG 架构

        20.3 测试所有端点
            测试 1：根路径
            GET http://localhost:8000/api/v1/snapshot-ingestion/

            测试 2：健康检查
            GET http://localhost:8000/api/v1/snapshot-ingestion/health
            Header: X-API-Key: edge-adapter-ros-key

            测试 3：发送快照
            POST http://localhost:8000/api/v1/snapshot-ingestion/snapshot
            Header: X-API-Key: edge-adapter-ros-key
            Body (JSON)
            {
            "robot_id": "agv_01",
            "model": "A1",
            "firmware": "v2.1",
            "timestamp": "2026-01-05T10:12:00Z",
            "errors": ["E201"],
            "joint_states": {"wheel_left": 0.0, "wheel_right": 0.0},
            "active_topics": ["/scan", "/odom"]
            }

            测试 4：批量发送
            POST http://localhost:8000/api/v1/snapshot-ingestion/batch
            Header: X-API-Key: edge-adapter-ros-key
            Body (JSON):
            {
            "snapshots": [
                {
                "robot_id": "agv_01",
                "model": "A1",
                "firmware": "v2.1",
                "timestamp": "2026-01-05T10:12:00Z",
                "errors": ["E201"],
                "joint_states": {"wheel_left": 0.0, "wheel_right": 0.0},
                "active_topics": ["/scan", "/odom"]
                },
                {
                "robot_id": "agv_02",
                "model": "B2",
                "firmware": "v1.5",
                "timestamp": "2026-01-05T10:13:00Z",
                "errors": [],
                "joint_states": {"wheel_left": 1.5, "wheel_right": 1.5},
                "active_topics": ["/scan", "/odom", "/cmd_vel"]
                }
            ]
            }

            测试 5：获取历史
            GET http://localhost:8000/api/v1/snapshot-ingestion/history/agv_01?limit=5
            Header: X-API-Key: edge-adapter-ros-key

            测试 6：统计信息
            GET http://localhost:8000/api/v1/snapshot-ingestion/stats
            Header: X-API-Key: edge-adapter-ros-key
            
            测试 7：机器人列表
            GET http://localhost:8000/api/v1/snapshot-ingestion/robots
            Header: X-API-Key: edge-adapter-ros-key