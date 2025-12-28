from typing import Dict, Any, List
import re
from ...models.schemas import ROSTopic

class TopicParser:
    def __init__(self):
        self.topic_pattern = re.compile(r'^/[a-zA-Z0-9_/]+$')
        self.msg_type_pattern = re.compile(r'^[a-zA-Z0-9_]+/[a-zA-Z0-9_]+$')
    
    def validate_topic(self, topic: str) -> bool:
        """验证ROS Topic格式"""
        return bool(self.topic_pattern.match(topic))
    
    def validate_msg_type(self, msg_type: str) -> bool:
        """验证消息类型格式"""
        return bool(self.msg_type_pattern.match(msg_type))
    
    def parse_topic(self, topic_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析单个ROS Topic文档
        
        Args:
            topic_doc: ROS Topic文档
            
        Returns:
            包含text和metadata的字典
        """
        # 验证必要字段
        if 'topic' not in topic_doc:
            raise ValueError("Missing required field: topic")
        if 'type' not in topic_doc:
            raise ValueError("Missing required field: type")
        
        # 构建文本描述
        topic = topic_doc['topic']
        msg_type = topic_doc['type']
        description = topic_doc.get('description', 'No description provided')
        rate = topic_doc.get('rate', 'unknown')
        publisher = topic_doc.get('publisher')
        subscribers = topic_doc.get('subscribers', [])
        
        text_parts = [
            f"ROS Topic: {topic}",
            f"Message Type: {msg_type}",
            f"Description: {description}",
            f"Publish Rate: {rate}"
        ]
        
        if publisher:
            text_parts.append(f"Publisher: {publisher}")
        
        if subscribers:
            subs_text = ", ".join(subscribers)
            text_parts.append(f"Subscribers: {subs_text}")
        
        text = ". ".join(text_parts) + "."
        
        # 构建metadata
        metadata = {
            "category": "ros_topic",
            "topic": topic,
            "msg_type": msg_type,
            "rate": rate,
            "publisher": publisher,
            "has_subscribers": len(subscribers) > 0
        }
        
        if subscribers:
            metadata["subscriber_count"] = len(subscribers)
        
        return {
            "text": text,
            "metadata": metadata
        }
    
    def parse_topics(self, topics: List[ROSTopic]) -> List[Dict[str, Any]]:
        """批量解析ROS Topics"""
        chunks = []
        
        for topic_data in topics:
            topic_dict = topic_data.dict()
            try:
                chunk = self.parse_topic(topic_dict)
                chunks.append(chunk)
            except Exception as e:
                print(f"Error parsing topic {topic_dict.get('topic')}: {e}")
        
        return chunks