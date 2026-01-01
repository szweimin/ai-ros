from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class QueryContext:
    """查询上下文"""
    query: str
    top_k: int = 5
    diagnostic_info: Optional[Dict[str, Any]] = None
    runtime_state: Optional[Dict[str, Any]] = None

class RAGPromptBuilder:
    """RAG提示词构建器"""
    
    @staticmethod
    def build_rag_prompt(
        query: str, 
        contexts: List[str], 
        runtime_context: str = ""
    ) -> str:
        """构建RAG查询的提示词"""
        
        # 构建文档上下文
        docs_context = ""
        for i, context in enumerate(contexts):
            docs_context += f"文档 {i+1}:\n"
            docs_context += f"内容: {context[:500]}...\n"
            docs_context += "---\n"
        
        # 基础系统提示
        system_prompt = f"""你是一个专业的ROS机器人工程师助手。基于以下文档和用户问题，提供详细、准确的回答。

可用文档：
{docs_context}

用户问题：{query}

请基于以上文档内容回答用户问题。如果文档中有相关信息，请引用具体文档内容。如果文档中没有足够信息，可以基于你的知识提供建议，但要明确说明这不在文档中。

回答要求：
1. 专业准确，使用ROS相关术语
2. 结构清晰，分点说明
3. 如有必要，提供代码示例
4. 引用相关文档编号
"""
        
        if runtime_context:
            system_prompt += f"\n运行时上下文:\n{runtime_context}\n"
        
        return system_prompt
    
    @staticmethod
    def build_diagnostic_prompt(
        query: str,
        contexts: List[str],
        runtime_context: str = "",
        error_codes: Optional[List[str]] = None,
        runtime_state: Optional[Any] = None
    ) -> str:
        """构建诊断分析的提示词"""
        
        # 构建文档上下文
        docs_context = ""
        for i, context in enumerate(contexts):
            docs_context += f"文档 {i+1}:\n"
            docs_context += f"内容: {context[:500]}...\n"
            docs_context += "---\n"
        
        prompt = f"""作为机器人故障诊断专家，分析以下故障情况：

用户问题：{query}
"""
        
        if error_codes:
            prompt += f"检测到的错误代码: {', '.join(error_codes)}\n"
        
        if runtime_context:
            prompt += f"运行时上下文:\n{runtime_context}\n"
        
        if docs_context:
            prompt += f"\n相关文档信息：\n{docs_context}\n"
        
        prompt += """
请进行综合分析：
1. 确定最可能的根本原因（按可能性排序）
2. 提供详细的排查步骤
3. 给出具体的修复建议
4. 如有多个错误，分析它们之间的关联性
5. 提供预防措施建议

请按以下格式回答：
## 综合分析
[总体分析]

## 根本原因分析
1. [原因1] (可能性: XX%)
   - 理由: ...
   - 排查步骤: ...
   - 修复方案: ...

## 紧急操作建议
[立即采取的操作]

## 长期预防措施
[预防建议]
"""
        
        return prompt
    
    @staticmethod
    def build_error_analysis_prompt(
        error_codes: List[str],
        contexts: List[str],
        runtime_context: str = "",
        runtime_state: Optional[Any] = None
    ) -> str:
        """构建错误分析的提示词"""
        
        # 构建文档上下文
        docs_context = ""
        for i, context in enumerate(contexts):
            docs_context += f"文档 {i+1}:\n"
            docs_context += f"内容: {context[:500]}...\n"
            docs_context += "---\n"
        
        prompt = f"""作为机器人故障诊断专家，深入分析以下错误：

错误代码: {', '.join(error_codes)}
"""
        
        if runtime_context:
            prompt += f"运行时状态:\n{runtime_context}\n"
        
        if docs_context:
            prompt += f"\n相关文档：\n{docs_context}\n"
        
        prompt += """
请进行深入分析：
1. 错误原因深度分析
2. 逐步排查流程
3. 详细修复方案
4. 验证步骤
5. 预防措施

请提供专业、详细的工程级分析。
"""
        
        return prompt

# 为了向后兼容，同时导出RAGPromptBuilder和PromptBuilder
class PromptBuilder(RAGPromptBuilder):
    """兼容旧版本的PromptBuilder"""
    pass

# 导出模块
__all__ = ['RAGPromptBuilder', 'PromptBuilder', 'QueryContext']
