#!/usr/bin/env python3
"""
Claude Code - Simple CLI-style Textual UI
A clean, terminal-native interface inspired by the official Claude Code
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Set
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Input, Static, Header, Footer
from textual.binding import Binding
from textual.reactive import reactive

from rich.console import RenderableType
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from .agent import ClaudeCodeAgent


class ChatMessage(Static):
    """Individual chat message in CLI style"""
    
    def __init__(self, content: str, role: str, timestamp: Optional[datetime] = None, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.role = role
        self.timestamp = timestamp or datetime.now()
        
    def render(self) -> RenderableType:
        """Render message in simple CLI style"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        
        if self.role == "user":
            # User messages with simple prompt style
            return Text.from_markup(f"[bold cyan]> [/bold cyan]{self.content}")
        elif self.role == "assistant":
            # Assistant messages with markdown but minimal styling
            return Markdown(self.content)
        elif self.role == "system":
            # System messages in dim style
            return Text.from_markup(f"[dim]{self.content}[/dim]")
        elif self.role == "tool":
            # Tool output in green
            return Text.from_markup(f"[green]Tool Output:[/green] {self.content}")
        else:
            return Text(self.content)


class ChatArea(ScrollableContainer):
    """Main chat area - scrollable container for messages"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        
    def add_message(self, content: str, role: str, timestamp: Optional[datetime] = None):
        """Add a new message to the chat"""
        message = ChatMessage(content, role, timestamp)
        self.messages.append(message)
        self.mount(message)
        self.scroll_end()
        
    def clear_messages(self):
        """Clear all messages"""
        for message in self.messages:
            message.remove()
        self.messages.clear()


class SimpleCLIInput(Input):
    """Simple input widget with command hints"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ClaudeCodeSimple(App):
    """Simple CLI-style Claude Code interface"""
    
    CSS = """
    /* Clean, minimal styling */
    Screen {
        background: $background;
    }
    
    Header {
        background: $primary;
        color: $text-muted;
        dock: top;
        height: 1;
    }
    
    Footer {
        background: $surface;
        color: $text-muted;
        dock: bottom;
        height: 1;
    }
    
    .chat-container {
        background: $surface;
        height: 1fr;
        padding: 1;
        border: none;
    }
    
    .input-container {
        background: $surface;
        height: 3;
        padding: 0 1;
        border-top: solid $border;
    }
    
    .welcome-message {
        color: $text-muted;
        text-style: italic;
        margin: 1 0;
    }
    
    ChatMessage {
        margin: 0 0 1 0;
        padding: 0;
        background: transparent;
        border: none;
    }
    
    Input {
        background: $surface;
        border: solid $border;
        border-title-color: $text-muted;
    }
    
    Input:focus {
        border: solid $primary;
        border-title-color: $primary;
    }
    
    /* Ensure good contrast and clean look */
    Static {
        background: transparent;
    }
    """
    
    TITLE = "Claude Code"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, 
                 model_name: Optional[str] = None,
                 host: str = "http://192.168.170.76:11434",
                 workspace_path: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 num_ctx: int = 4096,
                 enable_thinking: bool = False,
                 provider: str = "ollama",
                 api_key: Optional[str] = None,
                 verbose: bool = False):
        super().__init__()
        
        # Configuration
        self.workspace_path = Path(workspace_path).resolve() if workspace_path else Path.cwd()
        self.model_name = model_name or ("gemini-2.5-flash-preview-05-20" if provider == "gemini" else "qwen2.5:7b-instruct")
        self.host = host
        self.num_ctx = num_ctx
        self.enable_thinking = enable_thinking
        self.provider = provider
        self.api_key = api_key
        self.verbose = verbose
        
        # Initialize agent
        self.agent = ClaudeCodeAgent(
            model_name=self.model_name,
            host=self.host,
            workspace_root=str(self.workspace_path),
            system_prompt=system_prompt,
            num_ctx=self.num_ctx,
            enable_thinking=self.enable_thinking,
            provider=self.provider,
            api_key=self.api_key,
            status_callback=self._handle_agent_status
        )
        
        # State
        self.files_in_context: Set[Path] = set()
        self.processing = reactive(False)
        
    def compose(self) -> ComposeResult:
        """Compose the simple interface"""
        yield Header()
        
        # Main chat area
        with Container(classes="chat-container"):
            yield ChatArea(id="chat")
            
        # Input area
        with Container(classes="input-container"):
            yield SimpleCLIInput(
                placeholder="/help for help, /status for your current setup",
                id="input"
            )
            
        yield Footer()
        
    def on_mount(self) -> None:
        """Initialize the interface"""
        # Show welcome message
        chat = self.query_one("#chat", ChatArea)
        chat.add_message(
            "Welcome to Claude Code!\n\n/help for help, /status for your current setup",
            "system"
        )
        
        # Update subtitle with current working directory
        cwd_name = self.workspace_path.name
        self.sub_title = f"cwd: {cwd_name}"
        
    def action_clear(self) -> None:
        """Clear the chat"""
        chat = self.query_one("#chat", ChatArea)
        chat.clear_messages()
        chat.add_message("Console cleared", "system")
        
    def action_cancel(self) -> None:
        """Cancel current operation"""
        if self.processing:
            self.processing = False
            chat = self.query_one("#chat", ChatArea)
            chat.add_message("Operation cancelled", "system")
            
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input"""
        if event.input.id != "input":
            return
            
        user_input = event.value.strip()
        if not user_input:
            return
            
        # Clear input
        event.input.value = ""
        
        # Add user message to chat
        chat = self.query_one("#chat", ChatArea)
        chat.add_message(user_input, "user")
        
        # Set processing state
        self.processing = True
        
        try:
            # Handle commands
            if user_input.startswith('/'):
                await self._handle_command(user_input)
            # Handle file references
            elif user_input.startswith('@'):
                await self._handle_file_reference(user_input)
            # Handle regular chat
            else:
                await self._handle_chat(user_input)
                
        except Exception as e:
            chat.add_message(f"Error: {str(e)}", "system")
        finally:
            self.processing = False
            
    async def _handle_command(self, command_input: str):
        """Handle slash commands"""
        parts = command_input.split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        chat = self.query_one("#chat", ChatArea)
        
        if command == "/help":
            help_text = """## Available Commands

**Chat:**
- Just type to chat with Claude
- Use `@filename` to reference files

**Commands:**
- `/help` - Show this help
- `/status` - Show current setup  
- `/clear` - Clear conversation
- `/exit` - Exit application

**File Operations:**
- `/read <file>` - Read a file
- `/ls [path]` - List directory contents
- `/grep <pattern>` - Search in files

**Keyboard Shortcuts:**
- `Ctrl+C` - Quit
- `Ctrl+L` - Clear screen
- `Esc` - Cancel operation"""
            
            chat.add_message(help_text, "system")
            
        elif command == "/status":
            status_text = f"""## Current Setup

**Workspace:** `{self.workspace_path}`
**Model:** `{self.model_name}`
**Provider:** `{self.provider}`
**Host:** `{self.host}`
**Context Size:** `{self.num_ctx}`
**Files in Context:** `{len(self.files_in_context)}`
**Thinking Mode:** `{'Enabled' if self.enable_thinking else 'Disabled'}`"""
            
            chat.add_message(status_text, "system")
            
        elif command == "/clear":
            chat.clear_messages()
            chat.add_message("Console cleared", "system")
            
        elif command == "/exit":
            self.exit()
            
        elif command == "/read":
            if args:
                await self._read_file(args)
            else:
                chat.add_message("Usage: /read <filename>", "system")
                
        elif command == "/ls":
            await self._list_directory(args or ".")
            
        elif command == "/grep":
            if args:
                await self._grep_files(args)
            else:
                chat.add_message("Usage: /grep <pattern>", "system")
                
        else:
            chat.add_message(f"Unknown command: {command}. Type /help for available commands.", "system")
            
    async def _handle_file_reference(self, file_input: str):
        """Handle @filename references"""
        file_path = file_input[1:].strip()
        chat = self.query_one("#chat", ChatArea)
        
        path = Path(file_path).resolve()
        if path.exists() and path.is_file():
            self.files_in_context.add(path)
            relative_path = path.relative_to(self.workspace_path) if path.is_relative_to(self.workspace_path) else path
            chat.add_message(f"Added `{relative_path}` to context", "system")
        else:
            chat.add_message(f"File not found: `{file_path}`", "system")
            
    async def _handle_chat(self, user_input: str):
        """Handle regular chat messages"""
        chat = self.query_one("#chat", ChatArea)
        
        try:
            response = await self.agent.agent_response(user_input)
            chat.add_message(response, "assistant")
        except Exception as e:
            chat.add_message(f"Error communicating with model: {str(e)}", "system")
            
    async def _read_file(self, file_path: str):
        """Read and display a file"""
        chat = self.query_one("#chat", ChatArea)
        
        try:
            result = await self.agent.tools.read(file_path)
            if result.error:
                chat.add_message(f"Error reading file: {result.error}", "system")
            else:
                # Show file content in a clean format
                content = f"**{file_path}**\n\n```\n{result.content}\n```"
                chat.add_message(content, "system")
        except Exception as e:
            chat.add_message(f"Error reading file: {str(e)}", "system")
            
    async def _list_directory(self, path: str):
        """List directory contents"""
        chat = self.query_one("#chat", ChatArea)
        
        try:
            result = await self.agent.tools.ls(path)
            if result.error:
                chat.add_message(f"Error listing directory: {result.error}", "system")
            else:
                # Show directory listing in a clean format
                content = f"**Directory: {path}**\n\n```\n{result.content}\n```"
                chat.add_message(content, "system")
        except Exception as e:
            chat.add_message(f"Error listing directory: {str(e)}", "system")
            
    async def _grep_files(self, pattern: str):
        """Search files with grep"""
        chat = self.query_one("#chat", ChatArea)
        
        try:
            result = await self.agent.tools.grep(pattern)
            if result.error:
                chat.add_message(f"Error searching files: {result.error}", "system")
            else:
                # Show search results in a clean format
                content = f"**Search results for: {pattern}**\n\n```\n{result.content}\n```"
                chat.add_message(content, "system")
        except Exception as e:
            chat.add_message(f"Error searching files: {str(e)}", "system")
            
    def _handle_agent_status(self, action: str, data):
        """Handle status updates from agent"""
        # For the simple interface, we can show tool usage more subtly
        if action == "tool_completed" and self.verbose:
            chat = self.query_one("#chat", ChatArea)
            tool_name = data.get("tool_name", "unknown")
            # Just show a simple indicator that a tool was used
            chat.add_message(f"Used tool: {tool_name}", "tool")
            
    async def on_unmount(self) -> None:
        """Clean up when app is unmounted"""
        if hasattr(self.agent, 'close'):
            await self.agent.close()