from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import uuid

from ...services.parsers.topic_parser import TopicParser
from ...services.parsers.urdf_parser import URDFParser
from ...services.parsers.safety_parser import SafetyParser
from ...services.pipeline import ROSIngestionPipeline
from ...services.query_service import QueryService
from ...models.schemas import (
    ROSTopic, ROSTopicsIngestRequest, URDFIngestRequest,
    SafetyOperationIngestRequest, QueryRequest, QueryResponse,
     QueryWithRuntimeRequest, RuntimeState  
)

from ..dependencies import get_ingestion_pipeline, get_query_service

router = APIRouter(prefix="/ros", tags=["ROS Documentation"])
@router.post("/topics/ingest")
async def ingest_ros_topics(
    request: ROSTopicsIngestRequest,
    pipeline: ROSIngestionPipeline = Depends(get_ingestion_pipeline)
) -> Dict[str, Any]:
    """
    导入ROS Topics文档
    """
    try:
        # 解析topics
        parser = TopicParser()
        chunks = parser.parse_topics(request.topics)
        
        # 生成基础ID
        base_id = f"ros_topic_{uuid.uuid4().hex[:8]}"
        
        # 处理并存储
        result = await pipeline.ingest_chunks(base_id, chunks)
        
        return {
            "status": "success",
            "message": f"Successfully ingested {len(request.topics)} ROS topics",
            "chunk_count": result.get("chunk_count", 0),
            "details": result
        } 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting ROS topics: {str(e)}")

@router.post("/urdf/ingest")
async def ingest_urdf(
    request: URDFIngestRequest,
    pipeline: ROSIngestionPipeline = Depends(get_ingestion_pipeline)
) -> Dict[str, Any]:
    """
    导入URDF文档
    """
    try:
        # 解析URDF
        parser = URDFParser()
        chunks = parser.parse_urdf(request.urdf_content, request.robot_name)
        
        # 生成基础ID
        base_id = f"urdf_{request.robot_name}_{uuid.uuid4().hex[:8]}"
        
        # 处理并存储
        result = await pipeline.ingest_chunks(base_id, chunks)
        
        return {
            "status": "success",
            "message": f"Successfully ingested URDF for robot '{request.robot_name}'",
            "chunk_count": result.get("chunk_count", 0),
            "details": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting URDF: {str(e)}")

@router.post("/operation/ingest")
async def ingest_safety_operation(
    request: SafetyOperationIngestRequest,
    pipeline: ROSIngestionPipeline = Depends(get_ingestion_pipeline)
) -> Dict[str, Any]:
    """
    导入安全/操作文档
    """
    try:
        # 解析安全操作
        parser = SafetyParser()
        chunks = parser.parse_operations(request.operations)
        
        # 生成基础ID
        base_id = f"operation_{uuid.uuid4().hex[:8]}"
        
        # 处理并存储
        result = await pipeline.ingest_chunks(base_id, chunks)
        
        return {
            "status": "success",
            "message": f"Successfully ingested {len(request.operations)} safety/operation documents",
            "chunk_count": result.get("chunk_count", 0),
            "details": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting safety operations: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_ros_docs(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service)
) -> QueryResponse:
    """
    查询ROS文档知识库
    """
    try:
        result = await query_service.query(
            query_text=request.query,
            top_k=request.top_k
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying documentation: {str(e)}")
    
@router.post("/query-with-runtime", response_model=QueryResponse)
async def query_ros_docs_with_runtime(
    request: QueryWithRuntimeRequest,
    query_service: QueryService = Depends(get_query_service)
) -> QueryResponse:
    """
    查询ROS文档知识库（带运行时状态）
    """
    try:
        result = await query_service.query_with_runtime(request)
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying documentation with runtime: {str(e)}")
    
@router.get("/history")
async def get_query_history(
    query_service: QueryService = Depends(get_query_service),
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    获取查询历史
    """
    try:
        history = await query_service.get_query_history(limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting query history: {str(e)}")