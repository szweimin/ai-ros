"""
更新依赖注入以包含诊断服务
"""
from fastapi import Depends
from functools import lru_cache
from ..services.embedding_service import EmbeddingService
from ..services.llm_service import LLMService
from ..repositories.database import DatabaseRepository
from ..services.pipeline import ROSIngestionPipeline
from ..services.query_service_with_diagnosis import QueryService
from ..services.runtime_context import RuntimeContextBuilder
from ..services.prompt_builder_with_diagnosis import RAGPromptBuilder
from ..services.diagnostic_service import DiagnosticService

# 依赖项
@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """返回一个缓存的 EmbeddingService 实例"""
    return EmbeddingService()

def get_database_repository() -> DatabaseRepository:
    return DatabaseRepository()

def get_llm_service() -> LLMService:
    return LLMService()

def get_runtime_context_builder() -> RuntimeContextBuilder:
    return RuntimeContextBuilder()

def get_prompt_builder() -> RAGPromptBuilder:
    return RAGPromptBuilder()

def get_diagnostic_service() -> DiagnosticService:
    return DiagnosticService()

def get_query_service(
    embedding: EmbeddingService = Depends(get_embedding_service),
    db_repo: DatabaseRepository = Depends(get_database_repository),
    llm_service: LLMService = Depends(get_llm_service)
) -> QueryService:
    return QueryService(embedding, db_repo, llm_service)

def get_ingestion_pipeline(
    embedding: EmbeddingService = Depends(get_embedding_service),
    db_repo: DatabaseRepository = Depends(get_database_repository)
) -> ROSIngestionPipeline:
    return ROSIngestionPipeline(embedding, db_repo)
