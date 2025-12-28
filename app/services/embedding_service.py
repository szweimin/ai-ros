from typing import List, Optional
from ..clients.local_embedding_client import LocalEmbeddingClient
from ..clients.ollama_embedding_client import OllamaEmbeddingClient
from ..clients.openai_embedding_client import OpenAIEmbeddingClient
from ..clients.base_embedding_client import BaseEmbeddingClient
from ..core.config import settings

class EmbeddingService:
    def __init__(self):
        self.client: BaseEmbeddingClient = self._init_embedding_client()
        
    def _init_embedding_client(self) -> BaseEmbeddingClient:
        """根据配置初始化嵌入客户端"""
        embedding_service = settings.embedding_service
        
        if embedding_service == "openai" and settings.openai_api_key:
            print("Using OpenAI embedding service")
            return OpenAIEmbeddingClient(
                api_key=settings.openai_api_key,
                model="text-embedding-3-small"
            )
        elif embedding_service == "ollama":
            print("Using Ollama embedding service")
            return OllamaEmbeddingClient(
                host=settings.ollama_host,
                model="nomic-embed-text"
            )
        else:
            print(f"Using local embedding service with model: {settings.local_embedding_model}")
            return LocalEmbeddingClient(
                model_name=settings.local_embedding_model
            )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        为文本列表生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        if not texts:
            return []
        
        return await self.client.embed(texts)
    
    @property
    def dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.client.dimension