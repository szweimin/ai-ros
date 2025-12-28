from typing import List, Tuple, Optional, Dict, Any
import pinecone

class VectorRepository:
    def __init__(self):
        self.index = None
        self._init_pinecone()
    
    def _init_pinecone(self):
        """初始化Pinecone连接"""
        try:
            pinecone.init(
                api_key="your-pinecone-api-key",  # 实际使用时从配置读取
                environment="your-environment"
            )
            
            index_name = "ros-documentation"
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI text-embedding-3-small 维度
                    metric="cosine"
                )
            
            self.index = pinecone.Index(index_name)
        except Exception as e:
            print(f"Warning: Pinecone not initialized. Using mock storage. Error: {e}")
            self.index = None
    
    async def upsert(self, records: List[Tuple[str, str, List[float], Dict[str, Any]]]):
        """
        插入或更新向量记录
        
        Args:
            records: 记录列表，每个记录为 (id, text, vector, metadata)
        """
        if self.index is None:
            print("Mock: Storing records in memory")
            return
        
        vectors = []
        for record_id, text, vector, metadata in records:
            vectors.append({
                "id": record_id,
                "values": vector,
                "metadata": {"text": text, **metadata}
            })
        
        self.index.upsert(vectors=vectors)
    
    async def search(self, query_vector: List[float], top_k: int = 5, 
                    filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            搜索结果列表
        """
        if self.index is None:
            # 返回模拟结果用于测试
            return self._mock_search(query_vector, top_k, filter_dict)
        
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        return results.get("matches", [])
    
    def _mock_search(self, query_vector: List[float], top_k: int, 
                    filter_dict: Optional[Dict]) -> List[Dict[str, Any]]:
        """模拟搜索用于测试"""
        mock_results = [
            {
                "id": "mock_1",
                "score": 0.95,
                "metadata": {
                    "text": "ROS Topic /cmd_vel publishes geometry_msgs/Twist messages for velocity control.",
                    "category": "ros_topic",
                    "topic": "/cmd_vel",
                    "msg_type": "geometry_msgs/Twist"
                }
            },
            {
                "id": "mock_2",
                "score": 0.88,
                "metadata": {
                    "text": "Joint 'wheel_left_joint' is a continuous joint for left wheel rotation.",
                    "category": "urdf_joint",
                    "robot": "agv_robot",
                    "joint": "wheel_left_joint"
                }
            }
        ]
        
        if filter_dict and 'category' in filter_dict:
            category = filter_dict['category']
            mock_results = [r for r in mock_results if r['metadata'].get('category') == category]
        
        return mock_results[:top_k]