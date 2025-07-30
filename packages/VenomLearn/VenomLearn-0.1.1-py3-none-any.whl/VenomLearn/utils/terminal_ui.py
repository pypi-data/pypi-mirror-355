"""Terminal UI module for VenomLearn learning package.

This module provides a rich terminal user interface for the learning package.
"""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.prompt import Prompt
from VenomLearn.config import UI_THEME

console = Console()


class TerminalUI:
    """Terminal UI class for VenomLearn learning package."""
    
    def __init__(self):
        """Initialize the Terminal UI."""
        self.console = Console()
        self.theme = UI_THEME
    
    def display_section(self, title):
        """Display a section title."""
        self.console.print(f"\n[bold {self.theme['primary']}]== {title} ==[/bold {self.theme['primary']}]")
        self.console.print("─" * (len(title) + 6))
    
    def display_code(self, code, language="python"):
        """Display code with syntax highlighting."""
        syntax = Syntax(code.strip(), language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, border_style=self.theme['secondary']))
        self.console.print("")
    
    def display_exercise(self, title):
        """Display an exercise title."""
        self.console.print(f"\n[bold {self.theme['accent']}]{title}[/bold {self.theme['accent']}]")
        self.console.print("─" * len(title))
    
    def display_info(self, message):
        """Display an informational message."""
        self.console.print(f"[{self.theme['info']}]ℹ {message}[/{self.theme['info']}]")
    
    def display_success(self, message):
        """Display a success message."""
        self.console.print(f"[{self.theme['accent']}]✓ {message}[/{self.theme['accent']}]")
    
    def display_error(self, message):
        """Display an error message."""
        self.console.print(f"[{self.theme['error']}]✗ {message}[/{self.theme['error']}]")
    
    def display_markdown(self, markdown_text):
        """Display markdown text."""
        md = Markdown(markdown_text)
        self.console.print(md)
    
    def get_code_input(self):
        """Get code input from the user."""
        self.console.print("\n[bold]Enter your code below (type 'done' on a new line when finished):[/bold]")
        lines = []
        while True:
            line = Prompt.ask("> ")
            if line.strip().lower() == "done":
                break
            lines.append(line)
        return "\n".join(lines)
    
    def display_progress(self, completed, total):
        """Display progress bar."""
        from rich.progress import Progress
        
        with Progress() as progress:
            task = progress.add_task("[green]Progress", total=total)
            progress.update(task, completed=completed)
