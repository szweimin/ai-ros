from typing import List, Dict, Any
import uuid
import asyncio
import json
from .embedding_service import EmbeddingService
from ..repositories.database import DatabaseRepository

class ROSIngestionPipeline:
    def __init__(self, embedding_service: EmbeddingService, database_repo: DatabaseRepository):
        self.embedding = embedding_service
        self.db = database_repo
    
    async def ingest_chunks(self, base_id: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理并存储chunks - 修复embedding_vector格式问题
        """
        if not chunks:
            return {"status": "error", "message": "No chunks to process"}
        
        try:
            texts = [chunk["text"] for chunk in chunks]
            
            print(f"Generating embeddings for {len(texts)} texts...")
            vectors = await self.embedding.embed(texts)
            print(f"Generated {len(vectors)} vectors, each with dimension {len(vectors[0]) if vectors else 0}")
            
            # 准备数据库记录
            db_chunks = []
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                chunk_id = f"{base_id}_{i:04d}"
                
                # 确保metadata包含必要字段
                metadata = chunk.get("metadata", {})
                metadata["source_id"] = base_id
                
                # 确保category存在
                if "category" not in metadata:
                    metadata["category"] = "unknown"
                
                # 要插入pgvector，必须把list转换成库兼容的字符串格
                vector_str = self._vector_to_pg_string(vector)
              
                db_chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk["text"],
                    "embedding": vector,  # Python列表格式，用于JSON存储
                    "embedding_vector_str": vector_str,  # pgvector字符串格式
                    "metadata": metadata,
                    "category": metadata["category"]
                })
            
            # 存储到数据库 - 使用修复后的upsert_chunks
            print(f"Inserting {len(db_chunks)} chunks into database...")
            inserted_count = await self.db.upsert_chunks_with_vector(db_chunks)
            print(f"Successfully inserted {inserted_count} chunks")
            
            if inserted_count > 0:
                return {
                    "status": "success",
                    "message": f"Successfully ingested {inserted_count} chunks",
                    "chunk_count": inserted_count
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to insert any chunks into database"
                }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in ingestion pipeline: {error_details}")
            return {
                "status": "error",
                "message": f"Error ingesting chunks: {str(e)}"
            }
    
    def _vector_to_pg_string(self, vector: List[float]) -> str:
        """将向量转换为pgvector接受的字符串格式"""
        if not vector:
            return "NULL"
        
        # pgvector期望的格式: '[1.0, 2.0, 3.0]'
        # 确保所有元素都是浮点数，没有空格
        vector_str = "[" + ",".join(str(float(v)) for v in vector) + "]"
        
        # 验证格式
        try:
            # 确保能解析为JSON数组
            json.loads(vector_str)
            print(f"Vector string format valid: {vector_str[:50]}...")
        except Exception as e:
            print(f"Invalid vector string format: {e}")
            # 返回空字符串，让数据库处理为NULL
            return "NULL"
        
        return vector_str