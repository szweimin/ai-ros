
from typing import List, Optional
from ..models.schemas import RuntimeState

class RAGPromptBuilder:
    @staticmethod
    def build_rag_prompt(
        query: str, 
        contexts: List[str], 
        runtime_context: str = "",
        is_technical_query: bool = False
    ) -> str:
        """
        构建RAG提示词
        
        Args:
            query: 用户查询
            contexts: 知识上下文列表
            runtime_context: 运行时上下文
            is_technical_query: 是否为技术性查询
            
        Returns:
            完整的提示词
        """
        # 构建上下文块
        context_block = ""
        for i, context in enumerate(contexts, 1):
            context_block += f"[Context {i}]\n{context}\n\n"
        
        # 基础系统角色
        system_role = """You are an industrial robotics assistant specialized in ROS (Robot Operating System). 
Your task is to help diagnose and solve robotics issues by combining:
1. Static knowledge from documentation
2. Dynamic runtime state information

You must provide:
1. Direct answers based on available information
2. Clear explanations when the context is insufficient
3. Citations to your sources using [Context X]
4. Actionable recommendations when possible"""
        
        # 构建提示词
        prompt = f"""## System Role
{system_role}

## Current Situation"""
        
        # 添加运行时状态（如果有）
        if runtime_context:
            prompt += f"""
### Runtime State
{runtime_context}

### Relevant Documentation
{context_block}"""
        else:
            prompt += f"""
### Relevant Documentation
{context_block}"""
        
        # 添加查询
        prompt += f"""### Question
{query}

### Your Response Format
1. **Direct Answer**: Concise answer to the question
2. **Explanation**: How you arrived at this conclusion
3. **Sources**: Citations from the context [Context X]
4. **Recommendations**: Next steps if applicable

### Answer:"""
        
        return prompt
    
    @staticmethod
    def build_error_analysis_prompt(
        error_codes: List[str],
        contexts: List[str],
        runtime_context: str = ""
    ) -> str:
        """
        构建错误分析专用提示词
        
        Args:
            error_codes: 错误代码列表
            contexts: 知识上下文
            runtime_context: 运行时上下文
            
        Returns:
            错误分析提示词
        """
        error_str = ", ".join(error_codes)
        
        prompt = f"""## System Role
You are a robotics error diagnosis specialist. Analyze the following error codes and provide:
1. Likely causes
2. Immediate troubleshooting steps
3. Reference to relevant documentation

## Current Situation"""
        
        if runtime_context:
            prompt += f"""
### Runtime State
{runtime_context}"""
        
        prompt += f"""
### Active Error Codes
{error_str}

### Relevant Documentation
"""
        
        for i, context in enumerate(contexts, 1):
            prompt += f"[Context {i}]\n{context}\n\n"
        
        prompt += f"""### Error Analysis Request
Please analyze these error codes in the context provided.

### Analysis Format
1. **Error Description**: What each error code typically means
2. **Likely Causes**: Based on runtime state and documentation
3. **Immediate Actions**: Steps to diagnose/resolve
4. **Prevention**: How to avoid in future
5. **Sources**: Citations from documentation [Context X]

### Analysis:"""
        
        return prompt
