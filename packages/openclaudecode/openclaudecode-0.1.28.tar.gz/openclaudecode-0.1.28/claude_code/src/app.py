#!/usr/bin/env python3
"""
Claude Code - Main CLI Application
A Claude Code implementation with comprehensive tools and rich terminal UI
"""

import os
import sys
import asyncio
import argparse
import time
import logging
from typing import List, Dict, Optional, Set
from pathlib import Path

# Configure logging to suppress INFO messages
logging.basicConfig(level=logging.WARNING)

# Silence standard library loggers
for logger_name in ["asyncio", "urllib", "urllib3", "filelock", "httpx", "httpcore"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

import rich
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich import box
from rich.markdown import Markdown
from rich.theme import Theme
from rich.style import Style as RichStyle
from rich.console import Group
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner


# Add prompt_toolkit imports
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app
from prompt_toolkit.shortcuts import CompleteStyle

from .agent import ClaudeCodeAgent

# Claude Code logo
CLAUDE_CODE_LOGO = """
 ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗     ██████╗ ██████╗ ██████╗ ███████╗
██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
██║     ██║     ███████║██║   ██║██║  ██║█████╗      ██║     ██║   ██║██║  ██║█████╗  
██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝      ██║     ██║   ██║██║  ██║██╔══╝  
╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗    ╚██████╗╚██████╔╝██████╔╝███████╗
 ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
"""

# Claude-inspired theme colors  
CLAUDE_PRIMARY = "#E67E50"    # Warm coral/orange from Claude branding
CLAUDE_SECONDARY = "#D4A574"  # Warm beige/tan  
CLAUDE_ACCENT = "#B8956A"     # Deeper warm tone
CLAUDE_SUCCESS = "#7B9E3F"    # Natural green
CLAUDE_INFO = "#5B8AA6"       # Calm blue
CLAUDE_WARNING = "#D49C3D"    # Warm amber
CLAUDE_ERROR = "#C85450"      # Warm red
CLAUDE_TEXT = "#2C2B29"       # Warm dark text
CLAUDE_BACKGROUND = "#F5F5F2" # Warm off-white background

class CommandCompleter(Completer):
    """Completer for Claude Code commands"""
    def __init__(self, commands):
        self.commands = commands
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Complete commands that start with /
        if text.startswith('/'):
            word = text.lstrip('/')
            for command in self.commands:
                cmd = command.lstrip('/')
                if cmd.startswith(word):
                    yield Completion(
                        text=cmd,
                        start_position=-len(word),
                        display=command,
                        style='class:command'
                    )

class FileCompleter(Completer):
    """Completer for file paths with fuzzy matching"""
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root)
        self._cached_files = None
        self._last_cache_time = 0
    
    def _get_all_files(self):
        """Get all files in the workspace with cache support"""
        current_time = time.time()
        if self._cached_files is None or (current_time - self._last_cache_time) > 5:
            all_files = []
            for root, dirs, files in os.walk(self.workspace_root):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                for file in files:
                    if not file.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.workspace_root)
                        all_files.append(rel_path)
            
            self._cached_files = all_files
            self._last_cache_time = current_time
        
        return self._cached_files
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        if text.startswith('@'):
            path_text = text[1:]
            all_files = self._get_all_files()
            
            matches = []
            for file_path in all_files:
                if not path_text:
                    matches.append((0, file_path))
                elif path_text.lower() in file_path.lower():
                    match_pos = file_path.lower().find(path_text.lower())
                    matches.append((match_pos, file_path))
                elif all(c.lower() in file_path.lower() for c in path_text):
                    matches.append((100, file_path))
            
            matches.sort(key=lambda x: (x[0], len(x[1])))
            
            for _, file_path in matches[:20]:
                yield Completion(
                    text=file_path,
                    start_position=-len(path_text),
                    display=file_path,
                    style='class:file'
                )

class ClaudeCodeCompleter(Completer):
    """Combined completer for Claude Code"""
    def __init__(self, commands, workspace_root):
        self.command_completer = CommandCompleter(commands)
        self.file_completer = FileCompleter(workspace_root)
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        if text.startswith('/'):
            yield from self.command_completer.get_completions(document, complete_event)
        elif text.startswith('@'):
            yield from self.file_completer.get_completions(document, complete_event)
        elif not text:
            yield Completion(
                text='/',
                start_position=0,
                display='/ (command)',
                style='class:command'
            )
            yield Completion(
                text='@',
                start_position=0,
                display='@ (file)',
                style='class:file'
            )

class ClaudeCodeApp:
    """Main Claude Code application"""
    
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
        
        # Use provided workspace path or current working directory
        self.current_workspace = Path(workspace_path).resolve() if workspace_path else Path.cwd()
        
        # Set default model based on provider if not specified
        if not model_name:
            if provider == "gemini":
                model_name = "gemini-2.5-flash-preview-05-20"
            else:  # ollama or default
                model_name = "qwen2.5:7b-instruct"
        
        # Ensure logs are silenced
        logging.getLogger().setLevel(logging.WARNING)
        
        # Initialize agent with status callback
        self.agent = ClaudeCodeAgent(
            model_name=model_name,
            host=host, 
            workspace_root=str(self.current_workspace),
            system_prompt=system_prompt,
            num_ctx=num_ctx,
            enable_thinking=enable_thinking,
            provider=provider,
            api_key=api_key,
            status_callback=self._handle_status_callback
        )
        
        # Create Claude-inspired theme
        custom_theme = Theme({
            "info": RichStyle(color=CLAUDE_INFO),
            "warning": RichStyle(color=CLAUDE_WARNING),
            "error": RichStyle(color=CLAUDE_ERROR),
            "success": RichStyle(color=CLAUDE_SUCCESS),
            "primary": RichStyle(color=CLAUDE_PRIMARY),
            "primary.border": RichStyle(color=CLAUDE_PRIMARY),
            "primary.title": RichStyle(color=CLAUDE_PRIMARY, bold=True),
            "claude.thinking": RichStyle(color=CLAUDE_ACCENT, dim=True),
            "claude.streaming": RichStyle(color=CLAUDE_SUCCESS),
            "claude.tool": RichStyle(color=CLAUDE_WARNING),
            "claude.border": RichStyle(color=CLAUDE_SECONDARY),
            "claude.text": RichStyle(color=CLAUDE_TEXT),
        })
        
        # Initialize console with custom theme
        self.console = Console(theme=custom_theme, width=None)
        
        # Chat context management
        self.files_in_context: Set[Path] = set()
        self.chat_history: List[Dict[str, str]] = []
        
        # Available commands
        self.commands = [
            "/help", "/exit", "/status", "/clear", "/model", "/workspace",
            "/read", "/write", "/edit", "/ls", "/grep", "/bash", "/todo",
            "/chat", "/stream", "/interactive"
        ]
        
        # Current mode
        self.current_mode = "Claude Code"
        
        # Status tracking for dynamic indicators
        self.current_status = "ready"  # ready, processing, error, waiting
        self.current_tool = None  # Currently executing tool name
        
        # Token counting (only used in verbose mode)
        self.current_tokens = 0
        self.max_tokens = num_ctx
        self.verbose_mode = verbose
        
        # Live display management
        self.live_display = None
        self.live_task = None
        
        # Define prompt styles
        self.style = Style.from_dict({
            'command': f'{CLAUDE_PRIMARY} bold',
            'file': f'{CLAUDE_SUCCESS}',
            'prompt': f'{CLAUDE_WARNING} bold',
            'ansigreen': f'{CLAUDE_SUCCESS} bold',
            'text': f'{CLAUDE_TEXT}',
        })
        
        # Create key bindings
        kb = KeyBindings()
        
        # Flag to track if processing should be interrupted
        self.interrupt_processing = False
        
        @kb.add('escape')
        def _(event):
            """Interrupt current processing with Escape key"""
            self.interrupt_processing = True
            event.app.exit()
        
        @kb.add('c-space')
        def _(event):
            """Toggle completion with Ctrl+Space"""
            buff = event.app.current_buffer
            if buff.complete_state:
                buff.complete_next()
            else:
                buff.start_completion(select_first=False)
        
        @kb.add('c-n')
        def _(event):
            """Navigate to next completion with Ctrl+N"""
            buff = event.app.current_buffer
            if buff.complete_state:
                buff.complete_next()
        
        @kb.add('c-p')
        def _(event):
            """Navigate to previous completion with Ctrl+P"""
            buff = event.app.current_buffer
            if buff.complete_state:
                buff.complete_previous()
        
        # Initialize prompt session
        self.completer = ClaudeCodeCompleter(self.commands, self.current_workspace)
        self.history = InMemoryHistory()
        self.session = PromptSession(
            history=self.history,
            style=self.style,
            completer=self.completer,
            complete_while_typing=True,
            complete_in_thread=True,
            enable_history_search=True,
            complete_style=CompleteStyle.MULTI_COLUMN,
            key_bindings=kb
        )
    
    def count_tokens(self, text: str) -> int:
        """Rough estimate of tokens based on word count"""
        return int(len(text.split()) * 1.3)
    
    def update_token_count(self, text: str):
        """Update current token count"""
        self.current_tokens = self.count_tokens(text)
    
    def get_token_display(self) -> str:
        """Get formatted token count display"""
        if self.current_tokens > self.max_tokens * 0.8:
            icon = "🔶"  # Orange diamond when approaching limit
            color = CLAUDE_WARNING
        elif self.current_tokens > self.max_tokens * 0.6:
            icon = "🔶"  # Orange diamond when getting high
            color = CLAUDE_WARNING
        else:
            icon = "🔸"  # Small orange diamond when safe
            color = CLAUDE_SUCCESS
        
        return f"[{color}]{icon} {self.current_tokens}[/{color}] tokens"
    
    def get_status_indicator(self):
        """Get the current status indicator with tool name if executing"""
        if self.current_status == "processing" and self.current_tool:
            return f"[{CLAUDE_WARNING}]●[/{CLAUDE_WARNING}] [dim]{self.current_tool}[/dim]"
        
        status_indicators = {
            "ready": f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}]",      # Green dot - ready
            "processing": f"[{CLAUDE_WARNING}]●[/{CLAUDE_WARNING}]", # Yellow dot - processing
            "error": f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}]",          # Red dot - error
            "waiting": f"[{CLAUDE_INFO}]●[/{CLAUDE_INFO}]"           # Blue dot - waiting
        }
        return status_indicators.get(self.current_status, status_indicators["ready"])
    
    def create_live_status_display(self, tool_name: str):
        """Create live status display content"""
        # Create spinner with tool name
        spinner = Spinner("dots", text=f"[{CLAUDE_WARNING}]{tool_name.title()}...[/{CLAUDE_WARNING}]")
        
        # Add token count and interrupt hint
        if self.verbose_mode:
            token_display = self.get_token_display()
            progress_info = f"{token_display} • esc to interrupt"
        else:
            progress_info = "esc to interrupt"
        
        return Group(
            spinner,
            Text(progress_info, style="dim")
        )
    
    def show_tool_status(self, tool_name: str):
        """Display current tool execution status with live progress"""
        self.current_status = "processing"
        self.current_tool = tool_name
        
        # Create and start live display
        live_content = self.create_live_status_display(tool_name)
        self.live_display = Live(live_content, console=self.console, refresh_per_second=4)
        self.live_display.start()
    
    def clear_tool_status(self):
        """Clear tool execution status"""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
        
        self.current_status = "ready"
        self.current_tool = None
    
    def _handle_status_callback(self, action: str, data):
        """Handle status updates from agent"""
        if action == "show_tool":
            self.show_tool_execution(data)
        elif action == "tool_completed":
            self.show_tool_completed(data)
        elif action == "tool_error":
            self.show_tool_error(data)
    
    def show_tool_execution(self, tool_name: str):
        """Show tool execution with status indicator - using spinner instead of duplicate display"""
        pass  # Status display is handled by show_tool_completed to avoid duplication
    
    def show_tool_completed(self, data):
        """Show tool completion with green dot and results like in screenshots"""
        tool_name = data["tool_name"]
        result = data["result"]
        arguments = data["arguments"]
        
        # Format display based on tool type, similar to screenshots
        if tool_name == "ls":
            path = arguments.get("path", ".")
            if result.content:
                lines = result.content.strip().split('\n')
                file_count = len([line for line in lines if line.strip()])
                self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] List(.)")
                self.console.print(f"  └ Listed {file_count} paths")
            else:
                self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] List({path})")
                self.console.print(f"  └ Directory empty")
        
        elif tool_name == "read":
            file_path = arguments.get("file_path", "")
            if result.content:
                lines = result.content.strip().split('\n')
                line_count = len(lines)
                self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Read({file_path})")
                self.console.print(f"  └ Read {line_count} lines")
            else:
                self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Read({file_path})")
                self.console.print(f"  └ File empty")
        
        elif tool_name == "grep":
            pattern = arguments.get("pattern", "")
            if result.content:
                lines = result.content.strip().split('\n')
                match_count = len([line for line in lines if line.strip()])
                self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Grep({pattern})")
                self.console.print(f"  └ Found {match_count} matches")
            else:
                self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Grep({pattern})")
                self.console.print(f"  └ No matches found")
        
        elif tool_name == "bash":
            command = arguments.get("command", "")
            self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Bash({command[:30]}{'...' if len(command) > 30 else ''})")
            if result.error:
                self.console.print(f"  └ Command failed")
            else:
                self.console.print(f"  └ Command completed")
        
        else:
            # Generic tool completion display
            self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] {tool_name.capitalize()}")
            if result.error:
                self.console.print(f"  └ Failed: {result.error}")
            else:
                self.console.print(f"  └ Completed successfully")
    
    def show_tool_error(self, data):
        """Show tool error with red dot"""
        tool_name = data["tool_name"] 
        error = data["error"]
        self.console.print(f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}] {tool_name.capitalize()} failed")
        self.console.print(f"  └ {error}")
    
    def create_todo_style_display(self, items: list) -> Panel:
        """Create a todo-style display with checkboxes"""
        content = []
        for item in items:
            if item.get('completed', False):
                checkbox = f"[{CLAUDE_SUCCESS}]☑[/{CLAUDE_SUCCESS}]"
                text_style = f"[{CLAUDE_SUCCESS} dim strike]"
            else:
                checkbox = f"[{CLAUDE_INFO}]☐[/{CLAUDE_INFO}]"
                text_style = f"[{CLAUDE_TEXT}]"
            
            content.append(f"{checkbox} {text_style}{item['text']}[/{text_style}]")
        
        return Panel(
            "\n".join(content),
            title=f"[{CLAUDE_PRIMARY} bold]Tasks[/{CLAUDE_PRIMARY} bold]",
            border_style=CLAUDE_PRIMARY,
            box=box.ROUNDED,
            padding=(1, 2)
        )
    
    def print_logo(self):
        """Print the Claude Code logo"""
        self.console.print(f"[{CLAUDE_PRIMARY}]{CLAUDE_CODE_LOGO}[/{CLAUDE_PRIMARY}]")
    
    def print_help(self):
        """Print help information"""
        table = Table(
            title=f"[{CLAUDE_PRIMARY} bold]Claude Code Commands[/{CLAUDE_PRIMARY} bold]",
            box=box.ROUNDED, 
            border_style=CLAUDE_PRIMARY
        )
        table.add_column("Command", style="primary")
        table.add_column("Description", style="claude.text")
        
        table.add_row("/help", "Show this help message")
        table.add_row("/exit", "Exit Claude Code")
        table.add_row("/status", "Show system status")
        table.add_row("/clear", "Clear conversation history")
        table.add_row("/model", "Show current model info")
        table.add_row("/workspace", "Show workspace info")
        table.add_row("/read <file>", "Read a file")
        table.add_row("/write <file>", "Write to a file")
        table.add_row("/edit <file>", "Edit a file")
        table.add_row("/ls <path>", "List directory contents")
        table.add_row("/grep <pattern>", "Search files")
        table.add_row("/bash <command>", "Execute bash command")
        table.add_row("/todo", "Manage todo list")
        table.add_row("/chat <message>", "Chat without tools")
        table.add_row("/stream <message>", "Stream response")
        table.add_row("/interactive <message>", "Interactive mode")
        
        self.console.print(table)
        
        # Add information about special syntax
        syntax_table = Table(
            title=f"[{CLAUDE_PRIMARY} bold]Special Syntax[/{CLAUDE_PRIMARY} bold]",
            box=box.ROUNDED,
            border_style=CLAUDE_PRIMARY
        )
        syntax_table.add_column("Syntax", style="primary")
        syntax_table.add_column("Description", style="claude.text")
        
        syntax_table.add_row("@filename", "Add file to context")
        syntax_table.add_row("message without /", "Send to agent with tools")
        
        self.console.print(syntax_table)
    
    def show_status(self):
        """Show system status"""
        status_table = Table(
            title=f"[{CLAUDE_PRIMARY} bold]System Status[/{CLAUDE_PRIMARY} bold]",
            box=box.ROUNDED,
            border_style=CLAUDE_PRIMARY
        )
        status_table.add_column("Property", style="primary")
        status_table.add_column("Value", style="claude.text")
        
        status_table.add_row("Workspace", str(self.current_workspace))
        status_table.add_row("Model", self.agent.model_name)
        status_table.add_row("Host", self.agent.host)
        status_table.add_row("Context Size", str(self.agent.num_ctx))
        status_table.add_row("Files in Context", str(len(self.files_in_context)))
        
        self.console.print(status_table)
    
    def show_files_in_context(self):
        """Show files currently in context"""
        if not self.files_in_context:
            empty_panel = Panel(
                "No files in context. Use [bold]@filename[/bold] to add files.",
                title=f"[{CLAUDE_PRIMARY} bold]Files in Context[/{CLAUDE_PRIMARY} bold]",
                border_style=CLAUDE_PRIMARY,
                box=box.ROUNDED
            )
            self.console.print(empty_panel)
            return
        
        table = Table(box=box.SIMPLE, border_style=CLAUDE_PRIMARY)
        table.add_column("File", style="success")
        
        for file_path in sorted(self.files_in_context):
            table.add_row(str(file_path.relative_to(self.current_workspace)))
        
        files_panel = Panel(
            table,
            title=f"[{CLAUDE_PRIMARY} bold]Files in Context[/{CLAUDE_PRIMARY} bold]",
            border_style=CLAUDE_PRIMARY,
            box=box.ROUNDED,
            padding=(0, 1)  # Add some horizontal padding
        )
        self.console.print(files_panel)
        self.console.print()  # Add space after files panel
    
    def add_file_to_context(self, file_path: str):
        """Add a file to context"""
        path = Path(file_path).resolve()
        if path.exists() and path.is_file():
            self.files_in_context.add(path)
            self.console.print(f"[success]Added {path.relative_to(self.current_workspace)} to context[/success]")
        else:
            self.console.print(f"[error]File not found: {file_path}[/error]")
    
    async def process_command(self, command: str, args: str) -> bool:
        """Process a command and return whether to continue"""
        if command == "/exit":
            return False
        elif command == "/help":
            self.print_help()
        elif command == "/status":
            self.show_status()
        elif command == "/clear":
            self.chat_history.clear()
            self.agent.conversation_history.clear()
            self.console.print("[success]Conversation history cleared[/success]")
        elif command == "/model":
            self.console.print(f"[info]Current model: {self.agent.model_name}[/info]")
        elif command == "/workspace":
            self.console.print(f"[info]Current workspace: {self.current_workspace}[/info]")
        elif command == "/read":
            if args:
                result = await self.agent.tools.read(args)
                
                if result.error:
                    self.console.print(f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}] Read failed")
                    self.console.print(f"[error]{result.error}[/error]")
                else:
                    line_count = len(result.content.splitlines())
                    self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Read({args})")
                    self.console.print(f"  └ Read {line_count} lines")
                    syntax = Syntax(result.content, "text", theme="monokai", line_numbers=True)
                    panel = Panel(syntax, title=f"[{CLAUDE_PRIMARY} bold]File: {args}[/{CLAUDE_PRIMARY} bold]", border_style=CLAUDE_PRIMARY)
                    self.console.print(panel)
            else:
                self.console.print("[error]Usage: /read <file_path>[/error]")
        elif command == "/write":
            self.console.print("[info]Write command requires file path and content[/info]")
        elif command == "/edit":
            self.console.print("[info]Edit command requires interactive input[/info]")
        elif command == "/ls":
            path = args or "."
            result = await self.agent.tools.ls(path)
            
            if result.error:
                self.console.print(f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}] List failed")
                self.console.print(f"[error]{result.error}[/error]")
            else:
                lines = result.content.strip().split('\n') if result.content.strip() else []
                file_count = len([line for line in lines if line.strip()])
                self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] List({path})")
                self.console.print(f"  └ Listed {file_count} paths")
                self.console.print(result.content)
        elif command == "/grep":
            if args:
                result = await self.agent.tools.grep(args)
                
                if result.error:
                    self.console.print(f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}] Search failed")
                    self.console.print(f"[error]{result.error}[/error]")
                else:
                    # Count matches for better feedback
                    lines = result.content.strip().split('\n') if result.content.strip() else []
                    match_count = len([line for line in lines if line.strip()])
                    self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Grep({args})")
                    self.console.print(f"  └ Found {match_count} matches")
                    self.console.print(result.content)
            else:
                self.console.print("[error]Usage: /grep <pattern>[/error]")
        elif command == "/bash":
            if args:
                try:
                    result = await self.agent.tools.bash(args)
                    
                    if result.error:
                        self.console.print(f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}] Bash({args[:30]}{'...' if len(args) > 30 else ''})")
                        self.console.print(f"  └ Command failed")
                        self.console.print(f"[error]{result.error}[/error]")
                    else:
                        self.console.print(f"[{CLAUDE_SUCCESS}]●[/{CLAUDE_SUCCESS}] Bash({args[:30]}{'...' if len(args) > 30 else ''})")
                        self.console.print(f"  └ Command completed")
                        if result.content.strip():
                            self.console.print(result.content)
                except Exception as e:
                    self.console.print(f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}] Error: {str(e)}")
            else:
                self.console.print("[error]Usage: /bash <command>[/error]")
        elif command == "/todo":
            result = await self.agent.tools.todo_read()
            if result.error:
                self.console.print(f"[error]{result.error}[/error]")
            else:
                # Parse todos and display in a clean todo-style format
                try:
                    import json
                    todos_data = json.loads(result.content)
                    
                    if not todos_data:
                        empty_panel = Panel(
                            "No todos found. Create some tasks to get started!",
                            title=f"[{CLAUDE_PRIMARY} bold]Todo List[/{CLAUDE_PRIMARY} bold]",
                            border_style=CLAUDE_PRIMARY,
                            box=box.ROUNDED
                        )
                        self.console.print(empty_panel)
                    else:
                        # Convert to display format
                        display_items = []
                        for todo in todos_data:
                            completed = todo.get('status') == 'completed'
                            priority_indicator = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(todo.get('priority', 'medium'), "🟡")
                            text = f"{priority_indicator} {todo.get('content', 'Unknown task')}"
                            display_items.append({'text': text, 'completed': completed})
                        
                        todo_panel = self.create_todo_style_display(display_items)
                        self.console.print(todo_panel)
                        
                except Exception:
                    # Fallback to original display
                    panel = Panel(Markdown(f"```json\n{todos_data}\n```"), title=f"[{CLAUDE_PRIMARY} bold]Todo List[/{CLAUDE_PRIMARY} bold]", border_style=CLAUDE_PRIMARY)
                    self.console.print(panel)
        elif command == "/chat":
            if args:
                response = await self.agent.chat(args)
                panel = Panel(Markdown(response), title=f"[{CLAUDE_INFO} bold]Chat Response[/{CLAUDE_INFO} bold]", border_style=CLAUDE_INFO)
                self.console.print(panel)
            else:
                self.console.print("[error]Usage: /chat <message>[/error]")
        elif command == "/stream":
            if args:
                self.console.print("[info]Streaming response...[/info]")
                response_parts = []
                async for chunk in self.agent.stream_response(args):
                    self.console.print(chunk, end="")
                    response_parts.append(chunk)
                self.console.print()  # New line
            else:
                self.console.print("[error]Usage: /stream <message>[/error]")
        elif command == "/interactive":
            if args:
                response = await self.agent.interactive_mode(args)
                panel = Panel(Markdown(response), title=f"[{CLAUDE_WARNING} bold]Interactive Response[/{CLAUDE_WARNING} bold]", border_style=CLAUDE_WARNING)
                self.console.print(panel)
            else:
                self.console.print("[error]Usage: /interactive <message>[/error]")
        else:
            self.console.print(f"[error]Unknown command: {command}[/error]")
        
        return True
    
    async def run(self, initial_query: Optional[str] = None):
        """Run the Claude Code application"""
        # Show logo and welcome
        self.print_logo()
        
        # Create welcome panel with border but not expanded
        welcome_content = []
        welcome_content.append(f"[{CLAUDE_PRIMARY}]✨ Welcome to Claude Code![/{CLAUDE_PRIMARY}]")
        welcome_content.append("")
        welcome_content.append(f"[{CLAUDE_ACCENT}]/help[/{CLAUDE_ACCENT}] for help, [{CLAUDE_ACCENT}]/status[/{CLAUDE_ACCENT}] for your current setup")
        welcome_content.append("")
        welcome_content.append(f"[{CLAUDE_ACCENT}]cwd:[/{CLAUDE_ACCENT}] `{self.current_workspace}`")
        
        welcome_panel = Panel(
            "\n".join(welcome_content),
            border_style=CLAUDE_PRIMARY,
            box=box.ROUNDED,
            expand=False,
            padding=(0, 1)
        )
        self.console.print(welcome_panel)
        self.console.print()  # Add breathing room after welcome
        
        running = True
        while running:
            try:
                # Show files in context
                if self.files_in_context:
                    self.show_files_in_context()
                
                # Get user input
                if initial_query:
                    user_input = initial_query
                    initial_query = None
                else:
                    # Set waiting status when ready for user input
                    self.current_status = "waiting"
                    
                    # Create a cleaner prompt with better spacing and visual appeal
                    # Add a dynamic status indicator dot and clean > prompt
                    status_indicator = self.get_status_indicator()
                    token_display = self.get_token_display()
                    
                    # Add some breathing room with a blank line before the prompt
                    # Only add space if we're not showing files context (which already adds space)
                    if not self.files_in_context:
                        self.console.print()
                    
                    # Create the prompt without status indicator
                    prompt_text = "<ansigreen><b>></b></ansigreen> "
                    
                    # Display info line (token count only in verbose mode)
                    interrupt_text = "esc to interrupt"
                    
                    if self.verbose_mode:
                        info_line = f"{token_display} • {interrupt_text}"
                    else:
                        info_line = interrupt_text
                    
                    self.console.print(f"[dim]{info_line}[/dim]")
                    
                    user_input = await asyncio.to_thread(
                        lambda: self.session.prompt(
                            HTML(prompt_text)
                        )
                    )
                    
                    # Reset interrupt flag and status after user provides input
                    self.interrupt_processing = False
                    self.current_status = "ready"
                    
                    # Update token count based on user input
                    if user_input:
                        self.update_token_count(user_input)
                
                # Handle @ file references
                if user_input.startswith('@'):
                    file_path = user_input[1:].strip()
                    self.add_file_to_context(file_path)
                    continue
                
                # Parse commands
                if user_input.startswith('/'):
                    parts = user_input.split(' ', 1)
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""
                    
                    running = await self.process_command(command, args)
                else:
                    # Default to agent with tools
                    self.current_status = "processing"
                    self.interrupt_processing = False
                    
                    try:
                        # Update token count for user input
                        if user_input:
                            self.update_token_count(user_input)
                        
                        # Check for interruption during processing
                        response = await self.agent.agent_response(user_input)
                        
                        if self.interrupt_processing:
                            self.console.print("[warning]Processing interrupted by user[/warning]")
                            self.current_status = "ready"
                            continue
                        
                        self.current_status = "ready"
                        
                        # Update token count for response
                        if response:
                            self.update_token_count(user_input + response)
                        
                        # Add some spacing before response
                        self.console.print()
                        self.console.print(Markdown(response))
                        
                    except KeyboardInterrupt:
                        self.console.print("[warning]Processing interrupted[/warning]")
                        self.current_status = "ready"
                    except Exception as e:
                        # Clear any live display
                        if self.live_display:
                            self.live_display.stop()
                            self.live_display = None
                        
                        self.current_status = "error"
                        
                        # Show error with red dot
                        self.console.print(f"[{CLAUDE_ERROR}]●[/{CLAUDE_ERROR}] Agent error: {str(e)}")
                        
                        # Reset status after error display
                        await asyncio.sleep(1)  # Brief pause to show error status
                        self.current_status = "ready"
                    
            except KeyboardInterrupt:
                self.console.print("\n[warning]Exiting...[/warning]")
                running = False
            except Exception as e:
                self.console.print(f"[error]Error: {str(e)}[/error]")
        
        # Clean up live display if still active
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
        
        await self.agent.close()
        self.console.print(f"[{CLAUDE_PRIMARY} bold]Thank you for using Claude Code![/{CLAUDE_PRIMARY} bold]")

async def main():
    """Main entry point"""
    # Disable verbose logging
    logging.getLogger().setLevel(logging.WARNING)
    for module in ["httpx", "urllib3", "httpcore", "asyncio"]:
        logging.getLogger(module).setLevel(logging.ERROR)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Claude Code - AI Development Assistant")
    parser.add_argument("-m", "--model", help="Model name")
    parser.add_argument("--host", default="http://192.168.170.76:11434", help="Ollama host URL")
    parser.add_argument("-p", "--provider", default="ollama", choices=["ollama", "gemini"], help="LLM provider (default: ollama)")
    parser.add_argument("--api-key", default="AIzaSyBb8wTvVw9e25aX8XK-eBuu1JzDEPCdqUE", help="API key for Gemini provider")
    parser.add_argument("-w", "--workspace", help="Workspace directory path")
    parser.add_argument("-q", "--query", help="Initial query to process")
    parser.add_argument("--thinking", action="store_true", help="Enable thinking process")
    parser.add_argument("--num-ctx", type=int, default=4096, help="Context window size")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode with token display")
    
    args = parser.parse_args()
    
    # Set default model based on provider if not specified
    if not args.model:
        if args.provider == "gemini":
            args.model = "gemini-2.5-flash-preview-05-20"
        else:  # ollama or default
            args.model = "qwen2.5:7b-instruct"
    
    # Create and run app
    app = ClaudeCodeApp(
        model_name=args.model,
        host=args.host,
        workspace_path=args.workspace,
        num_ctx=args.num_ctx,
        enable_thinking=args.thinking,
        provider=args.provider,
        api_key=args.api_key,
        verbose=args.verbose
    )
    
    await app.run(initial_query=args.query)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")