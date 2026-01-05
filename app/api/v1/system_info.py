from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def root():
    return {
        "message": "ROS Documentation System with Fault Diagnosis",
        "version": "2.0.0",
        "environment": settings.environment,
        "features": {
            "static_knowledge": True,
            "runtime_integration": True,
            "fault_diagnosis_trees": True,
            "engineering_diagnostics": True
        }
    }


@router.get("/endpoints")
async def list_endpoints():
    return {
        "ingest_ros_topics": "POST /api/v1/ros/topics/ingest",
        "ingest_urdf": "POST /api/v1/ros/urdf/ingest",
        "ingest_safety_ops": "POST /api/v1/ros/operation/ingest",
        "query": "POST /api/v1/ros/query",
        "query_with_runtime": "POST /api/v1/ros/query-with-runtime",
        "diagnostic_analyze": "POST /api/v1/diagnostics/analyze",
        "available_diagnoses": "GET /api/v1/diagnostics/available",
        "get_fault_tree": "GET /api/v1/diagnostics/tree/{error_code}",
        "query_history": "GET /api/v1/ros/history"
    }