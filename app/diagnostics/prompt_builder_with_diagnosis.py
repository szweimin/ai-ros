
"""
更新查询服务以集成故障诊断树功能
"""
from typing import List, Dict, Any, Optional
import asyncio
from .embedding_service import EmbeddingService
from .llm_service import LLMService
from ..repositories.database import DatabaseRepository
from ..services.runtime_context import RuntimeContextBuilder
from ..services.prompt_builder_with_diagnosis import RAGPromptBuilder
from ..services.diagnostic_service import DiagnosticService
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
        self.diagnostic_service = DiagnosticService()
    
    async def query_with_runtime(self, request: QueryWithRuntimeRequest) -> Dict[str, Any]:
        """
        执行带有运行时状态的RAG查询（增强版，集成诊断树）
        """
        try:
            # 生成查询向量
            query_vectors = await self.embedding.embed([request.query])
            query_vector = query_vectors[0]
            
            # 构建过滤条件
            filter_dict = None
            if request.runtime_state and request.runtime_state.robot_id:
                filter_dict = {"robot": request.runtime_state.robot_id}
            
            # 执行向量搜索
            search_results = await self.db.search_similar_chunks(
                query_embedding=query_vector,
                top_k=request.top_k,
                filter_dict=filter_dict
            )
            
            # 如果有错误代码，额外搜索错误相关文档
            error_results = []
            if request.runtime_state and request.runtime_state.errors:
                error_search_terms = self.runtime_builder.extract_error_codes_for_search(
                    request.runtime_state.errors
                )
                
                if error_search_terms:
                    error_vectors = await self.embedding.embed(error_search_terms[:3])  # 限制数量
                    for error_vector in error_vectors:
                        more_results = await self.db.search_similar_chunks(
                            query_embedding=error_vector,
                            top_k=2,
                            filter_dict={"category": "ros_safety"}
                        )
                        error_results.extend(more_results)
            
            # 合并结果
            all_results = self._merge_and_deduplicate_results(search_results, error_results)
            
            # 构建运行时上下文
            runtime_context = ""
            if request.runtime_state:
                runtime_context = self.runtime_builder.build_runtime_context(request.runtime_state)
            
            # 使用增强的提示词构建器生成回答
            answer = await self._generate_llm_answer_with_diagnosis(
                query=request.query,
                search_results=all_results,
                runtime_context=runtime_context,
                runtime_state=request.runtime_state,
                error_codes=request.runtime_state.errors if request.runtime_state else None
            )
            
            # 提取源信息
            sources = self._extract_sources(all_results)
            
            # 计算置信度
            confidence = all_results[0]["score"] if all_results else 0.0
            
            # 保存查询历史
            await self.db.save_query_history(
                query=f"[Diagnosis] {request.query}",
                answer=answer,
                sources=sources,
                confidence=confidence
            )
            
            # 如果涉及错误诊断，添加诊断摘要
            diagnostic_summary = None
            if request.runtime_state and request.runtime_state.errors:
                try:
                    diagnosis = await self.diagnostic_service.diagnose_multiple_errors(
                        request.runtime_state.errors,
                        request.runtime_state
                    )
                    diagnostic_summary = {
                        "error_count": len(request.runtime_state.errors),
                        "primary_error": diagnosis.get("primary_error"),
                        "severity": diagnosis.get("primary_severity"),
                        "most_likely_cause": diagnosis.get("combined_causes", [{}])[0].get("description", "Unknown") if diagnosis.get("combined_causes") else "Unknown"
                    }
                except Exception as e:
                    diagnostic_summary = {"error": str(e)}
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "result_count": len(all_results),
                "runtime_context_used": runtime_context if request.runtime_state else None,
                "diagnostic_summary": diagnostic_summary
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
    
    async def _generate_llm_answer_with_diagnosis(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        runtime_context: str = "",
        runtime_state: Optional[RuntimeState] = None,
        error_codes: Optional[List[str]] = None
    ) -> str:
        """使用LLM基于搜索结果和诊断树生成回答"""
        if not search_results and not error_codes:
            return "I don't have enough information to answer this question based on the available documentation."
        
        # 提取上下文文本
        contexts = [result["metadata"]["text"] for result in search_results]
        
        # 判断是否为错误诊断查询
        is_error_diagnosis = error_codes is not None and len(error_codes) > 0
        
        # 构建提示词
        if is_error_diagnosis:
            prompt = await self.prompt_builder.build_diagnostic_prompt(
                query=query,
                contexts=contexts,
                runtime_context=runtime_context,
                error_codes=error_codes,
                runtime_state=runtime_state
            )
        else:
            prompt = self.prompt_builder.build_rag_prompt(
                query=query,
                contexts=contexts,
                runtime_context=runtime_context
            )
        
        # 生成回答
        answer = await self.llm.generate_answer_from_prompt(prompt)
        
        # 如果没有自动添加引用，手动添加
        if search_results and "Context" not in answer and "Source" not in answer:
            ref_text = " ".join([f"[Context {i+1}]" for i in range(len(search_results))])
            answer = f"{answer}\n\n**Documentation References**: {ref_text}"
        
        return answer
    
    async def diagnostic_query(self, error_codes: List[str], runtime_state: RuntimeState) -> Dict[str, Any]:
        """
        专门的诊断查询（直接使用故障树，不进行向量搜索）
        
        Args:
            error_codes: 错误代码列表
            runtime_state: 运行时状态
            
        Returns:
            诊断结果
        """
        try:
            # 生成诊断计划
            diagnosis_plan = await self.diagnostic_service.generate_diagnosis_plan(
                error_codes, runtime_state
            )
            
            # 获取相关的文档上下文（可选）
            if error_codes:
                # 搜索错误相关文档
                error_search_terms = self.runtime_builder.extract_error_codes_for_search(error_codes)
                if error_search_terms:
                    error_vectors = await self.embedding.embed(error_search_terms[:2])
                    search_results = []
                    for vector in error_vectors:
                        results = await self.db.search_similar_chunks(
                            query_embedding=vector,
                            top_k=2,
                            filter_dict={"category": "ros_safety"}
                        )
                        search_results.extend(results)
                    
                    contexts = [result["metadata"]["text"] for result in search_results]
                else:
                    contexts = []
            else:
                contexts = []
            
            # 构建运行时上下文
            runtime_context = self.runtime_builder.build_runtime_context(runtime_state)
            
            # 使用诊断专用提示词生成详细分析
            if contexts:
                prompt = await self.prompt_builder.build_error_analysis_prompt(
                    error_codes=error_codes,
                    contexts=contexts,
                    runtime_context=runtime_context,
                    runtime_state=runtime_state
                )
                
                detailed_analysis = await self.llm.generate_answer_from_prompt(prompt)
            else:
                detailed_analysis = "No additional documentation context available for detailed analysis."
            
            # 保存查询历史
            await self.db.save_query_history(
                query=f"[Diagnosis] Errors: {', '.join(error_codes)}",
                answer=detailed_analysis[:500],  # 只保存摘要
                sources=[],
                confidence=0.8  # 诊断树有较高的置信度
            )
            
            return {
                "status": "diagnosed",
                "diagnosis_plan": diagnosis_plan,
                "detailed_analysis": detailed_analysis,
                "error_codes": error_codes,
                "robot_id": runtime_state.robot_id,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Diagnostic query failed: {str(e)}",
                "error_codes": error_codes
            }
    
    def _merge_and_deduplicate_results(self, primary_results: List[Dict], secondary_results: List[Dict]) -> List[Dict]:
        """合并并去重搜索结果"""
        seen_ids = set()
        merged = []
        
        for result in primary_results:
            result_id = result.get("id")
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                merged.append(result)
        
        for result in secondary_results:
            result_id = result.get("id")
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                merged.append(result)
        
        merged.sort(key=lambda x: x.get("score", 0), reverse=True)
        return merged[:10]
    
    async def query(self, query_text: str, top_k: int = 5, 
                   filter_category: Optional[str] = None) -> Dict[str, Any]:
        """
        原始查询方法（向后兼容）
        """
        # ... 原有代码保持不变 ...
    
    async def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取查询历史"""
        return await self.db.get_query_history(limit)
    
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
    
    async def get_available_diagnoses(self) -> Dict[str, Any]:
        """获取可用的诊断信息"""
        error_codes = self.diagnostic_service.get_available_error_codes()
        
        # 获取每个错误代码的简要信息
        diagnoses_info = []
        for code in error_codes[:10]:  # 限制数量
            tree = self.diagnostic_service.fault_trees.get(code)
            if tree:
                diagnoses_info.append({
                    "error_code": code,
                    "description": tree.description,
                    "category": tree.category,
                    "severity": tree.severity,
                    "cause_count": len(tree.causes)
                })
        
        return {
            "available_error_codes": error_codes,
            "total_diagnoses": len(error_codes),
            "diagnoses_info": diagnoses_info
        }
