from typing import List, Dict, Any, Optional
import httpx
import asyncio
from openai import OpenAI
from ..core.config import settings

class LLMService:
    def __init__(self):
        
        self.use_openai = False  # 添加这个属性
        self.openai_client = None
        # 优先使用配置决定的LLM提供商
        self.llm_provider = getattr(settings, 'LLM_PROVIDER', 'ollama').lower()
        
        # 只有明确配置使用openai时才初始化OpenAI客户端
        if self.llm_provider == 'openai' and settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            print(f"Using OpenAI LLM service with model: {settings.openai_model}")
        else:
            # 默认使用Ollama
            self.llm_provider = 'ollama'
            print(f"Using Ollama LLM service with model: {settings.ollama_model}")
        # Ollama配置
        self.ollama_host = settings.ollama_host
        self.ollama_model = settings.ollama_model
    
    async def generate_answer(self, query: str, context: str) -> str:
        """
        基于上下文生成回答
        
        Args:
            query: 用户查询
            context: 相关上下文
            
        Returns:
            生成的回答
        """
        if self.llm_provider == 'openai' and self.openai_client:
            try:
                return await self._generate_with_openai(query, context)
            except Exception as e:
                print(f"OpenAI generation failed, falling back to Ollama: {e}")
                return await self._generate_with_ollama(query, context)
        else:
            # 默认使用Ollama
            return await self._generate_with_ollama(query, context)
        

    
    async def _generate_with_openai(self, query: str, context: str) -> str:
        """使用OpenAI生成回答"""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a ROS (Robot Operating System) documentation assistant. "
                                 "Answer questions based on the provided context. "
                                 "If the context doesn't contain relevant information, "
                                 "say 'I don't have enough information about that.'"
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating answer with OpenAI: {e}")
            return await self._generate_with_ollama(query, context)
    
    async def _generate_with_ollama(self, query: str, context: str) -> str:
        """使用Ollama生成回答"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": f"""You are a ROS (Robot Operating System) documentation assistant.

Context:
{context}

Based on the context above, answer this question: {query}

If the context doesn't contain relevant information, say "I don't have enough information about that."

Answer:""",
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 500
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "No response generated").strip()
                else:
                    print(f"Error from Ollama: {response.status_code}")
                    return f"I cannot generate an answer right now. Error: {response.status_code}"
                
        except Exception as e:
            print(f"Error generating answer with Ollama: {e}")
            return f"I encountered an error while generating the answer. Please try again."
    
    async def summarize_context(self, contexts: List[str]) -> str:
        """汇总多个上下文"""
        combined_context = "\n\n".join(contexts)
        
        if len(contexts) <= 3:
            return combined_context
        
        # 如果上下文太多，使用LLM进行摘要
        summary_prompt = f"""Please summarize the following ROS documentation contexts into a concise overview:

{combined_context}

Summary:"""
        
        if self.use_openai:
            try:
                response = self.openai_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
            except:
                # 如果摘要失败，返回前3个上下文
                return "\n\n".join(contexts[:3])
        else:
            # 对于Ollama，直接返回前3个上下文以避免过长
            return "\n\n".join(contexts[:3])