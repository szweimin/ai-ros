from typing import Dict, Any, List
from ...models.schemas import SafetyOperation

class SafetyParser:
    def __init__(self):
        pass
    
    def parse_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析安全/操作文档
        
        Args:
            operation: 安全操作文档
            
        Returns:
            包含text和metadata的字典
        """
        title = operation.get('title', 'Untitled Operation')
        content = operation.get('content', '')
        category = operation.get('category', 'operation')
        steps = operation.get('procedure_steps', [])
        
        # 构建文本
        text_parts = [f"Title: {title}", f"Category: {category}"]
        
        if content:
            text_parts.append(f"Description: {content}")
        
        if steps:
            steps_text = "; ".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
            text_parts.append(f"Procedure Steps: {steps_text}")
        
        text = ". ".join(text_parts) + "."
        
        # 构建metadata
        metadata = {
            "category": f"ros_{category}",
            "title": title,
            "operation_category": category,
            "has_steps": len(steps) > 0,
            "step_count": len(steps)
        }
        
        return {
            "text": text,
            "metadata": metadata
        }
    
    def parse_operations(self, operations: List[SafetyOperation]) -> List[Dict[str, Any]]:
        """批量解析安全操作文档"""
        chunks = []
        
        for op in operations:
            op_dict = op.dict()
            try:
                chunk = self.parse_operation(op_dict)
                chunks.append(chunk)
            except Exception as e:
                print(f"Error parsing operation {op_dict.get('title')}: {e}")
        
        return chunks