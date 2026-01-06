# api/v1/__init__.py
from .health import router as health_router
from .system_info import router as system_info_router
from .ros import router as ros_router
from .diagnostics import router as diagnostics_router
from .fleet_diagnostics import router as fleet_diagnostics_router
from .snapshot_ingestion import router as snapshot_ingestion_router

__all__ = [
    "health_router",
    "system_info_router", 
    "ros_router",
    "diagnostics_router",
    "fleet_diagnostics_router",
    "snapshot_ingestion_router"
]