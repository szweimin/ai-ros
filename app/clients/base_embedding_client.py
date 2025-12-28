from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingClient(ABC):
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成文本嵌入向量"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """返回嵌入向量的维度"""
        pass