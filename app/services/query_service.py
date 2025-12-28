from typing import List, Dict, Any, Optional
import asyncio
from .embedding_service import EmbeddingService
from .llm_service import LLMService
from ..repositories.database import DatabaseRepository

class QueryService:
    def __init__(self, embedding_service: EmbeddingService, 
                 database_repo: DatabaseRepository,
                 llm_service: LLMService):
        self.embedding = embedding_service
        self.db = database_repo
        self.llm = llm_service
    
    async def query(self, query_text: str, top_k: int = 5, 
                   filter_category: Optional[str] = None) -> Dict[str, Any]:
        """
        执行RAG查询
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            filter_category: 过滤类别
            
        Returns:
            查询结果
        """
        try:
            # 生成查询向量
            query_vectors = await self.embedding.embed([query_text])
            query_vector = query_vectors[0]
            
            # 构建过滤条件
            filter_dict = None
            if filter_category:
                filter_dict = {"category": filter_category}
            
            # 搜索相似文档
            search_results = await self.db.search_similar_chunks(
                query_embedding=query_vector,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
            # 使用LLM生成回答
            answer = await self._generate_llm_answer(query_text, search_results)
            
            # 提取源信息
            sources = self._extract_sources(search_results)
            
            # 保存查询历史
            await self.db.save_query_history(
                query=query_text,
                answer=answer,
                sources=sources,
                confidence=search_results[0]["score"] if search_results else 0.0
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": search_results[0]["score"] if search_results else 0.0,
                "result_count": len(search_results)
            }
            
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "result_count": 0
            }
    
    async def _generate_llm_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """使用LLM基于搜索结果生成回答"""
        if not search_results:
            return "I don't have enough information to answer this question based on the available documentation."
        
        # 提取上下文
        contexts = [result["metadata"]["text"] for result in search_results]
        
        # 汇总上下文
        if len(contexts) > 3:
            context = await self.llm.summarize_context(contexts)
        else:
            context = "\n\n".join(contexts)
        
        # 生成回答
        answer = await self.llm.generate_answer(query, context)
        
        # 添加引用
        if search_results:
            ref_text = " ".join([f"[Source {i+1}]" for i in range(len(search_results))])
            answer = f"{answer}\n\nReferences: {ref_text}"
        
        return answer
    
    def _extract_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从搜索结果中提取源信息"""
        sources = []
        for i, result in enumerate(search_results):
            metadata = result["metadata"]
            sources.append({
                "id": result["id"],
                "text": metadata["text"][:150] + "..." if len(metadata["text"]) > 150 else metadata["text"],
                "category": metadata.get("category", "unknown"),
                "score": result["score"],
                "metadata": {k: v for k, v in metadata.items() if k != "text"}
            })
        return sources
    
    async def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取查询历史"""
        return await self.db.get_query_history(limit)