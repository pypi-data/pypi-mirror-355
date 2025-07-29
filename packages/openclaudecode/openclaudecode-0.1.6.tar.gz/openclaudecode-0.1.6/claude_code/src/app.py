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

# Add prompt_toolkit imports
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
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
                 model_name: str = "qwen2.5:7b-instruct",
                 host: str = "http://192.168.170.76:11434", 
                 workspace_path: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 num_ctx: int = 4096,
                 enable_thinking: bool = False,
                 provider: str = "ollama",
                 api_key: Optional[str] = None):
        
        # Use provided workspace path or current working directory
        self.current_workspace = Path(workspace_path).resolve() if workspace_path else Path.cwd()
        
        # Ensure logs are silenced
        logging.getLogger().setLevel(logging.WARNING)
        
        # Initialize agent
        self.agent = ClaudeCodeAgent(
            model_name=model_name,
            host=host, 
            workspace_root=str(self.current_workspace),
            system_prompt=system_prompt,
            num_ctx=num_ctx,
            enable_thinking=enable_thinking,
            provider=provider,
            api_key=api_key
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
            box=box.ROUNDED
        )
        self.console.print(files_panel)
    
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
            self.console.print("[success]Conversation history cleared[/success]")
        elif command == "/model":
            self.console.print(f"[info]Current model: {self.agent.model_name}[/info]")
        elif command == "/workspace":
            self.console.print(f"[info]Current workspace: {self.current_workspace}[/info]")
        elif command == "/read":
            if args:
                result = await self.agent.tools.read(args)
                if result.error:
                    self.console.print(f"[error]{result.error}[/error]")
                else:
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
                self.console.print(f"[error]{result.error}[/error]")
            else:
                self.console.print(result.content)
        elif command == "/grep":
            if args:
                result = await self.agent.tools.grep(args)
                if result.error:
                    self.console.print(f"[error]{result.error}[/error]")
                else:
                    self.console.print(result.content)
            else:
                self.console.print("[error]Usage: /grep <pattern>[/error]")
        elif command == "/bash":
            if args:
                result = await self.agent.tools.bash(args)
                if result.error:
                    self.console.print(f"[error]{result.error}[/error]")
                else:
                    self.console.print(result.content)
            else:
                self.console.print("[error]Usage: /bash <command>[/error]")
        elif command == "/todo":
            result = await self.agent.tools.todo_read()
            if result.error:
                self.console.print(f"[error]{result.error}[/error]")
            else:
                todos_data = result.content
                panel = Panel(Markdown(f"```json\\n{todos_data}\\n```"), title=f"[{CLAUDE_PRIMARY} bold]Todo List[/{CLAUDE_PRIMARY} bold]", border_style=CLAUDE_PRIMARY)
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
        
        # Create welcome panel
        system_info = []
        system_info.append(f"**Workspace:** `{self.current_workspace}`")
        system_info.append(f"**Model:** `{self.agent.model_name}`")
        system_info.append(f"**Host:** `{self.agent.host}`")
        
        welcome_panel = Panel(
            Group(
                Markdown("**Welcome to Claude Code!** Type `/help` for available commands."),
                Markdown("\\n".join(system_info))
            ),
            title=f"[{CLAUDE_PRIMARY} bold]Claude Code - AI Development Assistant[/{CLAUDE_PRIMARY} bold]",
            border_style=CLAUDE_PRIMARY,
            box=box.ROUNDED
        )
        
        self.console.print(welcome_panel)
        
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
                    self.console.print(f"[{CLAUDE_WARNING} bold]{'─' * 20} CLAUDE CODE {'─' * 20}[/{CLAUDE_WARNING} bold]")
                    
                    user_input = await asyncio.to_thread(
                        lambda: self.session.prompt(
                            HTML(f"<ansigreen><b>[CLAUDE]></b></ansigreen> ")
                        )
                    )
                    self.console.print()
                
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
                    self.console.print("[info]Processing with agent...[/info]")
                    response = await self.agent.agent_response(user_input)
                    
                    panel = Panel(
                        Markdown(response),
                        title=f"[{CLAUDE_SUCCESS} bold]🤖 Claude Code Response 🤖[/{CLAUDE_SUCCESS} bold]",
                        border_style=CLAUDE_SUCCESS,
                        expand=True,
                        box=box.ROUNDED
                    )
                    self.console.print(panel)
                    
            except KeyboardInterrupt:
                self.console.print("\\n[warning]Exiting...[/warning]")
                running = False
            except Exception as e:
                self.console.print(f"[error]Error: {str(e)}[/error]")
        
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
    parser.add_argument("-m", "--model", default="qwen2.5:7b-instruct", help="Model name (default: qwen2.5:7b-instruct)")
    parser.add_argument("--host", default="http://192.168.170.76:11434", help="Ollama host URL")
    parser.add_argument("-p", "--provider", default="ollama", choices=["ollama", "gemini"], help="LLM provider (default: ollama)")
    parser.add_argument("--api-key", default="AIzaSyBb8wTvVw9e25aX8XK-eBuu1JzDEPCdqUE", help="API key for Gemini provider")
    parser.add_argument("-w", "--workspace", help="Workspace directory path")
    parser.add_argument("-q", "--query", help="Initial query to process")
    parser.add_argument("--thinking", action="store_true", help="Enable thinking process")
    parser.add_argument("--num-ctx", type=int, default=4096, help="Context window size")
    
    args = parser.parse_args()
    
    # Create and run app
    app = ClaudeCodeApp(
        model_name=args.model,
        host=args.host,
        workspace_path=args.workspace,
        num_ctx=args.num_ctx,
        enable_thinking=args.thinking,
        provider=args.provider,
        api_key=args.api_key
    )
    
    await app.run(initial_query=args.query)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nGoodbye!")