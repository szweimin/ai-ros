import httpx
from typing import List
import numpy as np
from .base_embedding_client import BaseEmbeddingClient

class OllamaEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, host: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        """初始化Ollama嵌入客户端"""
        self.host = host.rstrip('/')
        self.model = model
        self._dimension = 768  # nomic-embed-text 的维度
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        使用Ollama生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                embeddings = []
                
                for text in texts:
                    response = await client.post(
                        f"{self.host}/api/embeddings",
                        json={
                            "model": self.model,
                            "prompt": text
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        embedding = data.get("embedding", [])
                        embeddings.append(embedding)
                    else:
                        print(f"Error from Ollama: {response.status_code}")
                        # 返回随机向量
                        embeddings.append(self._generate_random_embedding())
                
                return embeddings
                
        except Exception as e:
            print(f"Error generating Ollama embeddings: {e}")
            return self._generate_fallback_embeddings(texts)
    
    def _generate_random_embedding(self) -> List[float]:
        """生成随机向量"""
        return np.random.randn(self._dimension).tolist()
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成降级嵌入向量"""
        return [self._generate_random_embedding() for _ in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension