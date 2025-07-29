#!/usr/bin/env python3
"""
LLM Client for Claude Code - Ollama Integration
"""

import json
import httpx
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str
    content: str

@dataclass
class LLMResponse:
    message: Message
    usage: Optional[Dict] = None
    model: Optional[str] = None

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, host: str = "http://192.168.170.76:11434", model: str = "qwen2.5:7b-instruct", timeout: int = 300):
        self.host = host.rstrip('/')
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
    
    async def chat(self, user_message: str, tools: Optional[List[Dict]] = None, 
                   system_prompt: Optional[str] = None, stream: bool = False) -> LLMResponse:
        """Send a chat message to Ollama"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            response = await self._client.post(
                f"{self.host}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                result = response.json()
                return LLMResponse(
                    message=Message(
                        role=result["message"]["role"],
                        content=result["message"]["content"]
                    ),
                    model=result.get("model"),
                    usage=result.get("usage")
                )
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
    
    async def stream_chat(self, user_message: str, tools: Optional[List[Dict]] = None,
                         system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Stream a chat response from Ollama"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            async with self._client.stream(
                "POST",
                f"{self.host}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_lines():
                    if chunk:
                        try:
                            data = json.loads(chunk)
                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                                if content:
                                    yield content
                            
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
    
    async def generate_with_tools(self, user_message: str, tools: List[Dict],
                                 system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response with tool calling support"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        try:
            response = await self._client.post(
                f"{self.host}/api/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = await self._client.get(f"{self.host}/api/tags")
            response.raise_for_status()
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy"""
        try:
            response = await self._client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except Exception:
            return False