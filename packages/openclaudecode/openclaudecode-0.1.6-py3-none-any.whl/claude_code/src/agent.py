#!/usr/bin/env python3
"""
Claude Code Agent - Main agent orchestrator with tool integration
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from pathlib import Path

from .llm import OllamaClient, LLMResponse
from .gemini import GeminiClient
from .tools import ClaudeCodeTools, ToolResult

logger = logging.getLogger(__name__)

class ClaudeCodeAgent:
    """Main agent for Claude Code with tool integration"""
    
    def __init__(self, 
                 model_name: str = "qwen2.5:7b-instruct",
                 host: str = "http://192.168.170.76:11434",
                 workspace_root: str = None,
                 system_prompt: str = None,
                 num_ctx: int = 4096,
                 enable_thinking: bool = False,
                 provider: str = "ollama",
                 api_key: Optional[str] = None):
        
        self.model_name = model_name
        self.host = host
        self.workspace_root = Path(workspace_root or ".").resolve()
        self.num_ctx = num_ctx
        self.enable_thinking = enable_thinking
        
        # Initialize LLM client based on provider
        if provider == "gemini":
            self.llm_client = GeminiClient(api_key=api_key, model=model_name)
        else:
            self.llm_client = OllamaClient(host=host, model=model_name)
        self.tools = ClaudeCodeTools(str(self.workspace_root))
        
        # Default system prompt inspired by Claude Code
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
    
    def _get_default_system_prompt(self) -> str:
        """Get the default Claude Code system prompt"""
        return f"""You are Claude Code, an AI assistant specialized in software development and code analysis.

You have access to a comprehensive set of tools for file operations, code execution, web research, and task management. You are currently working in the directory: {self.workspace_root}

## Available Tools:
- **File Operations**: read, write, edit, multiedit
- **Search & Discovery**: glob, grep, ls
- **Code Execution**: bash
- **Jupyter Notebooks**: notebook_read, notebook_edit  
- **Web Operations**: web_fetch, web_search
- **Task Management**: todo_read, todo_write
- **Complex Tasks**: task (for autonomous sub-agents)

## Guidelines:
1. Be direct and efficient in your responses
2. Use tools appropriately for the user's requests
3. Always verify file operations and provide clear feedback
4. Use proper error handling and report issues clearly
5. For complex multi-step tasks, use the todo system to track progress
6. Prefer existing tools over writing new code
7. Follow security best practices

## Tool Usage:
- Read files before editing them
- Use glob/grep for file discovery
- Use bash for system operations and testing
- Use multiedit for complex file changes
- Break down complex tasks into smaller steps

Current workspace: {self.workspace_root}
Model: {self.model_name}

Be helpful, accurate, and efficient!"""

    def _create_tool_schemas(self) -> List[Dict[str, Any]]:
        """Create JSON schemas for all available tools"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read",
                    "description": "Read file from filesystem with line numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file to read"},
                            "offset": {"type": "integer", "description": "Line number to start reading from", "default": 0},
                            "limit": {"type": "integer", "description": "Number of lines to read", "default": 2000}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "write",
                    "description": "Write content to file (overwrites existing)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file to write"},
                            "content": {"type": "string", "description": "Content to write to file"}
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit", 
                    "description": "Edit file with exact string replacement",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file to edit"},
                            "old_string": {"type": "string", "description": "Exact string to replace"},
                            "new_string": {"type": "string", "description": "Replacement string"},
                            "replace_all": {"type": "boolean", "description": "Replace all occurrences", "default": False}
                        },
                        "required": ["file_path", "old_string", "new_string"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "multiedit",
                    "description": "Perform multiple edits to a file atomically",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file to edit"},
                            "edits": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "old_string": {"type": "string"},
                                        "new_string": {"type": "string"},
                                        "replace_all": {"type": "boolean", "default": False}
                                    },
                                    "required": ["old_string", "new_string"]
                                }
                            }
                        },
                        "required": ["file_path", "edits"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "glob",
                    "description": "Find files matching glob pattern",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Glob pattern to match"},
                            "path": {"type": "string", "description": "Directory to search in", "default": "."}
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "grep",
                    "description": "Search file contents using regex",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Regex pattern to search for"},
                            "include": {"type": "string", "description": "File pattern to include"},
                            "path": {"type": "string", "description": "Directory to search in", "default": "."}
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ls",
                    "description": "List files and directories", 
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path to list"},
                            "ignore": {"type": "array", "items": {"type": "string"}, "description": "Patterns to ignore"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Execute bash command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to execute"},
                            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 120}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "notebook_read",
                    "description": "Read Jupyter notebook with cells and outputs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "notebook_path": {"type": "string", "description": "Path to notebook file"}
                        },
                        "required": ["notebook_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "notebook_edit",
                    "description": "Edit Jupyter notebook cell",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "notebook_path": {"type": "string", "description": "Path to notebook file"},
                            "cell_number": {"type": "integer", "description": "Cell index to edit"},
                            "new_source": {"type": "string", "description": "New cell content"},
                            "cell_type": {"type": "string", "enum": ["code", "markdown"], "description": "Cell type"},
                            "edit_mode": {"type": "string", "enum": ["replace", "insert", "delete"], "default": "replace"}
                        },
                        "required": ["notebook_path", "cell_number", "new_source"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_fetch",
                    "description": "Fetch and analyze web content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to fetch"},
                            "prompt": {"type": "string", "description": "Analysis prompt for the content"}
                        },
                        "required": ["url", "prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "allowed_domains": {"type": "array", "items": {"type": "string"}},
                            "blocked_domains": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "todo_read",
                    "description": "Read current todo list",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "todo_write",
                    "description": "Write/update todo list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "todos": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string"},
                                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                                        "id": {"type": "string"}
                                    },
                                    "required": ["content", "status", "priority", "id"]
                                }
                            }
                        },
                        "required": ["todos"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "task",
                    "description": "Launch autonomous agent for complex tasks",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string", "description": "Short task description"},
                            "prompt": {"type": "string", "description": "Detailed task instructions"}
                        },
                        "required": ["description", "prompt"]
                    }
                }
            }
        ]
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool with given arguments"""
        try:
            if hasattr(self.tools, tool_name):
                tool_method = getattr(self.tools, tool_name)
                result = await tool_method(**arguments)
                return result
            else:
                return ToolResult("", error=f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolResult("", error=f"Tool execution error: {str(e)}")
    
    async def _process_tool_calls(self, tool_calls: List[Dict]) -> List[str]:
        """Process multiple tool calls and return results"""
        results = []
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            
            # Parse arguments if they're a string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    results.append(f"Error: Invalid JSON arguments for {function_name}")
                    continue
            
            result = await self._execute_tool(function_name, arguments)
            
            if result.error:
                results.append(f"Error in {function_name}: {result.error}")
            else:
                results.append(f"Tool {function_name} result: {result.content}")
        
        return results
    
    async def chat(self, user_message: str) -> str:
        """Simple chat without tools"""
        try:
            response = await self.llm_client.chat(
                user_message=user_message,
                system_prompt=self.system_prompt
            )
            return response.message.content
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error: {str(e)}"
    
    async def agent_response(self, user_message: str, max_iterations: int = 5) -> str:
        """Generate agent response with tool usage"""
        try:
            tools = self._create_tool_schemas()
            iterations = 0
            conversation = [{"role": "user", "content": user_message}]
            
            while iterations < max_iterations:
                iterations += 1
                
                # Get LLM response with tools
                response_data = await self.llm_client.generate_with_tools(
                    user_message=json.dumps(conversation),
                    tools=tools,
                    system_prompt=self.system_prompt
                )
                
                message = response_data.get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                
                # Add assistant message to conversation
                conversation.append({"role": "assistant", "content": content})
                
                # If no tool calls, we're done
                if not tool_calls:
                    return content
                
                # Execute tool calls
                tool_results = await self._process_tool_calls(tool_calls)
                
                # Add tool results to conversation
                for i, result in enumerate(tool_results):
                    conversation.append({
                        "role": "tool", 
                        "content": result,
                        "tool_call_id": str(i)
                    })
                
                # Continue the conversation with tool results
                continue_prompt = "Please continue based on the tool results above."
                conversation.append({"role": "user", "content": continue_prompt})
            
            return "Maximum iterations reached. Task may require manual intervention."
            
        except Exception as e:
            logger.error(f"Error in agent response: {e}")
            return f"Error: {str(e)}"
    
    async def stream_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """Stream agent response"""
        try:
            async for chunk in self.llm_client.stream_chat(
                user_message=user_message,
                system_prompt=self.system_prompt
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Error in stream response: {e}")
            yield f"Error: {str(e)}"
    
    async def interactive_mode(self, user_message: str) -> str:
        """Interactive mode - execute one tool at a time"""
        try:
            tools = self._create_tool_schemas()
            
            # Get LLM response with tools
            response_data = await self.llm_client.generate_with_tools(
                user_message=user_message,
                tools=tools,
                system_prompt=self.system_prompt + "\\n\\nYou are in interactive mode. Execute only ONE tool call at a time."
            )
            
            message = response_data.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                return content
            
            # Execute only the first tool call
            if tool_calls:
                tool_call = tool_calls[0]
                function_name = tool_call["function"]["name"] 
                arguments = tool_call["function"]["arguments"]
                
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        return f"Error: Invalid JSON arguments for {function_name}"
                
                result = await self._execute_tool(function_name, arguments)
                
                if result.error:
                    return f"Error in {function_name}: {result.error}"
                else:
                    return f"{content}\\n\\nTool {function_name} executed:\\n{result.content}"
            
            return content
            
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            return f"Error: {str(e)}"
    
    async def close(self):
        """Clean up resources"""
        await self.tools.close()
        await self.llm_client._client.aclose()