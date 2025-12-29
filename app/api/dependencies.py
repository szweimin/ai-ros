from fastapi import Depends
from functools import lru_cache
from ..services.embedding_service import EmbeddingService
from ..services.llm_service import LLMService
from ..repositories.database import DatabaseRepository
from ..services.pipeline import ROSIngestionPipeline
from ..services.query_service import QueryService
from ..services.runtime_context import RuntimeContextBuilder  # 新增
from ..services.prompt_builder import RAGPromptBuilder  # 新增

# 依赖项
@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """返回一个缓存的 EmbeddingService 实例（避免每次请求重新加载模型）"""
    return EmbeddingService()

def get_database_repository() -> DatabaseRepository:
    return DatabaseRepository()

def get_llm_service() -> LLMService:
    return LLMService()

def get_runtime_context_builder() -> RuntimeContextBuilder:
    """获取运行时上下文构建器"""
    return RuntimeContextBuilder()

def get_prompt_builder() -> RAGPromptBuilder:
    """获取提示词构建器"""
    return RAGPromptBuilder()

def get_ingestion_pipeline(
    embedding: EmbeddingService = Depends(get_embedding_service),
    db_repo: DatabaseRepository = Depends(get_database_repository)
) -> ROSIngestionPipeline:
    return ROSIngestionPipeline(embedding, db_repo)

def get_query_service(
    embedding: EmbeddingService = Depends(get_embedding_service),
    db_repo: DatabaseRepository = Depends(get_database_repository),
    llm_service: LLMService = Depends(get_llm_service)
) -> QueryService:
    return QueryService(embedding, db_repo, llm_service)
