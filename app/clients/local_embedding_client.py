from sentence_transformers import SentenceTransformer
from typing import List
import asyncio
import numpy as np
from .base_embedding_client import BaseEmbeddingClient

class LocalEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """初始化本地嵌入模型"""
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        为文本列表生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        try:
            # 使用线程池处理嵌入计算，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                lambda: self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            )
            
            # 确保返回标准的Python列表
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            return embeddings
            
        except Exception as e:
            print(f"Error generating local embeddings: {e}")
            # 返回随机向量作为fallback
            return self._generate_fallback_embeddings(texts)
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成降级嵌入向量"""
        return [np.random.randn(self._dimension).tolist() for _ in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension