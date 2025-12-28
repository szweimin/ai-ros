# test_database.py
import asyncio
import os
import sys
from sqlalchemy import text
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.repositories.database import DatabaseRepository

async def test_database():
    print("Testing database connection...")
    db_repo = DatabaseRepository()
    
    # 1. 测试数据库连接
    try:
        async with db_repo.async_session() as session:
            result = await session.execute(text("SELECT 1"))
            test_result = result.scalar()
            print(f"✓ Database connection successful: SELECT 1 = {test_result}")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    # 2. 测试表是否存在
    try:
        async with db_repo.async_session() as session:
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'ros_document_chunks'
                )
            """))
            table_exists = result.scalar()
            print(f"✓ Table check: ros_document_chunks exists = {table_exists}")
            
            if table_exists:
                # 检查表结构
                result = await session.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'ros_document_chunks'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                print("Table columns:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
    except Exception as e:
        print(f"✗ Error checking tables: {e}")
    
    # 3. 测试插入数据
    print("\nTesting data insertion...")
    try:
        test_chunk = {
            "chunk_id": "test_001",
            "text": "Test ROS topic: /cmd_vel publishes geometry_msgs/Twist messages",
            "embedding": [0.1] * 384,  # 384维向量
            "metadata": {
                "category": "ros_topic",
                "topic": "/cmd_vel",
                "msg_type": "geometry_msgs/Twist",
                "source_id": "test_source"
            },
            "category": "ros_topic"
        }
        
        inserted = await db_repo.upsert_chunks([test_chunk])
        print(f"✓ Successfully inserted {inserted} test chunks")
        
        # 4. 验证插入的数据
        async with db_repo.async_session() as session:
            result = await session.execute(text(
                "SELECT COUNT(*) FROM ros_document_chunks WHERE chunk_id = 'test_001'"
            ))
            count = result.scalar()
            print(f"✓ Verified: Found {count} records with chunk_id='test_001'")
            
            # 显示插入的数据
            if count > 0:
                result = await session.execute(text(
                    "SELECT chunk_id, text, category FROM ros_document_chunks WHERE chunk_id = 'test_001'"
                ))
                row = result.fetchone()
                print(f"  Chunk ID: {row[0]}")
                print(f"  Text: {row[1][:50]}...")
                print(f"  Category: {row[2]}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"✗ Error inserting test data: {e}")
        traceback.print_exc()
        return False

async def test_pgvector():
    """测试pgvector扩展"""
    print("\nTesting pgvector extension...")
    db_repo = DatabaseRepository()
    
    try:
        async with db_repo.async_session() as session:
            # 检查pgvector扩展
            result = await session.execute(text(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            ))
            vector_ext = result.scalar()
            
            if vector_ext:
                print("✓ pgvector extension is installed")
                
                # 检查向量列
                result = await session.execute(text("""
                    SELECT column_name, udt_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'ros_document_chunks' 
                    AND column_name = 'embedding_vector'
                """))
                vector_col = result.fetchone()
                
                if vector_col:
                    print(f"✓ Vector column exists: {vector_col[0]} ({vector_col[1]})")
                else:
                    print("✗ Vector column does not exist")
            else:
                print("✗ pgvector extension is not installed")
                
    except Exception as e:
        print(f"✗ Error checking pgvector: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    
    success = asyncio.run(test_database())
    asyncio.run(test_pgvector())
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Database tests PASSED")
    else:
        print("✗ Database tests FAILED")
    print("=" * 60)