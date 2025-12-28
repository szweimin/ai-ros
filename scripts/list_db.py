#!/usr/bin/env python3
"""
检查数据库中的URDF数据
"""

import asyncio
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from sqlalchemy import text
from app.repositories.database import DatabaseRepository
async def debug_database():
  
    db = DatabaseRepository()
    
    async with db.async_session() as session:
        print("🔍 检查数据库中的URDF数据")
        print("="*60)
        
        # 1. 查看表结构
        sql = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'ros_document_chunks'
            ORDER BY ordinal_position
        """
        result = await session.execute(text(sql))
        print("\n1. 表结构:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        # 2. 查看实际数据
        sql = """
            SELECT 
                chunk_id,
                category,
                LEFT(text, 100) as text_preview,
                LEFT(doc_metadata::text, 100) as metadata_preview
            FROM ros_document_chunks 
            WHERE category LIKE '%urdf%'
            ORDER BY created_at DESC
            LIMIT 10
        """
        result = await session.execute(text(sql))
        rows = result.fetchall()
        
        print(f"\n2. URDF相关数据 (共{len(rows)}条):")
        for i, row in enumerate(rows):
            print(f"\n   记录 {i+1}:")
            print(f"     chunk_id: {row[0]}")
            print(f"     类别: {row[1]}")
            print(f"     文本预览: {row[2]}")
            print(f"     元数据: {row[3]}")
        
        # 3. 统计数据
        sql = """
            SELECT 
                category,
                COUNT(*) as count,
                COUNT(DISTINCT source_id) as sources
            FROM ros_document_chunks 
            GROUP BY category
            ORDER BY count DESC
        """
        result = await session.execute(text(sql))
        print(f"\n3. 数据统计:")
        for row in result:
            print(f"   类别 {row[0]}: {row[1]}条记录, {row[2]}个来源")

if __name__ == "__main__":
    asyncio.run(debug_database())