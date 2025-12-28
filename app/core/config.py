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
    
    # Ollama配置
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "mistral:latest")
    
    # OpenAI配置（可选）
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
      # LLM服务提供商配置 (新增) ✅
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