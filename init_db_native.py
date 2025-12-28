#!/usr/bin/env python3
"""
使用原生SQL创建数据库表
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def init_database_native():
    """使用原生SQL初始化数据库"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    
    # 数据库URL
    DATABASE_URL = "postgresql://ai_user:ai_password@182.61.39.44:5432/ai_infra"
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    print("连接到数据库...")
    
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("1. 启用pgvector扩展...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            print("2. 删除现有表（如果存在）...")
            await conn.execute(text("DROP TABLE IF EXISTS ros_document_chunks CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS query_history CASCADE"))
            
            print("3. 使用原生SQL创建表...")
            await conn.execute(text("""
                CREATE TABLE ros_document_chunks(
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(100) UNIQUE NOT NULL,
                    text TEXT NOT NULL,
                    embedding JSONB,
                    embedding_vector vector(384),  -- 使用pgvector类型
                    doc_metadata JSONB NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    source_id VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await conn.execute(text("""
                CREATE TABLE query_history (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources JSONB,
                    confidence FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            print("4. 创建索引...")
            await conn.execute(text("CREATE INDEX idx_chunk_id ON ros_document_chunks(chunk_id)"))
            await conn.execute(text("CREATE INDEX idx_category ON ros_document_chunks(category)"))
            await conn.execute(text("CREATE INDEX idx_source_id ON ros_document_chunks(source_id)"))
            await conn.execute(text("CREATE INDEX idx_category_source ON ros_document_chunks(category, source_id)"))
            await conn.execute(text("CREATE INDEX idx_embedding_vector ON ros_document_chunks USING ivfflat (embedding_vector vector_cosine_ops)"))
            await conn.execute(text("CREATE INDEX idx_doc_metadata ON ros_document_chunks USING GIN (doc_metadata)"))
            await conn.execute(text("CREATE INDEX idx_created_at ON query_history(created_at)"))
            
            print("✅ 数据库表创建成功！")
            
            # 验证
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('ros_document_chunks', 'query_history')
            """))
            
            tables = result.fetchall()
            print(f"✅ 验证通过，创建了 {len(tables)} 个表")
            
            # 检查列类型
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ros_document_chunks'
                AND column_name = 'embedding_vector'
            """))
            
            col_info = result.fetchone()
            if col_info:
                print(f"✅ embedding_vector列类型: {col_info[1]}")
            
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(init_database_native())
    if success:
        print("\n🎉 数据库初始化成功完成！")
        print("\n注意：由于使用了原生SQL创建表，您需要：")
        print("1. 修改 app/models/database_models.py，移除embedding_vector列的定义")
        print("2. 或者修改数据库仓库，直接使用原生SQL查询")
        sys.exit(0)
    else:
        print("\n💥 数据库初始化失败")
        sys.exit(1)