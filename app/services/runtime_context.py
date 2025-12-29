
from typing import Dict, Any, List, Optional
from ..models.schemas import RuntimeState

class RuntimeContextBuilder:
    @staticmethod
    def build_runtime_context(runtime_state: Optional[RuntimeState]) -> str:
        """
        构建运行时上下文描述
        
        Args:
            runtime_state: 运行时状态
            
        Returns:
            格式化的运行时上下文字符串
        """
        if not runtime_state:
            return "No runtime state available."
        
        parts = []
        
        # 添加机器人ID
        parts.append(f"Robot ID: {runtime_state.robot_id}")
        
        # 添加错误信息
        if runtime_state.errors:
            error_list = ", ".join(runtime_state.errors)
            parts.append(f"Active error codes: {error_list}.")
        
        # 添加活跃话题
        if runtime_state.active_topics:
            topic_list = ", ".join(runtime_state.active_topics)
            parts.append(f"Active ROS topics: {topic_list}.")
        
        # 添加参数
        if runtime_state.parameters:
            param_parts = []
            for key, value in runtime_state.parameters.items():
                param_parts.append(f"{key}={value}")
            param_str = "; ".join(param_parts)
            parts.append(f"Runtime parameters: {param_str}.")
        
        # 如果没有运行时信息
        if len(parts) == 1:  # 只有robot_id
            return f"Robot {runtime_state.robot_id} is currently running with no active errors or special state."
        
        return "\n".join(parts)
    
    @staticmethod
    def extract_error_codes_for_search(errors: Optional[List[str]]) -> List[str]:
        """
        从错误代码中提取用于搜索的关键词
        
        Args:
            errors: 错误代码列表
            
        Returns:
            用于向量搜索的关键词列表
        """
        if not errors:
            return []
        
        search_terms = []
        for error in errors:
            # 移除可能的E/E-前缀进行更通用的搜索
            if error.startswith('E'):
                error_num = error.lstrip('E-')
                search_terms.append(error)
                search_terms.append(f"error {error_num}")
                search_terms.append(f"error code {error_num}")
            else:
                search_terms.append(error)
                search_terms.append(f"error {error}")
        
        return search_terms
