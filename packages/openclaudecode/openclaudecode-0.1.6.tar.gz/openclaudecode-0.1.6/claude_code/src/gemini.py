#!/usr/bin/env python3
"""
Gemini Client for Claude Code - Google Gemini API Integration
"""

import os
import json
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

class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-pro-exp", timeout: int = 300):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable or api_key parameter is required")
        
        self.model = model
        self.timeout = timeout
        
        try:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=self.api_key)
            self._client = self.genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def chat(self, user_message: str, tools: Optional[List[Dict]] = None, 
                   system_prompt: Optional[str] = None, stream: bool = False) -> LLMResponse:
        """Send a chat message to Gemini"""
        try:
            # Combine system prompt and user message
            full_message = user_message
            if system_prompt:
                full_message = f"{system_prompt}\n\n{user_message}"
            
            # Generate response
            if stream:
                # For streaming, we'll use the stream_chat method
                response_content = ""
                async for chunk in self.stream_chat(user_message, tools, system_prompt):
                    response_content += chunk
                
                return LLMResponse(
                    message=Message(role="assistant", content=response_content),
                    model=self.model
                )
            else:
                response = await asyncio.to_thread(
                    self._client.generate_content, 
                    full_message
                )
                
                return LLMResponse(
                    message=Message(
                        role="assistant",
                        content=response.text if response.text else ""
                    ),
                    model=self.model,
                    usage={"prompt_tokens": 0, "completion_tokens": 0}  # Gemini doesn't provide detailed usage
                )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def stream_chat(self, user_message: str, tools: Optional[List[Dict]] = None,
                         system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Stream a chat response from Gemini"""
        try:
            # Combine system prompt and user message
            full_message = user_message
            if system_prompt:
                full_message = f"{system_prompt}\n\n{user_message}"
            
            # Generate streaming response
            response = await asyncio.to_thread(
                self._client.generate_content,
                full_message,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise
    
    async def generate_with_tools(self, user_message: str, tools: List[Dict],
                                 system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response with tool calling support (basic implementation)"""
        try:
            # Gemini function calling requires specific setup
            # For now, we'll do a basic implementation
            full_message = user_message
            if system_prompt:
                full_message = f"{system_prompt}\n\n{user_message}"
            
            response = await asyncio.to_thread(
                self._client.generate_content,
                full_message
            )
            
            return {
                "message": {
                    "role": "assistant",
                    "content": response.text if response.text else ""
                },
                "model": self.model,
                "done": True
            }
            
        except Exception as e:
            logger.error(f"Gemini tools error: {e}")
            raise
    
    async def list_models(self) -> List[str]:
        """List available Gemini models"""
        try:
            models = await asyncio.to_thread(self.genai.list_models)
            return [model.name for model in models if 'generateContent' in model.supported_generation_methods]
        except Exception as e:
            logger.error(f"Error listing Gemini models: {e}")
            return [self.model]
    
    async def health_check(self) -> bool:
        """Check if Gemini API is accessible"""
        try:
            response = await asyncio.to_thread(
                self._client.generate_content,
                "Hello"
            )
            return bool(response.text)
        except Exception:
            return False