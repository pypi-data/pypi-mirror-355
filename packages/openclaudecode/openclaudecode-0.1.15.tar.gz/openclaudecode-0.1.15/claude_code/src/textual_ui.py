#!/usr/bin/env python3
"""
Textual UI Components for Claude Code
Provides modern terminal UI with styled input boxes
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Static, Button
from textual.binding import Binding
from textual import events
from textual.message import Message
from textual.css.query import NoMatches
import asyncio
from typing import Optional, Callable, Any


class StyledInput(Input):
    """A beautifully styled input widget"""
    
    DEFAULT_CSS = """
    StyledInput {
        width: 100%;
        height: 3;
        border: solid $primary;
        border-title-color: $accent;
        border-title-style: bold;
        background: $surface;
        color: $text;
        margin-bottom: 1;
    }
    
    StyledInput:focus {
        border: solid $success;
        border-title-color: $success;
    }
    
    StyledInput > .input--cursor {
        background: $success;
        color: $surface;
    }
    
    StyledInput > .input--placeholder {
        color: $text-muted;
        opacity: 0.6;
    }
    """


class StatusBar(Static):
    """Status bar component"""
    
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        width: 100%;
        height: 1;
        background: $panel;
        color: $text-muted;
        text-align: right;
        padding: 0 1;
    }
    """


class ClaudeCodeInputApp(App):
    """Main input application with styled components"""
    
    CSS = """
    Screen {
        background: $background;
    }
    
    .input-container {
        width: 100%;
        height: auto;
        margin: 1 2;
        padding: 1;
        border: solid $primary;
        border-title-color: $primary;
        border-title-style: bold;
        background: $surface;
    }
    
    .prompt-indicator {
        width: auto;
        height: 1;
        color: $success;
        text-style: bold;
        margin: 0 1;
        padding: 0;
    }
    
    .content-area {
        height: 1fr;
        background: $background;
        padding: 1 2;
    }
    
    .welcome-text {
        color: $text;
        text-align: center;
        margin: 2 0;
    }
    """
    
    BINDINGS = [
        Binding("escape", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    
    def __init__(self, 
                 prompt_callback: Optional[Callable[[str], Any]] = None,
                 status_text: str = "Ready",
                 workspace: str = ""):
        super().__init__()
        self.prompt_callback = prompt_callback
        self.status_text = status_text
        self.workspace = workspace
        self.input_value = ""
        
    def compose(self) -> ComposeResult:
        """Create the app layout"""
        with Container(classes="content-area"):
            yield Static("✨ Claude Code - AI Development Assistant", classes="welcome-text")
            yield Static(f"📁 {self.workspace}", classes="welcome-text")
            
        with Container(classes="input-container"):
            with Horizontal():
                yield Static("❯", classes="prompt-indicator")
                yield StyledInput(
                    placeholder="Enter your command or message...",
                    id="main-input"
                )
                
        yield StatusBar(self.status_text, id="status-bar")
    
    def on_mount(self) -> None:
        """Focus the input when app starts"""
        self.query_one("#main-input", StyledInput).focus()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission"""
        if event.input.id == "main-input":
            value = event.value.strip()
            if value:
                self.input_value = value
                if self.prompt_callback:
                    await self.prompt_callback(value)
                # Clear the input
                event.input.value = ""
            
    def update_status(self, text: str) -> None:
        """Update the status bar"""
        try:
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.update(text)
        except NoMatches:
            pass
    
    def update_workspace(self, workspace: str) -> None:
        """Update workspace display"""
        self.workspace = workspace
        # Update the workspace display if needed
        
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()


class InputManager:
    """Manager for the input UI"""
    
    def __init__(self, workspace: str = ""):
        self.workspace = workspace
        self.app = None
        self.input_queue = asyncio.Queue()
        
    async def get_input(self, prompt: str = "❯ ", status: str = "Ready") -> str:
        """Get input from the user with styled UI"""
        
        async def handle_input(value: str):
            await self.input_queue.put(value)
            
        self.app = ClaudeCodeInputApp(
            prompt_callback=handle_input,
            status_text=status,
            workspace=self.workspace
        )
        
        # Run the app in the background
        app_task = asyncio.create_task(self.app.run_async())
        
        try:
            # Wait for input
            result = await self.input_queue.get()
            return result
        finally:
            # Clean up
            if self.app and self.app.is_running:
                self.app.exit()
            if not app_task.done():
                app_task.cancel()
                try:
                    await app_task
                except asyncio.CancelledError:
                    pass
    
    def update_status(self, text: str):
        """Update status text"""
        if self.app:
            self.app.update_status(text)
    
    def update_workspace(self, workspace: str):
        """Update workspace"""
        self.workspace = workspace
        if self.app:
            self.app.update_workspace(workspace)


# Example usage
async def main():
    """Example of how to use the styled input"""
    manager = InputManager("/home/user/project")
    
    while True:
        try:
            user_input = await manager.get_input(status="Ready • ESC to quit")
            print(f"You entered: {user_input}")
            
            if user_input.lower() in ['exit', 'quit']:
                break
                
        except KeyboardInterrupt:
            break
    
    print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())