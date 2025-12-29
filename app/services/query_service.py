from typing import List, Dict, Any, Optional
import asyncio
from .embedding_service import EmbeddingService
from .llm_service import LLMService
from ..repositories.database import DatabaseRepository
from ..services.runtime_context import RuntimeContextBuilder
from ..services.prompt_builder import RAGPromptBuilder
from ..models.schemas import RuntimeState, QueryWithRuntimeRequest

class QueryService:
    def __init__(self, embedding_service: EmbeddingService, 
                 database_repo: DatabaseRepository,
                 llm_service: LLMService):
        self.embedding = embedding_service
        self.db = database_repo
        self.llm = llm_service
        self.runtime_builder = RuntimeContextBuilder()
        self.prompt_builder = RAGPromptBuilder()

    async def query_with_runtime(self, request: QueryWithRuntimeRequest) -> Dict[str, Any]:
        """
        执行带有运行时状态的RAG查询
        
        Args:
            request: 包含查询和运行时状态的请求
            
        Returns:
            查询结果
        """
        try:
            # 生成查询向量
            query_vectors = await self.embedding.embed([request.query])
            query_vector = query_vectors[0]
            
            # 如果有运行时状态，构建运行时上下文
            runtime_context = ""
            error_search_terms = []
            
            if request.runtime_state:
                runtime_context = self.runtime_builder.build_runtime_context(request.runtime_state)
                error_search_terms = self.runtime_builder.extract_error_codes_for_search(
                    request.runtime_state.errors
                )
            
            # 构建搜索条件
            filter_dict = None
            if request.runtime_state and request.runtime_state.robot_id:
                filter_dict = {"robot": request.runtime_state.robot_id}
            
            # 执行向量搜索（主要搜索）
            search_results = await self.db.search_similar_chunks(
                query_embedding=query_vector,
                top_k=request.top_k,
                filter_dict=filter_dict
            )
            
            # 如果有错误代码，额外搜索错误相关文档
            error_results = []
            if error_search_terms:
                error_vectors = await self.embedding.embed(error_search_terms)
                for error_vector in error_vectors:
                    more_results = await self.db.search_similar_chunks(
                        query_embedding=error_vector,
                        top_k=3,  # 每个错误代码取3个相关文档
                        filter_dict={"category": "ros_safety"}  # 主要搜索安全/错误文档
                    )
                    error_results.extend(more_results)
            
            # 合并结果，去重
            all_results = self._merge_and_deduplicate_results(search_results, error_results)
            
            # 使用LLM生成回答（包含运行时上下文）
            answer = await self._generate_llm_answer_with_runtime(
                query=request.query,
                search_results=all_results,
                runtime_context=runtime_context,
                error_codes=request.runtime_state.errors if request.runtime_state else None
            )
            
            # 提取源信息
            sources = self._extract_sources(all_results)
            
            # 计算置信度（基于最相关结果）
            confidence = all_results[0]["score"] if all_results else 0.0
            
            # 保存查询历史
            await self.db.save_query_history(
                query=f"[Runtime] {request.query}",
                answer=answer,
                sources=sources,
                confidence=confidence
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "result_count": len(all_results),
                "runtime_context_used": runtime_context if request.runtime_state else None
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "answer": f"Error processing query with runtime state: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "result_count": 0
            }
    
    async def _generate_llm_answer_with_runtime(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        runtime_context: str = "",
        error_codes: Optional[List[str]] = None
    ) -> str:
        """使用LLM基于搜索结果和运行时上下文生成回答"""
        if not search_results:
            if runtime_context:
                return f"I don't have specific documentation for your query, but based on the runtime state: {runtime_context}. Please check the robot's current configuration and error logs."
            else:
                return "I don't have enough information to answer this question based on the available documentation."
        
        # 提取上下文文本
        contexts = [result["metadata"]["text"] for result in search_results]
        
        # 判断是否为错误分析查询
        is_error_query = error_codes is not None and len(error_codes) > 0
        
        # 构建提示词
        if is_error_query:
            prompt = self.prompt_builder.build_error_analysis_prompt(
                error_codes=error_codes,
                contexts=contexts,
                runtime_context=runtime_context
            )
        else:
            prompt = self.prompt_builder.build_rag_prompt(
                query=query,
                contexts=contexts,
                runtime_context=runtime_context
            )
        
        # 生成回答
        answer = await self.llm.generate_answer_from_prompt(prompt)
        
        # 添加引用
        if search_results:
            ref_text = " ".join([f"[Context {i+1}]" for i in range(len(search_results))])
            if "Sources:" not in answer:
                answer = f"{answer}\n\n**Sources**: {ref_text}"
        
        return answer
    
    def _merge_and_deduplicate_results(self, primary_results: List[Dict], secondary_results: List[Dict]) -> List[Dict]:
        """合并并去重搜索结果"""
        seen_ids = set()
        merged = []
        
        # 添加主要结果
        for result in primary_results:
            result_id = result.get("id")
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                merged.append(result)
        
        # 添加次要结果（如果不在主结果中）
        for result in secondary_results:
            result_id = result.get("id")
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                merged.append(result)
        
        # 按分数排序
        merged.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return merged[:10]  # 限制总数为10个
    
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