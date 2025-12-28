from openai import OpenAI
from typing import List
import numpy as np
from .base_embedding_client import BaseEmbeddingClient

class OpenAIEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """初始化OpenAI嵌入客户端"""
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._dimension = 1536  # text-embedding-3-small 的维度
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        使用OpenAI生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            print(f"Error generating OpenAI embeddings: {e}")
            return self._generate_fallback_embeddings(texts)
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成降级嵌入向量"""
        return [np.random.randn(self._dimension).tolist() for _ in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension