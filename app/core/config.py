import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "ROS Documentation System"
    environment: str = "development"
    
    # 数据库配置
    database_url: str = os.getenv("DATABASE_URL", "postgresql://ai_user:ai_password@182.61.39.44:5432/ai_infra")
    
    # Snapshot Ingestion 配置 ✅ - 使用更简单的处理方式
    snapshot_valid_api_keys: str = os.getenv("SNAPSHOT_VALID_API_KEYS", "edge-adapter-ros-key,edge-adapter-plc-key,edge-adapter-simulator-key")
    
    # 获取拆分后的列表
    @property
    def snapshot_valid_api_keys_list(self) -> list:
        return [key.strip() for key in self.snapshot_valid_api_keys.split(",") if key.strip()]
    
    snapshot_max_history: int = int(os.getenv("SNAPSHOT_MAX_HISTORY", "1000"))
    snapshot_analysis_enabled: bool = os.getenv("SNAPSHOT_ANALYSIS_ENABLED", "true").lower() == "true"
    snapshot_storage_type: Literal["memory", "redis", "database"] = os.getenv("SNAPSHOT_STORAGE_TYPE", "memory")
    
    # Redis 配置（用于快照存储）
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # 快照处理配置
    snapshot_processing_timeout: int = int(os.getenv("SNAPSHOT_PROCESSING_TIMEOUT", "30"))
    snapshot_cleanup_days: int = int(os.getenv("SNAPSHOT_CLEANUP_DAYS", "30"))
    snapshot_max_batch_size: int = int(os.getenv("SNAPSHOT_MAX_BATCH_SIZE", "100"))
    
    # Ollama配置
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "mistral:latest")
    
    # OpenAI配置（可选）
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # LLM服务提供商配置
    llm_provider: Literal["ollama", "openai"] = os.getenv("LLM_PROVIDER", "ollama")
    
    # 嵌入模型配置
    embedding_service: Literal["local", "openai", "ollama"] = os.getenv("EMBEDDING_SERVICE", "local")
    local_embedding_model: str = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # 向量维度（根据模型自动设置）
    embedding_dimension: int = 384  # all-MiniLM-L6-v2 的维度
    
    # 其他配置
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()