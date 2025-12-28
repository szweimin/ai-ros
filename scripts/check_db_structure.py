#!/usr/bin/env python3
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def check_structure():
    DATABASE_URL = "postgresql+asyncpg://ai_user:ai_password@182.61.39.44:5432/ai_infra"
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # 检查表结构
        result = await session.execute(text("""
            SELECT 
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'ros_document_chunks'
            ORDER BY ordinal_position
        """))
        
        print("=" * 60)
        print("ros_document_chunks 表结构")
        print("=" * 60)
        
        columns = result.fetchall()
        for col in columns:
            print(f"{col[0]:20} | {col[1]:15} | {col[2]:15} | 可为空: {col[4]}")
        
        # 检查是否有数据
        result = await session.execute(text("SELECT COUNT(*) FROM ros_document_chunks"))
        count = result.scalar()
        print(f"\n表中记录数: {count}")
        
        if count > 0:
            # 查看embedding_vector样例
            result = await session.execute(text("""
                SELECT 
                    id, 
                    chunk_id,
                    pg_typeof(embedding_vector) as vector_type,
                    embedding_vector IS NOT NULL as has_vector,
                    CASE 
                        WHEN embedding_vector IS NOT NULL THEN 
                            array_dims(embedding_vector::real[])
                        ELSE 'NULL'
                    END as vector_dims
                FROM ros_document_chunks 
                LIMIT 5
            """))
            
            print("\n前5条记录的向量信息:")
            samples = result.fetchall()
            for sample in samples:
                print(f"ID {sample[0]}: {sample[1]}, 类型: {sample[2]}, 有向量: {sample[3]}, 维度: {sample[4]}")

if __name__ == "__main__":
    asyncio.run(check_structure())