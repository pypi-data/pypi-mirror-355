"""
Interactive mode for agentctl with auto-completion.

AI_CONTEXT:
    This module provides an interactive REPL (Read-Eval-Print-Loop) for
    agentctl that includes:
    
    1. Tab completion for tool names and parameters
    2. Syntax highlighting for commands
    3. History tracking across sessions
    4. Inline help and suggestions
    5. Direct tool execution without typing 'agtos'
    
    The interactive mode makes it easier to explore and use agtos's
    many tools with a rich, user-friendly interface.
"""

import sys
import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings

from ..completion.engine import AutoCompleteEngine, CompletionContext
from ..metamcp.registry import ServiceRegistry
from ..metamcp.router import Router

console = Console()


class AgentCtlCompleter(Completer):
    """Prompt toolkit completer that uses agtos's completion engine.
    
    AI_CONTEXT:
        This completer integrates with prompt_toolkit to provide
        real-time completions in the interactive prompt. It:
        
        1. Delegates to AutoCompleteEngine for suggestions
        2. Formats completions with metadata
        3. Provides inline documentation
        4. Handles both tool names and parameters
    """
    
    def __init__(self, engine: AutoCompleteEngine):
        """Initialize completer with completion engine.
        
        Args:
            engine: AutoCompleteEngine instance
        """
        self.engine = engine
        self.recent_tools: List[str] = []
        
    def get_completions(self, document, complete_event):
        """Get completions for the current document.
        
        This is called by prompt_toolkit when tab is pressed.
        """
        # Create context from document
        context = CompletionContext(
            partial_input=document.text_before_cursor.split()[-1] if document.text_before_cursor else "",
            cursor_position=document.cursor_position,
            full_command=document.text,
            recent_tools=self.recent_tools[-10:]  # Last 10 tools
        )
        
        # Get candidates from engine
        candidates = self.engine.complete(context)
        
        # Convert to prompt_toolkit completions
        for candidate in candidates:
            # Create display text with metadata
            display_parts = [candidate.display]
            
            if candidate.description:
                display_parts.append(f" - {candidate.description}")
                
            if candidate.type == "alias":
                display_parts.append(" [alias]")
            elif candidate.type == "parameter":
                display_parts.append(" [param]")
                
            display = HTML(" ".join(display_parts))
            
            # Calculate start position
            start_position = -len(context.partial_input)
            
            yield Completion(
                text=candidate.value,
                start_position=start_position,
                display=display,
                display_meta=candidate.description
            )
    
    def add_to_history(self, tool_name: str):
        """Add a tool to recent history."""
        if tool_name not in self.recent_tools:
            self.recent_tools.append(tool_name)
        else:
            # Move to end if already in list
            self.recent_tools.remove(tool_name)
            self.recent_tools.append(tool_name)


class InteractiveSession:
    """Interactive REPL session for agtos.
    
    AI_CONTEXT:
        This class manages an interactive session where users can:
        
        1. Execute tools directly without 'agtos' prefix
        2. Get tab completion and suggestions
        3. View help for tools inline
        4. Track command history
        5. Execute tools and see results
        
        The session maintains state including the registry,
        router, and execution context.
    """
    
    def __init__(self, registry: ServiceRegistry, debug: bool = False):
        """Initialize interactive session.
        
        Args:
            registry: Service registry with available tools
            debug: Enable debug mode
        """
        self.registry = registry
        self.router = Router(registry)
        self.debug = debug
        
        # Set up completion
        self.engine = AutoCompleteEngine(registry=registry)
        self.completer = AgentCtlCompleter(self.engine)
        
        # Set up history
        history_file = Path.home() / ".agtos" / "interactive_history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = FileHistory(str(history_file))
        
        # Set up key bindings
        self.bindings = self._create_key_bindings()
        
        # Create prompt session
        self.session = PromptSession(
            completer=self.completer,
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            complete_while_typing=True,
            enable_history_search=True,
            key_bindings=self.bindings,
            style=self._create_style()
        )
        
        # Track session state
        self.command_count = 0
        self.last_result = None
        
    def _create_style(self) -> Style:
        """Create style for the prompt."""
        return Style.from_dict({
            'prompt': '#00aa00 bold',
            'continuation': '#888888',
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
            'scrollbar.background': 'bg:#88aaaa',
            'scrollbar.button': 'bg:#222222',
        })
    
    def _create_key_bindings(self) -> KeyBindings:
        """Create custom key bindings."""
        kb = KeyBindings()
        
        @kb.add('c-h')
        def show_help(event):
            """Show help for current command."""
            # Get current text
            text = event.app.current_buffer.text
            if text:
                self._show_inline_help(text)
        
        @kb.add('c-l')
        def clear_screen(event):
            """Clear the screen."""
            event.app.renderer.clear()
        
        return kb
    
    async def run(self):
        """Run the interactive session."""
        # Show welcome message
        self._show_welcome()
        
        # Main loop
        while True:
            try:
                # Get input with prompt
                prompt_text = HTML(f'<prompt>agentctl [{self.command_count}]></prompt> ')
                
                command = await self.session.prompt_async(
                    prompt_text,
                    multiline=False,
                    mouse_support=True
                )
                
                # Handle special commands
                if command.lower() in ['exit', 'quit', 'q']:
                    break
                elif command.lower() in ['help', '?']:
                    self._show_help()
                    continue
                elif command.lower() == 'clear':
                    console.clear()
                    continue
                elif command.lower() == 'tools':
                    self._list_tools()
                    continue
                elif command.startswith('help '):
                    tool_name = command[5:].strip()
                    self._show_tool_help(tool_name)
                    continue
                
                # Execute command
                if command.strip():
                    await self._execute_command(command)
                    self.command_count += 1
                    
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                if self.debug:
                    import traceback
                    console.print(traceback.format_exc())
        
        # Show goodbye
        console.print("\n[cyan]Thanks for using agentctl interactive mode![/cyan]")
    
    def _show_welcome(self):
        """Show welcome message with tips."""
        welcome = """
[bold cyan]Welcome to agentctl Interactive Mode![/bold cyan]

Tips:
  • Type tool names directly (no 'agtos' prefix needed)
  • Press [bold]Tab[/bold] for auto-completion
  • Press [bold]Ctrl+H[/bold] for help on current command
  • Type [bold]tools[/bold] to list all available tools
  • Type [bold]help <tool>[/bold] for tool documentation
  • Type [bold]exit[/bold] or press [bold]Ctrl+D[/bold] to quit

Example: [cyan]cli__git__status[/cyan] or [cyan]show git status[/cyan]
        """
        
        console.print(Panel(
            welcome.strip(),
            title="agtos Interactive",
            border_style="cyan"
        ))
    
    def _show_help(self):
        """Show general help."""
        help_text = """
[bold]Available Commands:[/bold]

  [cyan]<tool_name>[/cyan] [params]  - Execute a tool
  [cyan]help[/cyan] <tool>          - Show help for a tool  
  [cyan]tools[/cyan]               - List all available tools
  [cyan]clear[/cyan]               - Clear the screen
  [cyan]exit[/cyan]                - Exit interactive mode

[bold]Keyboard Shortcuts:[/bold]

  [cyan]Tab[/cyan]                 - Auto-complete
  [cyan]Ctrl+H[/cyan]              - Help for current command
  [cyan]Ctrl+R[/cyan]              - Search history
  [cyan]Ctrl+L[/cyan]              - Clear screen
  [cyan]Ctrl+D[/cyan]              - Exit

[bold]Natural Language:[/bold]

You can use natural language aliases:
  • "show files" → filesystem__list_directory
  • "git status" → cli__git__status
  • "run tests" → cli__pytest or cli__npm__test
        """
        
        console.print(Panel(
            help_text.strip(),
            title="Help",
            border_style="yellow"
        ))
    
    def _list_tools(self):
        """List all available tools organized by service."""
        console.print(Panel(
            "[bold]Available Tools[/bold]",
            border_style="cyan"
        ))
        
        # Group tools by service
        by_service = {}
        for service_name, service in self.registry.services.items():
            if service.tools:
                by_service[service_name] = service.tools
        
        # Display each service
        for service_name, tools in sorted(by_service.items()):
            console.print(f"\n[bold cyan]{service_name}:[/bold cyan]")
            
            # Create table for tools
            table = Table(show_header=False, padding=(0, 2))
            table.add_column("Tool", style="green")
            table.add_column("Description", style="white")
            
            for tool in sorted(tools, key=lambda t: t.name)[:10]:  # Limit to 10 per service
                # Get aliases for this tool
                aliases = self.engine.alias_registry.suggest_aliases(tool.name)
                alias_text = f" [{aliases[0]}]" if aliases else ""
                
                table.add_row(
                    tool.name + alias_text,
                    tool.description[:60] + "..." if len(tool.description) > 60 else tool.description
                )
            
            console.print(table)
            
            if len(tools) > 10:
                console.print(f"  [dim]... and {len(tools) - 10} more[/dim]")
    
    def _show_tool_help(self, tool_name: str):
        """Show detailed help for a specific tool."""
        # Find tool in registry
        tool_spec, service_name = self._find_tool(tool_name)
        
        if not tool_spec:
            self._handle_tool_not_found(tool_name)
            return
        
        # Display all tool information
        self._display_tool_info(tool_spec, service_name)
        self._display_tool_parameters(tool_spec)
        self._display_tool_aliases(tool_spec)
        self._display_tool_example(tool_spec)
    
    def _find_tool(self, tool_name: str):
        """Find a tool by name in the registry.
        
        Returns:
            Tuple of (tool_spec, service_name) or (None, None) if not found
        """
        for svc_name, service in self.registry.services.items():
            for tool in service.tools:
                if tool.name == tool_name:
                    return tool, svc_name
        return None, None
    
    def _handle_tool_not_found(self, tool_name: str):
        """Handle the case when a tool is not found."""
        # Try to find by alias
        alias_result = self.engine.alias_registry.find_tool(tool_name)
        if alias_result:
            actual_tool, confidence = alias_result
            console.print(f"[yellow]'{tool_name}' is an alias for {actual_tool}[/yellow]\n")
            self._show_tool_help(actual_tool)
            return
        
        console.print(f"[red]Tool not found: {tool_name}[/red]")
        
        # Suggest similar tools
        suggestions = self.engine.get_suggestions_for_error(
            f"Tool '{tool_name}' not found", 
            tool_name
        )
        if suggestions:
            console.print("\n[yellow]Suggestions:[/yellow]")
            for suggestion in suggestions:
                console.print(f"  • {suggestion}")
    
    def _display_tool_info(self, tool_spec, service_name: str):
        """Display basic tool information panel."""
        console.print(Panel(
            f"[bold]{tool_spec.name}[/bold]\n\n"
            f"Service: {service_name}\n"
            f"Description: {tool_spec.description or 'No description available'}",
            title="Tool Information",
            border_style="green"
        ))
    
    def _display_tool_parameters(self, tool_spec):
        """Display tool parameters in a table."""
        if not tool_spec.inputSchema:
            return
            
        properties = tool_spec.inputSchema.get("properties", {})
        required = tool_spec.inputSchema.get("required", [])
        
        if properties:
            console.print("\n[bold]Parameters:[/bold]")
            
            param_table = Table(show_header=True)
            param_table.add_column("Parameter", style="cyan")
            param_table.add_column("Type", style="yellow")
            param_table.add_column("Required", style="green")
            param_table.add_column("Description", style="white")
            
            for param_name, param_schema in properties.items():
                param_table.add_row(
                    f"--{param_name}",
                    param_schema.get("type", "string"),
                    "Yes" if param_name in required else "No",
                    param_schema.get("description", "")
                )
            
            console.print(param_table)
    
    def _display_tool_aliases(self, tool_spec):
        """Display natural language aliases for the tool."""
        aliases = self.engine.alias_registry.suggest_aliases(tool_spec.name)
        if aliases:
            console.print("\n[bold]Natural Language Aliases:[/bold]")
            for alias in aliases:
                console.print(f"  • {alias}")
    
    def _display_tool_example(self, tool_spec):
        """Display example usage for the tool."""
        console.print("\n[bold]Example Usage:[/bold]")
        example = tool_spec.name
        if tool_spec.inputSchema and tool_spec.inputSchema.get("required"):
            example += " " + " ".join(f"--{p} <value>" for p in tool_spec.inputSchema["required"])
        console.print(f"  [cyan]{example}[/cyan]")
    
    def _show_inline_help(self, command: str):
        """Show inline help for the current command."""
        parts = command.split()
        if not parts:
            return
            
        tool_name = parts[0]
        self._show_tool_help(tool_name)
    
    async def _execute_command(self, command: str):
        """Execute a command."""
        # Parse command
        parts = command.split()
        if not parts:
            return
        
        tool_input = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Try to resolve tool name (could be alias)
        tool_name = tool_input
        alias_result = self.engine.alias_registry.find_tool(tool_input)
        
        if alias_result:
            tool_name, confidence = alias_result
            if confidence > 0.5:
                console.print(f"[dim]Using tool: {tool_name}[/dim]")
            else:
                # Low confidence, ask for confirmation
                from rich.prompt import Confirm
                if not Confirm.ask(f"Did you mean '{tool_name}'?"):
                    return
        
        # Route to service
        try:
            service_name = self.router.route_tool(tool_name)
        except Exception as e:
            console.print(f"[red]Routing error: {e}[/red]")
            
            # Show suggestions
            suggestions = self.engine.get_suggestions_for_error(str(e), tool_name)
            if suggestions:
                console.print("\n[yellow]Suggestions:[/yellow]")
                for suggestion in suggestions:
                    console.print(f"  • {suggestion}")
            return
        
        # Parse arguments
        arguments = self._parse_arguments(args)
        
        # Execute tool
        console.print(f"[cyan]Executing {tool_name} via {service_name}...[/cyan]")
        
        try:
            result = await self.registry.execute_tool(
                service_name,
                tool_name,
                arguments
            )
            
            # Display result
            self._display_result(result)
            
            # Record usage
            self.engine.record_usage(tool_name, arguments)
            self.completer.add_to_history(tool_name)
            self.last_result = result
            
        except Exception as e:
            console.print(f"[red]Execution error: {e}[/red]")
            if self.debug:
                import traceback
                console.print(traceback.format_exc())
    
    def _parse_arguments(self, args: List[str]) -> Dict[str, Any]:
        """Parse command line arguments into a dictionary."""
        arguments = {}
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg.startswith('--'):
                # Long option
                key = arg[2:]
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    # Has value
                    value = args[i + 1]
                    # Try to parse as JSON
                    try:
                        value = json.loads(value)
                    except:
                        # Keep as string
                        pass
                    arguments[key] = value
                    i += 2
                else:
                    # Boolean flag
                    arguments[key] = True
                    i += 1
            elif arg.startswith('-'):
                # Short option
                key = arg[1:]
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    arguments[key] = args[i + 1]
                    i += 2
                else:
                    arguments[key] = True
                    i += 1
            else:
                # Positional argument
                if '_positional' not in arguments:
                    arguments['_positional'] = []
                arguments['_positional'].append(arg)
                i += 1
        
        return arguments
    
    def _display_result(self, result: Any):
        """Display execution result."""
        if isinstance(result, dict):
            if result.get("success") is False:
                # Error result
                console.print(Panel(
                    f"[red]{result.get('error', 'Unknown error')}[/red]",
                    title="Error",
                    border_style="red"
                ))
                
                if "details" in result:
                    console.print("\n[yellow]Details:[/yellow]")
                    for key, value in result["details"].items():
                        if value and key != "traceback":  # Skip traceback unless debug
                            console.print(f"  {key}: {value}")
                            
                    if self.debug and "traceback" in result["details"]:
                        console.print("\n[dim]Traceback:[/dim]")
                        console.print(result["details"]["traceback"])
                        
            elif "output" in result:
                # Command output
                console.print(result["output"])
                
            elif "content" in result:
                # MCP result format
                content = result["content"]
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            console.print(item["text"])
                        else:
                            console.print(str(item))
                else:
                    console.print(str(content))
                    
            else:
                # Generic result
                console.print(json.dumps(result, indent=2))
                
        else:
            # Non-dict result
            console.print(str(result))


def register_interactive_command(app: typer.Typer):
    """Register the interactive command with the CLI.
    
    AI_CONTEXT:
        This adds the 'interactive' command to agtos's CLI,
        allowing users to enter an interactive REPL mode.
    """
    
    @app.command()
    def interactive(
        debug: bool = typer.Option(
            False,
            "--debug", "-d",
            help="Enable debug mode with detailed error output"
        ),
        project: Optional[str] = typer.Option(
            None,
            "--project", "-p",
            help="Load specific project context"
        )
    ):
        """Start interactive mode with auto-completion and rich UI.
        
        AI_CONTEXT:
            This command launches an interactive REPL where users can:
            - Execute tools directly without the 'agtos' prefix
            - Use tab completion for tool names and parameters
            - Access inline help and documentation
            - Use natural language aliases
            - Track command history across sessions
        """
        console.print(Panel(
            "[bold cyan]Starting agentctl Interactive Mode...[/bold cyan]",
            border_style="cyan"
        ))
        
        try:
            # Create registry
            from ..mcp_server import create_registry
            
            # Load project if specified
            env_vars = {}
            if project:
                from ..project_store import ProjectStore
                store = ProjectStore()
                project_data = store.get_project(project)
                if project_data:
                    env_vars = project_data.env_vars
                    console.print(f"[green]Loaded project: {project}[/green]")
                else:
                    console.print(f"[yellow]Warning: Project '{project}' not found[/yellow]")
            
            # Create registry with environment
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Loading tools and services...", total=None)
                
                registry = create_registry(debug=debug, env_vars=env_vars)
                
                # Wait for services to be ready
                import time
                time.sleep(1)  # Give services time to initialize
                
                progress.update(task, completed=100)
            
            # Count available tools
            total_tools = sum(len(svc.tools) for svc in registry.services.values())
            console.print(f"[green]✓ Loaded {total_tools} tools from {len(registry.services)} services[/green]\n")
            
            # Create and run session
            session = InteractiveSession(registry, debug=debug)
            
            # Run async session
            asyncio.run(session.run())
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed to start interactive mode: {e}[/red]")
            if debug:
                import traceback
                console.print(traceback.format_exc())
            raise typer.Exit(1)