from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text, select, desc
from sqlalchemy.dialects.postgresql import insert
from typing import List, Optional, Dict, Any
import json
import numpy as np
from datetime import datetime
import logging

from ..core.config import settings
from ..models.database_models import Base, ROSDocumentChunk, QueryHistory

logger = logging.getLogger(__name__)

class DatabaseRepository:
    def __init__(self):
        # 将postgresql:// 转换为 postgresql+asyncpg://
        self.database_url = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def init_db(self):
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            # 启用pgvector扩展
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
            
            # 检查是否需要添加向量列
            await self._check_and_add_vector_column(conn)


    async def _check_and_add_vector_column(self, conn):
        """检查并添加向量列（如果使用pgvector）"""
        try:
            # 先检查表是否存在
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'ros_document_chunks'
                )
            """))
            
            table_exists = result.scalar()
            if not table_exists:
                logger.info("Table ros_document_chunks does not exist, will be created")
                return
            
            # 检查embeddings列类型
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ros_document_chunks' 
                AND column_name = 'embedding_vector'
            """))
            
            column_info = result.fetchone()
            if not column_info:
                # 先检查pgvector扩展
                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                except Exception as e:
                    logger.warning(f"Could not create vector extension: {e}")
                    return
                
                # 添加向量列
                try:
                    await conn.execute(text("""
                        ALTER TABLE ros_document_chunks 
                        ADD COLUMN IF NOT EXISTS embedding_vector vector(384)
                    """))
                    logger.info("Added embedding_vector column")
                except Exception as e:
                    logger.warning(f"Could not add vector column: {e}")
                    # 继续使用JSON列存储向量
                    
        except Exception as e:
            logger.warning(f"Error checking/adding vector column: {e}")
    
   
   
    async def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        插入或更新文档块 - 使用原生SQL避免pgvector类型问题
        """
        if not chunks:
            return 0
        
        async with self.async_session() as session:
            inserted_count = 0  
            for chunk in chunks:
                try:
                    metadata = chunk.get("metadata", {})
                    embedding = chunk.get("embedding", [])
                    
                    # 使用原生SQL插入，避免embedding_vector列的类型问题
                    sql = text("""
                        INSERT INTO ros_document_chunks 
                        (chunk_id, text, embedding, doc_metadata, category, source_id, created_at, updated_at)
                        VALUES (:chunk_id, :text, :embedding, :doc_metadata, :category, :source_id, NOW(), NOW())
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            text = EXCLUDED.text,
                            embedding = EXCLUDED.embedding,
                            doc_metadata = EXCLUDED.doc_metadata,
                            category = EXCLUDED.category,
                            source_id = EXCLUDED.source_id,
                            updated_at = NOW()
                    """)
                    
                    params = {
                        "chunk_id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "embedding": json.dumps(embedding) if embedding else None,
                        "doc_metadata": json.dumps(metadata),
                        "category": metadata.get("category", "unknown"),
                        "source_id": metadata.get("source_id", "unknown")
                    }
                    
                    await session.execute(sql, params)
                    inserted_count += 1
                    
                    if inserted_count % 10 == 0:
                        print(f"Inserted {inserted_count} chunks...")
                        
                except Exception as e:
                    print(f"Error inserting chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            try:
                await session.commit()
                print(f"Successfully committed {inserted_count} chunks")
            except Exception as e:
                print(f"Error committing transaction: {e}")
                await session.rollback()
                inserted_count = 0
            return inserted_count
    
    async def search_similar_chunks(self, query_embedding: List[float], 
                                   top_k: int = 5, 
                                   filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        搜索相似的文档块（支持向量相似度搜索）
        
        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            filter_dict: 过滤条件
            
        Returns:
            相似文档块列表
        """
        try:
            # 尝试使用pgvector进行向量搜索
            return await self._vector_search(query_embedding, top_k, filter_dict)
        except Exception as e:
            logger.warning(f"Vector search failed, using fallback: {e}")
            # 降级到文本相似度搜索
            return await self._text_search_fallback(query_embedding, top_k, filter_dict)
   
    
    async def _vector_search(self, query_embedding: List[float], 
                            top_k: int, 
                            filter_dict: Optional[Dict]) -> List[Dict[str, Any]]:
        """使用pgvector进行向量搜索"""
        async with self.async_session() as session:
            # 构建向量搜索查询
            vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # 基础查询
            query = text("""
                SELECT 
                    chunk_id,
                    text,
                    doc_metadata,
                    1 - (embedding_vector <=> :query_vector) as similarity
                FROM ros_document_chunks
                WHERE embedding_vector IS NOT NULL
            """)
            
            params = {"query_vector": vector_str}
            
            # 添加过滤条件
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(f"doc_metadata->>'{key}' = :{key}")
                    params[key] = str(value)
                
                if conditions:
                    query = text(str(query) + " AND " + " AND ".join(conditions))
            
            # 添加排序和限制
            query = text(str(query) + " ORDER BY similarity DESC LIMIT :limit")
            params["limit"] = top_k
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            
            # 正确解析metadata
            results = []
            for row in rows:
                metadata = row[2]
                if isinstance(metadata, str):
                    try:
                        metadata_dict = json.loads(metadata)
                    except:
                        metadata_dict = {}
                else:
                    metadata_dict = metadata or {}
                
                results.append({
                    "id": row[0],
                    "score": float(row[3]) if row[3] else 0.0,
                    "metadata": {
                        "text": row[1],
                        **metadata_dict
                    }
                })
            
            return results
    
    
    async def upsert_chunks_with_vector(self, chunks: List[Dict[str, Any]]) -> int:
        """
        插入或更新文档块，正确填充embedding_vector列
        """
        async with self.async_session() as session:
            inserted_count = 0
            
            for chunk in chunks:
                try:
                    metadata = chunk.get("metadata", {})
                    embedding = chunk.get("embedding", [])
        
                    vector_str = chunk.get("embedding_vector_str", [])
                    # 方法1：使用更简单的SQL，让PostgreSQL自动转换类型
                    sql = text("""
                        INSERT INTO ros_document_chunks 
                        (chunk_id, text, embedding, embedding_vector, doc_metadata, category, source_id, created_at, updated_at)
                        VALUES (
                            :chunk_id, 
                            :text, 
                            :embedding,
                            :embedding_vector,
                            :doc_metadata,
                            :category,
                            :source_id,
                            NOW(),
                            NOW()
                        )
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            text = EXCLUDED.text,
                            embedding = EXCLUDED.embedding,
                            embedding_vector = EXCLUDED.embedding_vector,
                            doc_metadata = EXCLUDED.doc_metadata,
                            category = EXCLUDED.category,
                            source_id = EXCLUDED.source_id,
                            updated_at = NOW()
                    """)
                    
                    # 注意：直接传递JSON字符串和向量字符串，让PostgreSQL进行类型推断
                    params = {
                        "chunk_id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "embedding": json.dumps(embedding),  # 已经是JSON字符串
                        "embedding_vector": vector_str,      # 已经是pgvector格式字符串
                        "doc_metadata": json.dumps(metadata), # 已经是JSON字符串
                        "category": metadata.get("category", "unknown"),
                        "source_id": metadata.get("source_id", "unknown")
                    }
                    
                    await session.execute(sql, params)
                    inserted_count += 1
                    
                    print(f"Inserted chunk {chunk['chunk_id']} with vector")
                    
                except Exception as e:
                    print(f"Error inserting chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            try:
                await session.commit()
                print(f"Successfully committed {inserted_count} chunks with vectors")
            except Exception as e:
                print(f"Error committing transaction: {e}")
                await session.rollback()
                inserted_count = 0
            return inserted_count
    

    async def _text_search_fallback(self, query_embedding: List[float], 
                                   top_k: int, 
                                   filter_dict: Optional[Dict]) -> List[Dict[str, Any]]:
        """文本搜索降级方案"""
        async with self.async_session() as session:
            query = select(ROSDocumentChunk).where(
                ROSDocumentChunk.embedding.is_not(None)
            )
            
            # 添加过滤条件
            if filter_dict:
                for key, value in filter_dict.items():
                    query = query.where(
                        ROSDocumentChunk.doc_metadata[key].astext == str(value)
                    )
            
            result = await session.execute(query)
            chunks = result.scalars().all()
            
            # 计算余弦相似度
            similarities = []
            for chunk in chunks:
                if chunk.embedding:
                    try:
                        if isinstance(chunk.embedding, str):
                            chunk_embedding = json.loads(chunk.embedding)
                        else:
                            chunk_embedding = chunk.embedding
                            
                        if len(chunk_embedding) == len(query_embedding):
                            similarity = self._cosine_similarity(chunk_embedding, query_embedding)
                            similarities.append((chunk, similarity))
                    except Exception as e:
                        logger.debug(f"Error calculating similarity: {e}")
                        continue
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 返回结果
            results = []
            for chunk, similarity in similarities[:top_k]:
                # 解析metadata
                metadata = chunk.doc_metadata
                if isinstance(metadata, str):
                    try:
                        metadata_dict = json.loads(metadata)
                    except:
                        metadata_dict = {}
                else:
                    metadata_dict = metadata or {}
                
                results.append({
                    "id": chunk.chunk_id,
                    "score": float(similarity),
                    "metadata": {
                        "text": chunk.text,
                        **metadata_dict
                    }
                })
            
            return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def get_chunks_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """按类别获取文档块"""
        async with self.async_session() as session:
            query = select(ROSDocumentChunk).where(
                ROSDocumentChunk.category == category
            ).limit(limit)
            
            result = await session.execute(query)
            chunks = result.scalars().all()
            
            results = []
            for chunk in chunks:
                # 解析metadata
                metadata = chunk.doc_metadata
                if isinstance(metadata, str):
                    try:
                        metadata_dict = json.loads(metadata)
                    except:
                        metadata_dict = {}
                else:
                    metadata_dict = metadata or {}
                
                results.append({
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "metadata": metadata_dict,
                    "category": chunk.category
                })
            
            return results
    
    async def save_query_history(self, query: str, answer: str, 
                               sources: Optional[List] = None, 
                               confidence: float = 0.0) -> int:
        """保存查询历史"""
        async with self.async_session() as session:
            query_history = QueryHistory(
                query=query,
                answer=answer,
                sources=sources or [],
                confidence=confidence
            )
            session.add(query_history)
            await session.commit()
            return query_history.id
    
    async def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取查询历史"""
        async with self.async_session() as session:
            query = select(QueryHistory).order_by(
                desc(QueryHistory.created_at)
            ).limit(limit)
            
            result = await session.execute(query)
            history = result.scalars().all()
            
            return [{
                "id": item.id,
                "query": item.query,
                "answer": item.answer[:100] + "..." if len(item.answer) > 100 else item.answer,
                "confidence": item.confidence,
                "created_at": item.created_at.isoformat()
            } for item in history]