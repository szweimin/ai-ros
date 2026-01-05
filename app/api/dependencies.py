"""
更新依赖注入以包含诊断服务
"""
from fastapi import Depends
from functools import lru_cache
from ..services.embedding_service import EmbeddingService
from ..services.llm_service import LLMService
from ..repositories.database import DatabaseRepository
from ..services.pipeline import ROSIngestionPipeline
from ..services.query_service import QueryService
from ..services.diagnostic_service import DiagnosticService
from app.services.fleet_diagnostic_service import FleetDiagnosticService
# 依赖项
@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """返回一个缓存的 EmbeddingService 实例"""
    return EmbeddingService()

def get_database_repository() -> DatabaseRepository:
    return DatabaseRepository()

def get_llm_service() -> LLMService:
    return LLMService()

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

def get_fleet_diagnostic_service() -> FleetDiagnosticService:
    """
    获取车队诊断服务实例
    """
    diagnostic_service = get_diagnostic_service()
    return FleetDiagnosticService(diagnostic_service)