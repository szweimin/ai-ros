from typing import Dict, Any, List
import re
from ...models.schemas import ROSTopic

class TopicParser:
    def __init__(self):
        self.topic_pattern = re.compile(r'^/[a-zA-Z0-9_/]+$')
        self.msg_type_pattern = re.compile(r'^[a-zA-Z0-9_]+/[a-zA-Z0-9_]+$')
    
    def validate_topic(self, topic: str) -> bool:
        """验证ROS Topic格式"""
        return bool(self.topic_pattern.match(topic)) if topic else False
    
    def validate_msg_type(self, msg_type: str) -> bool:
        """验证消息类型格式"""
        return bool(self.msg_type_pattern.match(msg_type)) if msg_type else False
    
    def parse_topic(self, topic_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析单个ROS Topic文档
        
        Args:
            topic_doc: ROS Topic文档
            
        Returns:
            包含text和metadata的字典
        """
        try:
            # 验证必要字段
            if not topic_doc or 'topic' not in topic_doc:
                raise ValueError("Missing topic field")
            
            topic = topic_doc.get('topic', '').strip()
            if not topic:
                raise ValueError("Topic is empty")
            
            if 'type' not in topic_doc:
                raise ValueError(f"Missing type field for topic {topic}")
            
            msg_type = topic_doc.get('type', '').strip()
            if not msg_type:
                raise ValueError(f"Type is empty for topic {topic}")
            
            # 获取其他字段，确保不为None
            description = topic_doc.get('description', 'No description provided') or 'No description provided'
            rate = topic_doc.get('rate', 'unknown') or 'unknown'
            publisher = topic_doc.get('publisher')
            subscribers = topic_doc.get('subscribers') or []
            
            # 确保subscribers是列表
            if not isinstance(subscribers, list):
                subscribers = []
            
            # 构建文本描述
            text_parts = [
                f"ROS Topic: {topic}",
                f"Message Type: {msg_type}",
                f"Description: {description}",
                f"Publish Rate: {rate}"
            ]
            
            if publisher:
                text_parts.append(f"Publisher: {publisher}")
            
            if subscribers:
                # 过滤掉None值
                valid_subscribers = [sub for sub in subscribers if sub]
                if valid_subscribers:
                    subs_text = ", ".join(valid_subscribers)
                    text_parts.append(f"Subscribers: {subs_text}")
            
            text = ". ".join(text_parts) + "."
            
            # 构建metadata
            metadata = {
                "category": "ros_topic",
                "topic": topic,
                "msg_type": msg_type,
                "rate": rate,
                "description": description,
                "has_subscribers": len(valid_subscribers) > 0 if subscribers else False
            }
            
            if publisher:
                metadata["publisher"] = publisher
            
            if subscribers and valid_subscribers:
                metadata["subscriber_count"] = len(valid_subscribers)
                metadata["subscribers"] = valid_subscribers
            
            return {
                "text": text,
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"Error parsing topic {topic_doc.get('topic', 'unknown')}: {e}")
            raise
    
    
        # 修改 topic_parser.py 中的 parse_topics 方法
    def parse_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量解析ROS Topics - 支持字典和Pydantic模型"""
        chunks = []
        
        for topic_data in topics:
            try:
                # 如果传入的是Pydantic模型，转换为字典
                if hasattr(topic_data, 'dict'):
                    topic_dict = topic_data.dict()
                else:
                    # 已经是字典
                    topic_dict = topic_data
                
                chunk = self.parse_topic(topic_dict)
                chunks.append(chunk)
            except Exception as e:
                topic_name = topic_dict.get('topic', 'unknown') if 'topic_dict' in locals() else 'unknown'
                print(f"Error parsing topic {topic_name}: {e}")
        
        return chunks