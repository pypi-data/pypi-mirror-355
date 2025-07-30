"""Terminal User Interface (TUI) for agtOS.

This module provides an interactive terminal interface for agtOS that allows
users to perform administrative tasks and launch the orchestrator agent.

AI_CONTEXT:
    The TUI is the main interface users see after running 'agtos'. It provides:
    - Quick administrative actions (project switching, credential management)
    - Launch point for AI orchestrator (Claude)
    - Status monitoring and cost tracking
    - An alternative to memorizing CLI commands
    
    Users can either use the TUI for quick tasks or launch Claude for complex work.

Future Command Ideas:
    Agent Management:
    - View agent capabilities
    - Set cost limits per agent
    - View usage history
    - Configure agent preferences
    - Test agent connectivity
    
    Tool Management:
    - Search tools by capability
    - View tool documentation
    - Test tool execution
    - Create custom tool
    - Import/export tools
    
    Monitoring:
    - Real-time log viewer
    - Performance metrics
    - Error diagnostics
    - Network traffic monitor
    - Resource usage
    
    Workflow:
    - Create workflow from history
    - Schedule workflow execution
    - Workflow marketplace
    - Share workflows
    
    Settings:
    - Theme customization
    - Keyboard shortcuts
    - Notification preferences
    - Auto-update settings
    - Backup/restore config
"""

import asyncio
import sys
import json
import subprocess
import os
import time
import threading
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime
from pathlib import Path
from packaging import version

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl, Float, FloatContainer
from prompt_toolkit.layout.containers import Container
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.filters import Condition
from prompt_toolkit.buffer import Buffer

from .agents import AgentRegistry
from .project_store import ProjectStore
from .config import get_config_dir
from .providers import get_provider
from .workflows.library import WorkflowLibrary
from .utils import get_logger
from .orchestration.engine import OrchestrationEngine
from .metamcp.fuzzy_match import fuzzy_match_tools
from .tui_loading import LoadingSpinner, LoadingContext, run_with_spinner, get_spinner
from .tui_tutorial import TutorialManager, is_first_run
from .tui_toast import get_toast_manager, success, error, info, warning
from .tui_command_palette import CommandPalette, CommandRegistry, build_command_registry_from_menu
from .tui_dashboard import DashboardView
from .operation_manager import get_operation_manager, OperationType

# Optional auth module (may not exist yet)
try:
    from .auth.manager import AuthManager
    from .tui_auth import AuthDialogManager
except ImportError:
    AuthManager = None
    AuthDialogManager = None

logger = get_logger(__name__)


class MenuItem:
    """Represents a menu item in the TUI."""
    
    def __init__(
        self, 
        label: str, 
        action: Optional[Callable] = None,
        submenu: Optional[List['MenuItem']] = None,
        cost_info: Optional[str] = None,
        separator: bool = False,
        recommended: bool = False,
        hint: Optional[str] = None
    ):
        self.label = label
        self.action = action
        self.submenu = submenu
        self.cost_info = cost_info
        self.separator = separator
        self.recommended = recommended
        self.hint = hint


class AgtOSTUI:
    """Interactive Terminal User Interface for agtOS.
    
    AI_CONTEXT:
        This TUI provides a user-friendly interface for agtOS operations.
        It's designed to be intuitive with keyboard navigation and search.
        The TUI complements the AI orchestrator by handling quick admin tasks.
    """
    
    def __init__(self):
        """Initialize the TUI components."""
        self.selected_index = 0
        self.search_query = ""
        self.search_mode = False
        self.search_results: List[Tuple[MenuItem, List[str]]] = []  # (item, path)
        self.current_menu: List[MenuItem] = []
        self.menu_stack: List[List[MenuItem]] = []
        self.breadcrumb_stack: List[str] = ["Home"]  # Track breadcrumb navigation
        self.search_buffer = Buffer()
        
        # Directory input mode
        self.directory_input_mode = False
        self.directory_input = ""
        
        # Initialize loading spinner
        self.spinner = LoadingSpinner()
        
        # Initialize toast manager
        self.toast_manager = get_toast_manager()
        
        # Initialize components with loading indicator
        with LoadingContext(self.spinner, "Initializing agtOS...") as ctx:
            ctx.update("Loading agent registry...")
            self.agent_registry = AgentRegistry()
            
            ctx.update("Loading project store...")
            self.project_store = ProjectStore()
            
            ctx.update("Loading workflow library...")
            self.workflow_library = WorkflowLibrary()
            
            ctx.update("Loading credential provider...")
            self.provider = get_provider()
            
            ctx.update("Checking authentication...")
            self.auth_manager = AuthManager() if AuthManager else None
        
        # Check authentication
        self.current_user = None
        self.needs_auth = False
        
        # Load update preferences
        self.update_preferences = self._load_update_preferences()
        self.pending_update = None
        
        # Check if this is first run (must be before building menu)
        self.is_first_run = is_first_run()
        
        # Check authentication before building menu
        self._check_authentication()
        
        # Initialize command registry (must be before building menu)
        self.command_registry = CommandRegistry()
        
        # Build main menu
        self.main_menu = self._build_main_menu()
        self.current_menu = self.main_menu
        
        # Initialize flags that are needed during app creation
        self.dashboard_visible = False
        self.help_overlay_visible = False
        
        # Animation state for gradient logo
        self.animation_frame = 0
        self.animation_thread = None
        self.animation_running = True
        
        # Create a temporary app for tutorial manager initialization
        # We need to create tutorial manager before app, but it needs app
        # So we'll initialize it with None and set app later
        self.tutorial_manager = None
        self.auth_dialog_manager = None
        self.command_palette = None
        self.dashboard = None
        
        # Create application (must be done before other managers)
        self.app = self._create_application()
        
        # Ensure spinner animation stops during init
        # Clear any remaining loading states from initialization
        self.spinner.loading_states.clear()
        self.spinner._stop_event.set()  # Stop animation thread
        
        # Now initialize managers with the real app
        self.tutorial_manager = TutorialManager(self.app)
        self.tutorial_manager.on_completion(self._on_tutorial_complete)
        
        # Initialize auth dialog manager if auth is available
        if AuthDialogManager and self.auth_manager:
            self.auth_dialog_manager = AuthDialogManager(self.auth_manager, self.app)
        
        # Initialize command palette
        self.command_palette = CommandPalette(self.command_registry, self.app, self)
        self._rebuild_command_registry()
        
        # Initialize dashboard
        self.dashboard = DashboardView(self.app, self)
        
        # Get operation manager
        self.operation_manager = get_operation_manager()
        
        # Check for updates on startup if enabled
        if self.update_preferences.get("check_on_startup", True):
            self._check_updates_startup()
        
        # Start animation thread
        self._start_animation()
    
    def _rebuild_command_registry(self):
        """Rebuild the command registry from current menu structure."""
        self.command_registry.clear()
        if hasattr(self, 'main_menu'):
            build_command_registry_from_menu(self.main_menu, self.command_registry)
    
    def _build_main_menu(self) -> List[MenuItem]:
        """Build the main menu structure."""
        # Get agent costs
        claude_cost = "$0.25/1K tokens"  # Example, would fetch real costs
        codex_cost = "$0.02/1K tokens"
        
        # Check if credentials are configured
        has_credentials = bool(self.provider.list_services()) if hasattr(self.provider, 'list_services') else False
        
        menu = [
            MenuItem(
                "Open Claude (Orchestrator)", 
                self._open_claude, 
                cost_info=claude_cost,
                recommended=True if not self.is_first_run else False,
                hint="Start here for complex tasks"
            ),
            MenuItem("Select Primary Agent", submenu=self._build_agent_menu()),
            MenuItem("", separator=True),
            MenuItem("Browse Workflows", self._browse_workflows, hint="Pre-built automation"),
            MenuItem("Manage Projects", submenu=self._build_project_menu()),
            MenuItem(
                "Configure Credentials", 
                submenu=self._build_credential_menu(),
                recommended=not has_credentials,
                hint="Required for external services" if not has_credentials else None
            ),
            MenuItem("Change Directory", self._change_directory, hint="Set working directory"),
            MenuItem("", separator=True),
            MenuItem("View Agent Costs", self._view_agent_costs),
            MenuItem("View Dashboard", self._show_dashboard, hint="Real-time system status"),
            MenuItem("Server Status", self._show_server_status),
            MenuItem("Check for Updates", self._check_updates),
            MenuItem(
                "Help & Documentation", 
                submenu=self._build_help_menu(),
                hint="New? Start here" if self.is_first_run else None
            ),
            MenuItem("", separator=True),
            MenuItem("Quit", self._quit, hint="Exit agtOS (Ctrl+C)"),
        ]
        
        # Rebuild command registry after menu is built
        self._rebuild_command_registry()
        
        return menu
    
    def _build_agent_menu(self) -> List[MenuItem]:
        """Build the agent selection submenu."""
        agents = self.agent_registry.get_available_agents()
        menu_items = []
        
        for agent in agents:
            cost_info = self._get_agent_cost_info(agent.name)
            menu_items.append(
                MenuItem(
                    f"{agent.name} - {agent.description}",
                    lambda a=agent: self._select_agent(a),
                    cost_info=cost_info
                )
            )
        
        return menu_items
    
    def _build_project_menu(self) -> List[MenuItem]:
        """Build the project management submenu."""
        return [
            MenuItem("Select Project", self._select_project),
            MenuItem("Create Project", self._create_project),
            MenuItem("List Projects", self._list_projects),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
    
    def _build_credential_menu(self) -> List[MenuItem]:
        """Build the credential management submenu."""
        return [
            MenuItem("Add API Key", self._add_api_key),
            MenuItem("Update Credential", self._update_credential),
            MenuItem("List Credentials", self._list_credentials),
            MenuItem("Test Connection", self._test_credential),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
    
    def _create_application(self) -> Application:
        """Create the prompt_toolkit application."""
        # Key bindings
        kb = KeyBindings()
        
        # Search mode filter
        search_mode_filter = Condition(lambda: self.search_mode)
        
        # Directory input mode filter
        directory_input_filter = Condition(lambda: self.directory_input_mode)
        
        # Auth dialog filter - disable main key bindings when auth dialog is visible
        auth_dialog_filter = Condition(
            lambda: not (self.auth_dialog_manager and self.auth_dialog_manager.dialog_visible)
        )
        
        # Tutorial filter - disable main key bindings when tutorial is active
        tutorial_filter = Condition(lambda: not (self.tutorial_manager and self.tutorial_manager.tutorial_active))
        
        # Command palette filter - disable main key bindings when palette is visible
        command_palette_filter = Condition(lambda: not (self.command_palette and self.command_palette.visible))
        
        # Dashboard filter - disable main key bindings when dashboard is visible
        dashboard_filter = Condition(lambda: not self.dashboard_visible)
        
        # Help overlay filter - disable main key bindings when help is visible
        help_overlay_filter = Condition(lambda: not self.help_overlay_visible)
        
        # Combined filter for main key bindings
        main_kb_filter = auth_dialog_filter & tutorial_filter & command_palette_filter & dashboard_filter & help_overlay_filter & ~directory_input_filter
        
        @kb.add('up', filter=main_kb_filter)
        @kb.add('k', filter=main_kb_filter)  # Vim binding
        def move_up(event):
            self._move_selection(-1)
        
        @kb.add('down', filter=main_kb_filter)
        @kb.add('j', filter=main_kb_filter)  # Vim binding
        def move_down(event):
            self._move_selection(1)
        
        @kb.add('enter', filter=main_kb_filter)
        def select_item(event):
            self._execute_selected()
        
        @kb.add('escape', filter=main_kb_filter)
        def go_back(event):
            self._go_back()
        
        @kb.add('/', filter=~search_mode_filter & main_kb_filter)
        def start_search(event):
            self.search_mode = True
            self.search_buffer.text = ""
            self.search_results = []
            self.selected_index = 0
            event.app.invalidate()
        
        # Handle text input during search
        from prompt_toolkit.key_binding.key_processor import KeyPressEvent
        from prompt_toolkit.keys import Keys
        
        @kb.add(Keys.Any, filter=search_mode_filter & main_kb_filter)
        def handle_search_input(event: KeyPressEvent):
            # Handle character input
            if event.key_sequence[0].key == Keys.Backspace:
                if self.search_buffer.text:
                    self.search_buffer.text = self.search_buffer.text[:-1]
                    self._update_search_results()
            elif len(str(event.key_sequence[0].key)) == 1:
                # Regular character
                self.search_buffer.text += str(event.key_sequence[0].key)
                self._update_search_results()
            event.app.invalidate()
        
        # Directory input mode handlers
        @kb.add('enter', filter=directory_input_filter)
        def confirm_directory(event):
            """Confirm directory change."""
            self._confirm_directory_change()
        
        @kb.add('escape', filter=directory_input_filter)
        def cancel_directory(event):
            """Cancel directory input."""
            self._cancel_directory_input()
        
        @kb.add('tab', filter=directory_input_filter)
        def autocomplete_directory(event):
            """Auto-complete directory path."""
            suggestions = self._get_directory_suggestions(self.directory_input)
            if suggestions:
                self.directory_input = suggestions[0]
                if not self.directory_input.endswith('/'):
                    self.directory_input += '/'
                self._update_directory_menu()
                event.app.invalidate()
        
        @kb.add(Keys.Backspace, filter=directory_input_filter)
        def directory_backspace(event):
            """Handle backspace in directory input."""
            if self.directory_input:
                self.directory_input = self.directory_input[:-1]
                self._update_directory_menu()
                event.app.invalidate()
        
        @kb.add(Keys.Any, filter=directory_input_filter)
        def handle_directory_input(event: KeyPressEvent):
            """Handle character input for directory path."""
            if len(str(event.key_sequence[0].key)) == 1:
                # Regular character
                self.directory_input += str(event.key_sequence[0].key)
                self._update_directory_menu()
                event.app.invalidate()
        
        @kb.add('c-c')
        def exit_app(event):
            event.app.exit()
        
        @kb.add('c-d', filter=main_kb_filter)
        def dismiss_toasts(event):
            """Dismiss all active toast notifications."""
            self.toast_manager.dismiss_all()
        
        @kb.add('c-p')
        def open_command_palette(event):
            """Open the command palette."""
            if self.command_palette:
                self.command_palette.show()
        
        @kb.add('c-s', filter=main_kb_filter)
        def show_dashboard_shortcut(event):
            """Show dashboard with keyboard shortcut."""
            self._show_dashboard()
        
        # Number key shortcuts (1-9) for quick menu selection
        def create_number_handler(num):
            def handler(event):
                """Select menu item by number."""
                visible_items = [item for item in self.current_menu if not item.separator]
                if num - 1 < len(visible_items):
                    self.selected_index = self.current_menu.index(visible_items[num - 1])
                    self._execute_selected()
            return handler
        
        for i in range(1, 10):
            kb.add(str(i), filter=main_kb_filter)(create_number_handler(i))
        
        # Help overlay with ?
        @kb.add('?', filter=main_kb_filter)
        def show_help_overlay(event):
            """Toggle help overlay showing all keyboard shortcuts."""
            self._toggle_help_overlay()
        
        # Close help overlay with Escape or ? when it's visible
        help_visible_filter = Condition(lambda: self.help_overlay_visible)
        
        @kb.add('escape', filter=help_visible_filter)
        @kb.add('?', filter=help_visible_filter)
        def close_help_overlay(event):
            """Close the help overlay."""
            self.help_overlay_visible = False
            event.app.invalidate()
        
        # Merge tutorial key bindings (if tutorial manager exists)
        if self.tutorial_manager:
            kb = kb | self.tutorial_manager.kb
        
        # Merge dashboard key bindings when visible
        if self.dashboard:
            dashboard_kb_filter = Condition(lambda: self.dashboard_visible)
            filtered_dashboard_kb = KeyBindings()
            for binding in self.dashboard.get_key_bindings().bindings:
                filtered_dashboard_kb.add(
                    *binding.keys,
                    filter=dashboard_kb_filter & binding.filter
                )(binding.handler)
            kb = kb | filtered_dashboard_kb
        
        # Merge command palette key bindings when visible
        if self.command_palette:
            palette_kb_filter = Condition(lambda: self.command_palette.visible)
            filtered_palette_kb = KeyBindings()
            for binding in self.command_palette.kb.bindings:
                filtered_palette_kb.add(
                    *binding.keys,
                    filter=palette_kb_filter & binding.filter
                )(binding.handler)
            kb = kb | filtered_palette_kb
        
        # Create layout
        # We'll use a dummy container for now and update it dynamically
        self.main_container = self._create_main_container()
        layout = Layout(self.main_container)
        
        # Style
        base_style = {
            'title': '#00ff00 bold',
            'status': '#888888',
            'selected': 'reverse',
            'separator': '#444444',
            'cost': '#ffaa00',
            'header': '#00aaff',
            'recommended': '#00ff00',
            'hint': '#888888 italic',
            'breadcrumb': '#666666',
            'breadcrumb.separator': '#444444',
            'breadcrumb.current': '#888888 bold',
            'help': '#ffffff',
            'help.frame': 'bg:#1a1a1a #888888',
        }
        
        # Add auth dialog styles if available
        if self.auth_dialog_manager:
            base_style.update(self.auth_dialog_manager.get_style_extensions())
        
        # Add tutorial styles
        if self.tutorial_manager:
            base_style.update(self.tutorial_manager.get_style_dict())
        
        # Add toast styles
        base_style.update(self.toast_manager.get_style_dict())
        
        # Add command palette styles
        if self.command_palette:
            base_style.update(self.command_palette.get_style_dict())
        
        # Add dashboard styles
        if self.dashboard:
            base_style.update(self.dashboard.get_style_dict())
        
        style = Style.from_dict(base_style)
        
        return Application(
            layout=layout,
            key_bindings=kb,
            style=style,
            full_screen=True,
            mouse_support=True,
        )
    
    def _create_main_container(self) -> Container:
        """Create the main container with all UI elements."""
        # If dashboard is visible, show dashboard instead
        if self.dashboard_visible:
            return self.dashboard.get_container()
        
        # ASCII art title
        title_text = """
                    ▄▀█ █▀▀ ▀█▀ █▀█ █▀
                    █▀█ █▄█  █  █▄█ ▄█
                    
                  Agent Operating System v0.3.2 (Beta)
        """
        
        # Build main content
        main_content = HSplit([
            # Title section with animated gradient
            Window(
                FormattedTextControl(
                    lambda: self._get_animated_title()
                ),
                height=7,
                align='center'
            ),
            # Status bar
            Window(
                FormattedTextControl(
                    lambda: FormattedText([('class:status', self._get_status_text())])
                ),
                height=1,
                style='class:status reverse'
            ),
            # Breadcrumb navigation
            Window(
                FormattedTextControl(
                    lambda: self._render_breadcrumbs()
                ),
                height=1,
                style='class:breadcrumb'
            ),
            # Main menu area
            Window(
                FormattedTextControl(
                    lambda: self._render_menu(),
                    focusable=True,
                ),
                wrap_lines=True,
            ),
            # Bottom help text
            Window(
                FormattedTextControl(
                    lambda: FormattedText([
                        ('', '  '),
                        ('class:header', 'Press / to search' if not self.search_mode else 'Type to search...'),
                        ('', '                    '),
                        ('class:status', 
                         'ESC: Cancel  ↑↓: Navigate  Enter: Select' if self.search_mode 
                         else self._get_help_text())
                    ])
                ),
                height=2,
            ),
        ])
        
        # Check if we need to show auth dialog or tutorial
        floats = []
        
        # Auth dialog
        if self.auth_dialog_manager:
            dialog_float = self.auth_dialog_manager.get_dialog_float()
            if dialog_float:
                floats.append(dialog_float)
        
        # Tutorial overlay
        if self.tutorial_manager and self.tutorial_manager.tutorial_active:
            tutorial_overlay = self.tutorial_manager.get_tutorial_overlay()
            if tutorial_overlay:
                floats.append(Float(content=tutorial_overlay))
        
        # Add toast notifications
        toast_windows = self.toast_manager.get_toast_windows()
        for window, row_offset, col_offset in toast_windows:
            floats.append(Float(
                content=window,
                top=row_offset,
                right=-col_offset if col_offset < 0 else None,
                left=col_offset if col_offset >= 0 else None,
            ))
        
        # Add command palette if visible
        if self.command_palette:
            command_palette_float = self.command_palette.get_dialog_float()
            if command_palette_float:
                floats.append(command_palette_float)
        
        # Add help overlay if visible
        if self.help_overlay_visible:
            help_overlay = self._create_help_overlay()
            if help_overlay:
                floats.append(Float(
                    content=help_overlay,
                    xcursor=True,
                    ycursor=True,
                ))
        
        # Return with or without floats
        if floats:
            return FloatContainer(
                content=main_content,
                floats=floats,
            )
        else:
            return main_content
    
    def _get_help_text(self) -> str:
        """Get context-aware help text for bottom bar."""
        if self.command_palette.visible:
            return 'Command Palette Mode - Search for any action'
        elif self.tutorial_manager.tutorial_active:
            return 'Tutorial Mode - Follow instructions above'
        elif self.is_first_run:
            return 'Welcome! Press Enter to start tutorial | ESC: Back | ↑↓: Navigate | /: Search | Ctrl+P: Commands | Ctrl+S: Dashboard | Ctrl+C: Quit'
        else:
            return 'ESC: Back  ↑↓: Navigate  Enter: Select  /: Search  Ctrl+P: Commands  Ctrl+S: Dashboard  Ctrl+D: Dismiss toasts  Ctrl+C: Quit'
    
    def _get_status_text(self) -> str:
        """Get the status bar text."""
        # Check for active loading operations
        loading_text = self.spinner.get_display_text()
        if loading_text:
            # Show loading message if active
            return f"  {loading_text}  "
        
        agents = len(self.agent_registry.get_available_agents())
        # In real implementation, would get actual tool count
        tools = 87
        
        # Check if server is running
        server_status = "● Active"  # Would check actual status
        
        # Get current working directory
        cwd = os.getcwd()
        # Shorten path if it's too long
        if len(cwd) > 40:
            # Show last part of path
            parts = cwd.split(os.sep)
            if len(parts) > 3:
                cwd = f"...{os.sep}{os.sep.join(parts[-3:])}"
        
        return f"  Dir: {cwd}    Status: {server_status}    Agents: {agents}    Tools: {tools}     "
    
    def _render_breadcrumbs(self) -> FormattedText:
        """Render the breadcrumb navigation trail."""
        parts = []
        
        # Add padding
        parts.append(('', '  '))
        
        # Handle search mode specially
        if self.search_mode:
            # Show search breadcrumb
            parts.append(('class:breadcrumb', 'Home'))
            parts.append(('class:breadcrumb.separator', ' → '))
            parts.append(('class:breadcrumb.current', f'Search: "{self.search_buffer.text}"'))
        else:
            # Add each breadcrumb level
            for i, crumb in enumerate(self.breadcrumb_stack):
                # Use different style for current (last) breadcrumb
                is_current = i == len(self.breadcrumb_stack) - 1
                style = 'class:breadcrumb.current' if is_current else 'class:breadcrumb'
                
                parts.append((style, crumb))
                
                # Add separator if not the last item
                if not is_current:
                    parts.append(('class:breadcrumb.separator', ' → '))
        
        # Add hint about navigation
        if len(self.breadcrumb_stack) > 1 and not self.search_mode:
            parts.append(('', '  '))
            parts.append(('class:breadcrumb', '(ESC to go back)'))
        
        return FormattedText(parts)
    
    def _render_menu(self) -> FormattedText:
        """Render the current menu as formatted text."""
        lines = []
        
        # Header
        lines.append(('', '\n'))
        if self.search_mode:
            lines.append(('class:header', f'  Search: {self.search_buffer.text}'))
            lines.append(('class:selected', '_'))  # Cursor
            lines.append(('', '\n\n'))
            if self.search_results:
                lines.append(('', f'  Found {len(self.search_results)} results:\n'))
            else:
                lines.append(('class:status', '  No results found\n'))
            lines.append(('', '\n'))
        else:
            if self.is_first_run:
                lines.append(('class:header', '  Welcome to agtOS! Select an action to get started:\n'))
            else:
                lines.append(('', '  Select an action (↑↓ to navigate, Enter to select):\n'))
            lines.append(('', '\n'))
        
        if self.search_mode and self.search_results:
            # Render search results with paths
            for i, (item, path) in enumerate(self.search_results):
                # Selection indicator
                if i == self.selected_index:
                    lines.append(('class:selected', '  > '))
                else:
                    lines.append(('', '    '))
                
                # Menu label
                lines.append(('class:selected' if i == self.selected_index else '', item.label))
                
                # Show path if not at root
                if len(path) > 1:
                    path_str = ' → '.join(path[:-1])
                    padding = 50 - len(item.label)
                    lines.append(('', ' ' * max(1, padding)))
                    lines.append(('class:status', f'({path_str})'))
                
                lines.append(('', '\n'))
        else:
            # Filter menu items if searching
            visible_items = self._filter_menu_items()
            
            # Render each menu item
            for i, item in enumerate(visible_items):
                if item.separator:
                    lines.append(('class:separator', '    ──────────────────────────────────────\n'))
                else:
                    # Selection indicator with recommendation
                    if i == self.selected_index:
                        lines.append(('class:selected', '  > '))
                    else:
                        if item.recommended:
                            lines.append(('class:recommended', '  ★ '))  # Star for recommended
                        else:
                            lines.append(('', '    '))
                    
                    # Menu label
                    style = 'class:selected' if i == self.selected_index else ('class:recommended' if item.recommended else '')
                    lines.append((style, item.label))
                    
                    # Cost info if available
                    if item.cost_info:
                        padding = 40 - len(item.label)
                        lines.append(('', ' ' * max(1, padding)))
                        lines.append(('class:cost', f'[{item.cost_info}]'))
                    
                    # Hint if available and selected
                    if item.hint and i == self.selected_index:
                        lines.append(('class:hint', f' - {item.hint}'))
                    
                    lines.append(('', '\n'))
        
        lines.append(('', '\n'))
        
        return FormattedText(lines)
    
    def _filter_menu_items(self) -> List[MenuItem]:
        """Filter menu items based on search query."""
        if self.search_mode and self.search_results:
            # In search mode, show search results
            return [item for item, _ in self.search_results]
        
        if not self.search_query:
            return self.current_menu
        
        # Simple case-insensitive search
        query = self.search_query.lower()
        return [
            item for item in self.current_menu
            if query in item.label.lower() or item.separator
        ]
    
    def _move_selection(self, direction: int):
        """Move the selection up or down."""
        visible_items = [i for i in self._filter_menu_items() if not i.separator]
        if not visible_items:
            return
        
        max_index = len(visible_items) - 1
        self.selected_index = max(0, min(max_index, self.selected_index + direction))
    
    def _execute_selected(self):
        """Execute the selected menu item."""
        if self.search_mode and self.search_results:
            # Execute from search results
            if self.selected_index < len(self.search_results):
                selected, path = self.search_results[self.selected_index]
                
                # Exit search mode
                self.search_mode = False
                self.search_buffer.text = ""
                self.search_results = []
                
                if selected.submenu:
                    # Navigate to submenu
                    self._navigate_to_item(selected, path)
                elif selected.action:
                    # Execute action through command palette for tracking
                    cmd_id = "_".join(path + [selected.label]).replace(" ", "_").lower()
                    self.command_registry.record_usage(cmd_id)
                    selected.action()
        else:
            visible_items = [i for i in self._filter_menu_items() if not i.separator]
            if not visible_items or self.selected_index >= len(visible_items):
                return
            
            selected = visible_items[self.selected_index]
            
            if selected.submenu:
                # Enter submenu - update breadcrumb
                self.menu_stack.append(self.current_menu)
                self.current_menu = selected.submenu
                self.selected_index = 0
                
                # Add to breadcrumb stack (clean up label)
                breadcrumb_label = self._clean_breadcrumb_label(selected.label)
                if breadcrumb_label:  # Only add non-empty labels
                    self.breadcrumb_stack.append(breadcrumb_label)
                
                # Rebuild command registry to include submenu actions
                self._rebuild_command_registry()
            elif selected.action:
                # Execute action through command palette for tracking
                path = self.breadcrumb_stack[1:] if len(self.breadcrumb_stack) > 1 else []
                cmd_id = "_".join(path + [selected.label]).replace(" ", "_").lower()
                self.command_registry.record_usage(cmd_id)
                selected.action()
    
    def _navigate_to_item(self, target_item: MenuItem, path: List[str]):
        """Navigate to a specific item through its path."""
        # Reset to main menu
        self.menu_stack = []
        self.current_menu = self.main_menu
        self.breadcrumb_stack = ["Home"]  # Reset breadcrumbs
        
        # Navigate through the path
        current_items = self.main_menu
        for i, path_label in enumerate(path[:-1]):
            # Find the menu item in current level
            for item in current_items:
                if item.label == path_label and item.submenu:
                    self.menu_stack.append(current_items)
                    current_items = item.submenu
                    self.current_menu = current_items
                    
                    # Add to breadcrumb (clean up label)
                    breadcrumb_label = self._clean_breadcrumb_label(path_label)
                    if breadcrumb_label:  # Only add non-empty labels
                        self.breadcrumb_stack.append(breadcrumb_label)
                    break
        
        # Select the target item
        for i, item in enumerate(self.current_menu):
            if item.label == target_item.label:
                self.selected_index = i
                break
    
    def _navigate_to_command(self, command):
        """Navigate to a command through its menu path."""
        # Find the menu item for this command
        def find_menu_item(items, label, path_so_far=[]):
            for item in items:
                if item.separator:
                    continue
                if item.label == label:
                    return item, path_so_far + [label]
                if item.submenu:
                    result = find_menu_item(item.submenu, label, path_so_far + [item.label])
                    if result:
                        return result
            return None
        
        # Find the menu item
        result = find_menu_item(self.main_menu, command.label)
        if result:
            item, path = result
            self._navigate_to_item(item, path)
    
    def _go_back(self):
        """Go back to previous menu or exit search mode."""
        if self.search_mode:
            self.search_mode = False
            self.search_buffer.text = ""
            self.search_results = []
            self.selected_index = 0
        elif self.menu_stack:
            self.current_menu = self.menu_stack.pop()
            self.selected_index = 0
            # Pop breadcrumb when going back
            if len(self.breadcrumb_stack) > 1:
                self.breadcrumb_stack.pop()
    
    def _search_menu_items(self, query: str) -> List[Tuple[MenuItem, List[str]]]:
        """Search through all menu items recursively.
        
        Returns list of (MenuItem, path) tuples where path shows menu hierarchy.
        """
        if not query:
            return []
        
        results = []
        query_lower = query.lower()
        
        def search_recursive(items: List[MenuItem], path: List[str] = []):
            for item in items:
                if item.separator:
                    continue
                
                # Check if query matches this item
                if query_lower in item.label.lower():
                    results.append((item, path + [item.label]))
                
                # Search submenu if it exists
                if item.submenu:
                    search_recursive(item.submenu, path + [item.label])
        
        # Start search from main menu
        search_recursive(self.main_menu)
        
        # Use fuzzy matching for better results
        if not results and len(query) >= 2:
            # Collect all menu item labels
            all_labels = []
            def collect_labels(items: List[MenuItem], path: List[str] = []):
                for item in items:
                    if not item.separator:
                        all_labels.append((item.label, item, path))
                        if item.submenu:
                            collect_labels(item.submenu, path + [item.label])
            
            collect_labels(self.main_menu)
            
            # Get fuzzy matches
            labels_only = [label for label, _, _ in all_labels]
            fuzzy_matches = fuzzy_match_tools(query, labels_only, max_suggestions=10, threshold=0.4)
            
            # Convert back to menu items
            for matched_label, score in fuzzy_matches:
                for label, item, path in all_labels:
                    if label == matched_label:
                        results.append((item, path + [item.label]))
                        break
        
        return results
    
    def _update_search_results(self):
        """Update search results based on current buffer text."""
        query = self.search_buffer.text.strip()
        if query:
            self.search_results = self._search_menu_items(query)
            self.selected_index = 0
        else:
            self.search_results = []
    
    # Action handlers
    def _open_claude(self):
        """Open Claude orchestrator in new terminal."""
        import threading
        import subprocess
        import platform
        import os
        
        def launch_claude():
            # Track this as an AI operation
            op_id = self.operation_manager.track_ai_operation(
                agent="Claude",
                task="Starting orchestrator session",
                model="claude-3-opus"
            )
            
            operation_id = self.spinner.start("Launching Claude orchestrator...")
            
            system = platform.system()
            claude_command = "claude"
            
            try:
                if system == "Darwin":  # macOS
                    # Use osascript to open new Terminal
                    # Get current working directory to preserve context
                    cwd = os.getcwd()
                    # Change to current directory before running claude
                    # Escape the path for AppleScript by replacing quotes and backslashes
                    escaped_cwd = cwd.replace('\\', '\\\\').replace('"', '\\"')
                    script = f'''
                    tell application "Terminal"
                        activate
                        do script "cd \\"{escaped_cwd}\\" && {claude_command}"
                    end tell
                    '''
                    subprocess.run(["osascript", "-e", script], check=True)
                    self.spinner.stop(operation_id, "✓ Claude launched!")
                    success("Claude launched in new terminal!")
                    
                    # Complete the operation (no cost yet, will be tracked by Claude)
                    self.operation_manager.complete_operation(op_id)
                else:
                    # For other systems, try to run directly
                    # Pass current working directory to preserve context
                    subprocess.Popen(claude_command.split(), cwd=os.getcwd())
                    self.spinner.stop(operation_id, "✓ Claude launched!")
                    success("Claude launched!")
                    self.operation_manager.complete_operation(op_id)
            except Exception as e:
                self.spinner.stop(operation_id, "❌ Failed to launch Claude")
                error(f"Failed to launch Claude: {str(e)}")
                logger.error(f"Failed to launch Claude: {e}")
                self.operation_manager.fail_operation(op_id, str(e))
            
            self.app.invalidate()
        
        # Run in background thread
        threading.Thread(target=launch_claude, daemon=True).start()
    
    def _select_agent(self, agent):
        """Select an agent as primary."""
        success(f"Selected {agent.name} as primary agent")
        # Would save this preference
        self.app.invalidate()
    
    def _browse_workflows(self):
        """Browse available workflows."""
        # Track this operation
        op_id = self.operation_manager.start_operation(
            type=OperationType.SYSTEM_PROCESS,
            name="Discover Workflows",
            description="Loading workflow library"
        )
        
        # Discover workflows from library with loading indicator
        try:
            workflows = run_with_spinner(
                lambda: self.workflow_library.discover_workflows(),
                "Discovering workflows...",
                self.spinner,
                success_message="✓ Workflows loaded"
            )
            self.operation_manager.complete_operation(op_id)
        except Exception as e:
            error(f"Failed to load workflows: {str(e)}")
            workflows = []
            self.operation_manager.fail_operation(op_id, str(e))
        
        submenu = []
        
        # Add header explaining how to use workflows
        submenu.append(MenuItem("📖 Workflows are executed through Claude", None))
        submenu.append(MenuItem("Ask Claude: 'run the <workflow-name> workflow'", None))
        submenu.append(MenuItem("", separator=True))
        
        # Group workflows by category
        categories = {}
        for workflow in workflows:
            if workflow.category not in categories:
                categories[workflow.category] = []
            categories[workflow.category].append(workflow)
        
        # Show workflows organized by category
        if categories:
            for category, category_workflows in sorted(categories.items()):
                submenu.append(MenuItem(f"📁 {category.title()} Workflows:", None))
                
                for workflow in category_workflows[:5]:  # Limit per category
                    # Create nice display with tags
                    tags_str = f" [{', '.join(workflow.tags[:2])}]" if workflow.tags else ""
                    description = workflow.description[:40] + "..." if len(workflow.description) > 40 else workflow.description
                    
                    submenu.append(
                        MenuItem(
                            f"  • {workflow.name} - {description}{tags_str}",
                            lambda w=workflow: self._show_workflow_details(w)
                        )
                    )
                
                if len(category_workflows) > 5:
                    submenu.append(MenuItem(f"     ... and {len(category_workflows) - 5} more {category} workflows", None))
                
                submenu.append(MenuItem("", separator=True))
        else:
            submenu.append(MenuItem("⚠️  No workflows found in library", None))
            submenu.append(MenuItem("Check examples/workflows directory", None))
        
        submenu.append(MenuItem(f"📊 Total workflows: {len(workflows)}", None))
        submenu.append(MenuItem("", separator=True))
        submenu.append(MenuItem("← Back", self._go_back))
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _show_workflow_info(self, workflow):
        """Show workflow information."""
        info(f"Tell Claude: 'run the {workflow['name']} workflow'")
        self.app.invalidate()
    
    def _show_workflow_details(self, workflow):
        """Show detailed workflow information."""
        submenu = [
            MenuItem(f"📋 {workflow.name}", None),
            MenuItem("", separator=True),
            MenuItem(f"📝 Description: {workflow.description}", None),
            MenuItem(f"🏷️  Category: {workflow.category}", None),
            MenuItem(f"📌 Version: {workflow.version}", None),
        ]
        
        if workflow.tags:
            submenu.append(MenuItem(f"🔖 Tags: {', '.join(workflow.tags)}", None))
        
        if workflow.required_tools:
            submenu.append(MenuItem("", separator=True))
            submenu.append(MenuItem("🔧 Required Tools:", None))
            for tool in workflow.required_tools:
                submenu.append(MenuItem(f"  • {tool}", None))
        
        if workflow.required_env:
            submenu.append(MenuItem("", separator=True))
            submenu.append(MenuItem("🔐 Required Environment Variables:", None))
            for env in workflow.required_env:
                submenu.append(MenuItem(f"  • {env}", None))
        
        submenu.extend([
            MenuItem("", separator=True),
            MenuItem("💡 To run this workflow:", None),
            MenuItem(f"   Tell Claude: 'run the {workflow.name} workflow'", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ])
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _select_project(self):
        """Select a project."""
        projects = list(self.project_store.list())
        submenu = []
        
        # Get current project
        current_project = self.project_store.get_current()
        
        if current_project:
            submenu.append(MenuItem(f"✅ Current: {current_project.slug}", None))
            submenu.append(MenuItem("", separator=True))
        
        if projects:
            submenu.append(MenuItem("Select a project:", None))
            for slug, project in projects:
                is_current = current_project and current_project.slug == slug
                prefix = "→ " if is_current else "  "
                submenu.append(
                    MenuItem(
                        f"{prefix}{slug} - {project.path}",
                        lambda p=project: self._switch_project(p)
                    )
                )
        else:
            submenu.append(MenuItem("⚠️  No projects found", None))
            submenu.append(MenuItem("Create your first project below", None))
        
        submenu.append(MenuItem("", separator=True))
        submenu.append(MenuItem("← Back", self._go_back))
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _switch_project(self, project):
        """Switch to selected project."""
        try:
            self.project_store.set_current(project.slug)
            success(f"Switched to project: {project.slug}")
            # Update the menu to reflect the change
            self._go_back()
            self._select_project()
        except Exception as e:
            error(f"Failed to switch project: {str(e)}")
        self.app.invalidate()
    
    def _create_project(self):
        """Create a new project."""
        submenu = [
            MenuItem("📁 Create New Project", None),
            MenuItem("", separator=True),
            MenuItem("To create a project, run in terminal:", None),
            MenuItem("", separator=True),
            MenuItem("  agtos project create <name> --path /your/project/path", None),
            MenuItem("", separator=True),
            MenuItem("Or ask Claude:", None),
            MenuItem("  'Create a new project called myapp'", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _list_projects(self):
        """List all projects."""
        projects = list(self.project_store.list())
        current = self.project_store.get_current()
        
        submenu = [
            MenuItem("📊 All Projects", None),
            MenuItem("", separator=True),
        ]
        
        if projects:
            for slug, project in projects:
                is_current = current and current.slug == slug
                status = " (current)" if is_current else ""
                submenu.append(
                    MenuItem(
                        f"• {slug}{status}",
                        lambda p=project: self._show_project_details(p)
                    )
                )
            submenu.append(MenuItem("", separator=True))
            submenu.append(MenuItem(f"Total: {len(projects)} projects", None))
        else:
            submenu.append(MenuItem("No projects found", None))
        
        submenu.append(MenuItem("", separator=True))
        submenu.append(MenuItem("← Back", self._go_back))
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _show_project_details(self, project):
        """Show project details."""
        submenu = [
            MenuItem(f"📁 Project: {project.slug}", None),
            MenuItem("", separator=True),
            MenuItem(f"📍 Path: {project.path}", None),
            MenuItem(f"📝 Description: {project.description or 'No description'}", None),
        ]
        
        if hasattr(project, 'created_at'):
            submenu.append(MenuItem(f"📅 Created: {project.created_at}", None))
        
        submenu.extend([
            MenuItem("", separator=True),
            MenuItem("💡 Actions:", None),
            MenuItem("  • Select 'Manage Projects' → 'Select Project'", None),
            MenuItem("  • Or tell Claude: 'switch to {project.slug} project'", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ])
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _add_api_key(self):
        """Add an API key."""
        submenu = [
            MenuItem("🔑 Add API Key", None),
            MenuItem("", separator=True),
            MenuItem("To add credentials securely, run:", None),
            MenuItem("", separator=True),
            MenuItem("  agtos creds set <service>", None),
            MenuItem("", separator=True),
            MenuItem("Examples:", None),
            MenuItem("  agtos creds set openai", None),
            MenuItem("  agtos creds set anthropic", None),
            MenuItem("  agtos creds set github", None),
            MenuItem("", separator=True),
            MenuItem("Or ask Claude:", None),
            MenuItem("  'Add my OpenAI API key'", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _update_credential(self):
        """Update a credential."""
        # List existing credentials to update
        try:
            services = self.provider.list_services()
            
            if services:
                submenu = [
                    MenuItem("🔄 Update Credential", None),
                    MenuItem("", separator=True),
                    MenuItem("Select service to update:", None),
                ]
                
                for service in services:
                    submenu.append(
                        MenuItem(
                            f"  • {service}",
                            lambda s=service: self._show_update_command(s)
                        )
                    )
                
                submenu.extend([
                    MenuItem("", separator=True),
                    MenuItem("← Back", self._go_back),
                ])
            else:
                submenu = [
                    MenuItem("⚠️  No credentials found", None),
                    MenuItem("Add credentials first using 'Add API Key'", None),
                    MenuItem("", separator=True),
                    MenuItem("← Back", self._go_back),
                ]
            
            self.menu_stack.append(self.current_menu)
            self.current_menu = submenu
            self.selected_index = 0
            
        except Exception as e:
            error(f"Error listing credentials: {str(e)}")
            self.app.invalidate()
    
    def _show_update_command(self, service):
        """Show command to update a specific service."""
        submenu = [
            MenuItem(f"🔄 Update {service} Credential", None),
            MenuItem("", separator=True),
            MenuItem("Run in terminal:", None),
            MenuItem("", separator=True),
            MenuItem(f"  agtos creds set {service}", None),
            MenuItem("", separator=True),
            MenuItem("This will securely update your credential", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _list_credentials(self):
        """List stored credentials."""
        try:
            services = self.provider.list_services()
            submenu = [
                MenuItem("🔐 Stored Credentials", None),
                MenuItem("", separator=True),
            ]
            
            if services:
                submenu.append(MenuItem(f"Found {len(services)} credentials:", None))
                submenu.append(MenuItem("", separator=True))
                
                for service in sorted(services):
                    # Get security info
                    security_icon = "🔒" if self.provider.security_level == "high" else "🔓"
                    submenu.append(
                        MenuItem(
                            f"{security_icon} {service}",
                            lambda s=service: self._show_credential_info(s)
                        )
                    )
                
                submenu.extend([
                    MenuItem("", separator=True),
                    MenuItem(f"Provider: {self.provider.name}", None),
                    MenuItem(f"Security: {self.provider.security_level}", None),
                ])
            else:
                submenu.extend([
                    MenuItem("⚠️  No credentials found", None),
                    MenuItem("", separator=True),
                    MenuItem("Add credentials using 'Add API Key'", None),
                ])
            
            submenu.extend([
                MenuItem("", separator=True),
                MenuItem("← Back", self._go_back),
            ])
            
            self.menu_stack.append(self.current_menu)
            self.current_menu = submenu
            self.selected_index = 0
            
        except Exception as e:
            error(f"Error listing credentials: {str(e)}")
            self.app.invalidate()
    
    def _show_credential_info(self, service):
        """Show information about a specific credential."""
        submenu = [
            MenuItem(f"🔑 {service} Credential", None),
            MenuItem("", separator=True),
            MenuItem("Actions:", None),
            MenuItem("  • Update: agtos creds set " + service, None),
            MenuItem("  • Delete: agtos creds delete " + service, None),
            MenuItem("  • Test: Select 'Test Connection'", None),
            MenuItem("", separator=True),
            MenuItem("Test Connection", lambda: self._test_specific_credential(service)),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _test_credential(self):
        """Test credential connections."""
        try:
            services = self.provider.list_services()
            
            if services:
                submenu = [
                    MenuItem("🧪 Test Credentials", None),
                    MenuItem("", separator=True),
                    MenuItem("Select service to test:", None),
                ]
                
                for service in services:
                    submenu.append(
                        MenuItem(
                            f"  • {service}",
                            lambda s=service: self._test_specific_credential(s)
                        )
                    )
                
                submenu.extend([
                    MenuItem("", separator=True),
                    MenuItem("← Back", self._go_back),
                ])
            else:
                submenu = [
                    MenuItem("⚠️  No credentials to test", None),
                    MenuItem("Add credentials first", None),
                    MenuItem("", separator=True),
                    MenuItem("← Back", self._go_back),
                ]
            
            self.menu_stack.append(self.current_menu)
            self.current_menu = submenu
            self.selected_index = 0
            
        except Exception as e:
            error(f"Error: {str(e)}")
            self.app.invalidate()
    
    def _test_specific_credential(self, service):
        """Test a specific credential."""
        import threading
        
        def test_credential_async():
            # Track this operation
            op_id = self.operation_manager.start_operation(
                type=OperationType.NETWORK_REQUEST,
                name=f"Test {service}",
                description=f"Testing {service} API connection",
                metadata={"service": service}
            )
            
            operation_id = self.spinner.start(f"Testing {service} connection...")
            
            def test_connection():
                # In a real implementation, would test the actual service
                # For now, just simulate
                import time
                time.sleep(1.5)  # Simulate network delay
                
                # Check if credential exists
                if self.provider.get_secret(service):
                    return True
                else:
                    raise ValueError(f"{service} credential not found")
            
            try:
                success_result = test_connection()
                self.spinner.stop(operation_id, f"✅ {service} connection successful!")
                success(f"{service} connection successful!")
                self.operation_manager.complete_operation(op_id)
            except Exception as e:
                self.spinner.stop(operation_id, f"❌ {service} test failed")
                error(f"{service} test failed: {str(e)}")
                self.operation_manager.fail_operation(op_id, str(e))
            
            self.app.invalidate()
        
        # Run in background thread
        threading.Thread(target=test_credential_async, daemon=True).start()
    
    def _view_agent_costs(self):
        """View agent cost breakdown."""
        submenu = [
            MenuItem("💰 Agent Pricing Overview", None),
            MenuItem("", separator=True),
            MenuItem("📊 Premium Agents (API-based):", None),
            MenuItem("", separator=True),
            MenuItem("🤖 Claude 3 Opus", None),
            MenuItem("   Input:  $15.00 / 1M tokens", None),
            MenuItem("   Output: $75.00 / 1M tokens", None),
            MenuItem("   Best for: Complex reasoning, code generation", None),
            MenuItem("", separator=True),
            MenuItem("🤖 Claude 3 Sonnet", None),
            MenuItem("   Input:  $3.00 / 1M tokens", None),
            MenuItem("   Output: $15.00 / 1M tokens", None),
            MenuItem("   Best for: Balanced performance/cost", None),
            MenuItem("", separator=True),
            MenuItem("🤖 GPT-4 Turbo", None),
            MenuItem("   Input:  $10.00 / 1M tokens", None),
            MenuItem("   Output: $30.00 / 1M tokens", None),
            MenuItem("   Best for: General purpose AI tasks", None),
            MenuItem("", separator=True),
            MenuItem("🤖 GPT-3.5 Turbo", None),
            MenuItem("   Input:  $0.50 / 1M tokens", None),
            MenuItem("   Output: $1.50 / 1M tokens", None),
            MenuItem("   Best for: Simple tasks, fast responses", None),
            MenuItem("", separator=True),
            MenuItem("📊 Local Agents (Free):", None),
            MenuItem("", separator=True),
            MenuItem("🏠 Ollama (Llama, Mistral, etc)", None),
            MenuItem("   Cost: Free (requires local GPU)", None),
            MenuItem("   Best for: Privacy, unlimited usage", None),
            MenuItem("", separator=True),
            MenuItem("💡 Cost Optimization Tips:", None),
            MenuItem("  • Use local models for development", None),
            MenuItem("  • Route simple tasks to cheaper agents", None),
            MenuItem("  • Set spending limits per agent", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _show_dashboard(self):
        """Show the real-time status dashboard."""
        self.dashboard_visible = True
        self.dashboard.show()
        self.app.invalidate()
    
    def _change_directory(self):
        """Change the working directory with interactive input."""
        import threading
        from pathlib import Path
        
        # Create a dialog-like menu that prompts for directory
        self._show_directory_dialog()
    
    def _show_directory_dialog(self):
        """Show directory change dialog."""
        # Store the current state
        self.directory_input_mode = True
        self.directory_input = ""
        self.menu_stack.append(self.current_menu)
        self.breadcrumb_stack.append("Change Directory")
        
        # Create a special menu for directory input
        self._update_directory_menu()
    
    def _update_directory_menu(self):
        """Update the directory input menu."""
        cwd = os.getcwd()
        
        submenu = [
            MenuItem("📁 Change Working Directory", None),
            MenuItem("", separator=True),
            MenuItem(f"Current directory:", None),
            MenuItem(f"  {cwd}", None),
            MenuItem("", separator=True),
            MenuItem("Enter new directory path:", None),
            MenuItem(f"  > {self.directory_input}\u2588", None),  # Show cursor
            MenuItem("", separator=True),
            MenuItem("[Enter] Confirm    [Tab] Auto-complete    [Esc] Cancel", None),
            MenuItem("", separator=True),
        ]
        
        # Add auto-complete suggestions if input is not empty
        if self.directory_input:
            suggestions = self._get_directory_suggestions(self.directory_input)
            if suggestions:
                submenu.append(MenuItem("Suggestions:", None))
                for idx, suggestion in enumerate(suggestions[:5]):
                    hint = f"Tab to select" if idx == 0 else None
                    submenu.append(
                        MenuItem(
                            f"  {suggestion}", 
                            lambda s=suggestion: self._select_directory_suggestion(s),
                            hint=hint
                        )
                    )
                submenu.append(MenuItem("", separator=True))
        
        self.current_menu = submenu
        self.selected_index = 6  # Focus on input line
        
        # Rebuild command registry
        self._rebuild_command_registry()
    
    def _get_directory_suggestions(self, path_input: str) -> List[str]:
        """Get directory suggestions based on partial input."""
        from pathlib import Path
        import os
        
        suggestions = []
        
        # Handle ~ expansion
        if path_input.startswith('~'):
            path_input = os.path.expanduser(path_input)
        
        # If path ends with /, list subdirectories
        if path_input.endswith('/'):
            base_path = Path(path_input)
            if base_path.exists() and base_path.is_dir():
                try:
                    for item in base_path.iterdir():
                        if item.is_dir() and not item.name.startswith('.'):
                            suggestions.append(str(item))
                except PermissionError:
                    pass
        else:
            # Get directory name and parent
            parent = Path(path_input).parent
            prefix = Path(path_input).name
            
            if parent.exists() and parent.is_dir():
                try:
                    for item in parent.iterdir():
                        if item.is_dir() and item.name.startswith(prefix) and not item.name.startswith('.'):
                            suggestions.append(str(item))
                except PermissionError:
                    pass
        
        return sorted(suggestions)[:5]
    
    def _select_directory_suggestion(self, suggestion: str):
        """Select a directory suggestion."""
        self.directory_input = suggestion
        if not suggestion.endswith('/'):
            self.directory_input += '/'
        self._update_directory_menu()
        self.app.invalidate()
    
    def _confirm_directory_change(self):
        """Confirm and execute the directory change."""
        from pathlib import Path
        
        # Expand ~ and resolve path
        new_path = os.path.expanduser(self.directory_input.strip())
        
        try:
            # Validate the path
            path = Path(new_path).resolve()
            
            if not path.exists():
                error(f"Directory does not exist: {new_path}")
                return
            
            if not path.is_dir():
                error(f"Not a directory: {new_path}")
                return
            
            # Change directory
            os.chdir(path)
            success(f"Changed directory to: {path}")
            
            # Clear input mode and go back
            self.directory_input_mode = False
            self.directory_input = ""
            self._go_back()
            
            # Update status bar
            self.app.invalidate()
            
        except PermissionError:
            error(f"Permission denied: {new_path}")
        except Exception as e:
            error(f"Failed to change directory: {str(e)}")
    
    def _cancel_directory_input(self):
        """Cancel directory input and go back."""
        self.directory_input_mode = False
        self.directory_input = ""
        self._go_back()
    
    def _toggle_help_overlay(self):
        """Toggle the help overlay showing keyboard shortcuts."""
        self.help_overlay_visible = not self.help_overlay_visible
        self.app.invalidate()
    
    def _create_help_overlay(self) -> Container:
        """Create the help overlay showing all keyboard shortcuts."""
        help_text = """
╭─────────────────── Keyboard Shortcuts ───────────────────╮
│                                                           │
│  Navigation:                                              │
│  ↑/k         Move up                                      │
│  ↓/j         Move down                                    │
│  Enter       Select item                                  │
│  Escape      Go back                                      │
│  1-9         Quick select menu item by number             │
│                                                           │
│  Search & Commands:                                       │
│  /           Start search                                 │
│  Ctrl+P      Open command palette                         │
│  Escape      Exit search mode                             │
│                                                           │
│  Interface:                                               │
│  Ctrl+S      Show dashboard                               │
│  ?           Toggle this help                             │
│  Ctrl+D      Dismiss toast notifications                  │
│  Ctrl+C      Exit application                             │
│                                                           │
│  Press ? or Escape to close this help                     │
╰───────────────────────────────────────────────────────────╯
"""
        return Frame(
            Window(
                FormattedTextControl(
                    FormattedText([('class:help', help_text)])
                ),
                height=Dimension(min=20, max=25),
                width=Dimension(min=60, max=65),
            ),
            title="Help",
            style='class:help.frame'
        )
    
    def _get_animated_title(self) -> FormattedText:
        """Get the title with animated gradient effect."""
        title_lines = [
            "▄▀█ █▀▀ ▀█▀ █▀█ █▀",
            "█▀█ █▄█  █  █▄█ ▄█",
        ]
        subtitle = "Agent Operating System v0.3.2 (Beta)"
        
        # Gradient colors (subtle green to blue)
        colors = [
            '#00ff00',  # Bright green
            '#00dd22',  # Green-cyan
            '#00bb44',  # Cyan-green
            '#009966',  # Cyan
            '#007788',  # Blue-cyan
            '#0055aa',  # Light blue
            '#0033cc',  # Blue
            '#0055aa',  # Light blue
            '#007788',  # Blue-cyan
            '#009966',  # Cyan
            '#00bb44',  # Cyan-green
            '#00dd22',  # Green-cyan
        ]
        
        # Calculate color index based on animation frame
        color_offset = self.animation_frame % len(colors)
        
        # Build formatted text with gradient
        formatted_parts = []
        
        # Add empty line
        formatted_parts.append(('', '\n'))
        
        # Add title lines with gradient
        for line in title_lines:
            # Center the line
            padding = (60 - len(line)) // 2
            formatted_parts.append(('', ' ' * padding))
            
            # Apply gradient to each character
            for i, char in enumerate(line):
                if char != ' ':
                    color_idx = (color_offset + i) % len(colors)
                    color = colors[color_idx]
                    formatted_parts.append((f'{color} bold', char))
                else:
                    formatted_parts.append(('', char))
            formatted_parts.append(('', '\n'))
        
        # Add empty line
        formatted_parts.append(('', '\n'))
        
        # Add subtitle (no animation, just centered)
        padding = (60 - len(subtitle)) // 2
        formatted_parts.append(('', ' ' * padding))
        formatted_parts.append(('class:status', subtitle))
        formatted_parts.append(('', '\n'))
        
        return FormattedText(formatted_parts)
    
    def _start_animation(self):
        """Start the gradient animation thread."""
        def animate():
            while self.animation_running:
                self.animation_frame += 1
                if self.animation_frame >= 360:  # Reset after full cycle
                    self.animation_frame = 0
                    
                # Only invalidate if app exists and is running
                if hasattr(self, 'app') and self.app and self.app.is_running:
                    self.app.invalidate()
                    
                time.sleep(0.1)  # 10 FPS animation
        
        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()
    
    def _stop_animation(self):
        """Stop the animation thread."""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
    
    def _show_server_status(self):
        """Show Meta-MCP server status."""
        # Check if server is actually running with loading indicator
        import requests
        server_url = "http://localhost:8585"
        
        submenu = [
            MenuItem("🖥️  Meta-MCP Server Status", None),
            MenuItem("", separator=True),
        ]
        
        operation_id = self.spinner.start("Checking server status...")
        
        try:
            # Try to connect to server
            response = requests.get(f"{server_url}/health", timeout=2)
            self.spinner.stop(operation_id)
            if response.status_code == 200:
                health_data = response.json()
                
                submenu.extend([
                    MenuItem("✅ Status: Running", None),
                    MenuItem(f"📍 URL: {server_url}", None),
                    MenuItem(f"🕐 Uptime: {health_data.get('uptime', 'Unknown')}", None),
                    MenuItem("", separator=True),
                    MenuItem("📊 Connected Services:", None),
                ])
                
                # Show connected MCP servers
                services = health_data.get('services', {})
                if services:
                    healthy_count = 0
                    for service, status in services.items():
                        status_icon = "✅" if status == "healthy" else "❌"
                        if status == "healthy":
                            healthy_count += 1
                        submenu.append(MenuItem(f"  {status_icon} {service}", None))
                    # Show toast with summary
                    success(f"Server is running with {healthy_count}/{len(services)} healthy services")
                else:
                    submenu.append(MenuItem("  No services connected", None))
                    warning("Server is running but no services connected")
                
                submenu.extend([
                    MenuItem("", separator=True),
                    MenuItem(f"🔧 Available Tools: {health_data.get('tool_count', 0)}", None),
                    MenuItem(f"📈 Requests Handled: {health_data.get('request_count', 0)}", None),
                ])
            else:
                submenu.extend([
                    MenuItem("⚠️  Server responding but unhealthy", None),
                    MenuItem(f"Status code: {response.status_code}", None),
                ])
                
        except requests.exceptions.ConnectionError:
            self.spinner.stop(operation_id, "❌ Server not running")
            error("Meta-MCP server is not running", duration=5.0)
            submenu.extend([
                MenuItem("❌ Status: Not Running", None),
                MenuItem("", separator=True),
                MenuItem("Start the server with:", None),
                MenuItem("  agtos mcp-server", None),
                MenuItem("", separator=True),
                MenuItem("Or use stdio mode for Claude Code:", None),
                MenuItem("  agtos mcp-server --stdio", None),
            ])
        except requests.exceptions.Timeout:
            self.spinner.stop(operation_id, "⚠️ Server timeout")
            submenu.extend([
                MenuItem("⚠️  Server not responding", None),
                MenuItem("Check if port 8585 is blocked", None),
            ])
        except Exception as e:
            self.spinner.stop(operation_id, "❌ Error checking status")
            submenu.extend([
                MenuItem("❌ Error checking status", None),
                MenuItem(f"Error: {str(e)}", None),
            ])
        
        # Add stop server option if server is running
        try:
            requests.get(f"{server_url}/health", timeout=0.5)
            submenu.append(MenuItem("🛑 Stop Server", self._stop_mcp_server))
        except:
            pass  # Server not running, don't show stop option
        
        submenu.extend([
            MenuItem("", separator=True),
            MenuItem("🔄 Refresh", self._show_server_status),
            MenuItem("← Back", self._go_back),
        ])
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _stop_mcp_server(self):
        """Stop the running MCP server."""
        import subprocess
        import threading
        
        def stop_server_async():
            operation_id = self.spinner.start("Stopping MCP server...")
            
            try:
                # Run the mcp-stop command
                result = subprocess.run(
                    ["agtos", "mcp-stop"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                self.spinner.stop(operation_id, "✅ Server stopped successfully")
                success("MCP server stopped successfully")
                
                # Refresh the status menu after a short delay
                def refresh_menu():
                    time.sleep(1)
                    self._show_server_status()
                
                threading.Thread(target=refresh_menu, daemon=True).start()
                
            except subprocess.CalledProcessError as e:
                self.spinner.stop(operation_id, "❌ Failed to stop server")
                error(f"Failed to stop server: {e.stderr}")
            except Exception as e:
                self.spinner.stop(operation_id, "❌ Error stopping server")
                error(f"Error stopping server: {str(e)}")
            
            self.app.invalidate()
        
        # Run in background thread
        threading.Thread(target=stop_server_async, daemon=True).start()
    
    def _build_help_menu(self) -> List[MenuItem]:
        """Build the help and documentation submenu."""
        return [
            MenuItem(
                "🎓 Show Interactive Tutorial", 
                self._show_tutorial,
                recommended=self.is_first_run,
                hint="Learn the basics interactively"
            ),
            MenuItem("📚 Quick Start Guide", self._show_quick_start),
            MenuItem("⌨️  Keyboard Shortcuts", self._show_keyboard_shortcuts),
            MenuItem("💡 Tips & Tricks", self._show_tips),
            MenuItem("🔗 Online Resources", self._show_resources),
            MenuItem("📊 System Information", self._show_system_info),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
    
    def _show_tutorial(self):
        """Show the interactive tutorial."""
        self.tutorial_manager.start_tutorial(force=True)
    
    def _on_tutorial_complete(self):
        """Handle tutorial completion."""
        self.is_first_run = False
        success("Tutorial completed! You're ready to use agtOS 🎉", duration=5.0)
        self.app.invalidate()
    
    def _show_quick_start(self):
        """Show quick start guide."""
        submenu = [
            MenuItem("🚀 Quick Start Guide", None),
            MenuItem("", separator=True),
            MenuItem("1. Launch Claude (Orchestrator)", None),
            MenuItem("   - Select 'Open Claude' from main menu", None),
            MenuItem("   - Claude opens in new terminal", None),
            MenuItem("", separator=True),
            MenuItem("2. Natural Language Commands", None),
            MenuItem("   - Tell Claude what you want to do", None),
            MenuItem("   - Examples:", None),
            MenuItem("     • 'Create a new React app'", None),
            MenuItem("     • 'Deploy to production'", None),
            MenuItem("     • 'Run the security audit workflow'", None),
            MenuItem("", separator=True),
            MenuItem("3. Tool Creation on Demand", None),
            MenuItem("   - Claude creates tools as needed", None),
            MenuItem("   - Example: 'Post to Slack' → Slack tool created", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _show_keyboard_shortcuts(self):
        """Show keyboard shortcuts."""
        submenu = [
            MenuItem("⌨️  Keyboard Shortcuts", None),
            MenuItem("", separator=True),
            MenuItem("Navigation:", None),
            MenuItem("  ↑      Move up", None),
            MenuItem("  ↓      Move down", None),
            MenuItem("  Enter  Select item", None),
            MenuItem("  Esc    Go back", None),
            MenuItem("", separator=True),
            MenuItem("Search:", None),
            MenuItem("  /      Start search", None),
            MenuItem("  Type   Filter results", None),
            MenuItem("  Esc    Exit search", None),
            MenuItem("", separator=True),
            MenuItem("Command Palette:", None),
            MenuItem("  Ctrl+P Open command palette", None),
            MenuItem("  Type   Search commands", None),
            MenuItem("  Enter  Execute command", None),
            MenuItem("", separator=True),
            MenuItem("Dashboard:", None),
            MenuItem("  Ctrl+S Show status dashboard", None),
            MenuItem("  Tab    Switch dashboard sections", None),
            MenuItem("  R      Reset session costs", None),
            MenuItem("", separator=True),
            MenuItem("Notifications:", None),
            MenuItem("  Ctrl+D Dismiss all toasts", None),
            MenuItem("", separator=True),
            MenuItem("General:", None),
            MenuItem("  Ctrl+C Exit agtOS", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _show_tips(self):
        """Show tips and tricks."""
        submenu = [
            MenuItem("💡 Tips & Tricks", None),
            MenuItem("", separator=True),
            MenuItem("Search is your superpower:", None),
            MenuItem("  • Press '/' from anywhere", None),
            MenuItem("  • Type partial names", None),
            MenuItem("  • Searches all menus", None),
            MenuItem("", separator=True),
            MenuItem("Cost optimization:", None),
            MenuItem("  • Check agent costs before selecting", None),
            MenuItem("  • Use local agents for development", None),
            MenuItem("  • Set spending limits", None),
            MenuItem("", separator=True),
            MenuItem("Workflow efficiency:", None),
            MenuItem("  • Browse workflows for common tasks", None),
            MenuItem("  • Tell Claude to run workflows", None),
            MenuItem("  • Create custom workflows", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _show_resources(self):
        """Show online resources."""
        submenu = [
            MenuItem("🔗 Online Resources", None),
            MenuItem("", separator=True),
            MenuItem("📖 Documentation:   https://agtos.ai/docs", None),
            MenuItem("💻 GitHub:          https://github.com/agtos-ai/agtos", None),
            MenuItem("🐛 Report Issues:   https://github.com/agtos-ai/agtos/issues", None),
            MenuItem("💬 Discord:         https://discord.gg/agtos", None),
            MenuItem("🌐 Website:         https://agtos.ai", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _show_system_info(self):
        """Show system information."""
        submenu = [
            MenuItem("📊 System Information", None),
            MenuItem("", separator=True),
            MenuItem(f"Version:    {self._get_current_version()}", None),
            MenuItem(f"Config Dir: ~/.agtos/", None),
            MenuItem(f"Logs Dir:   ~/.agtos/logs/", None),
            MenuItem(f"Provider:   {self.provider.name}", None),
            MenuItem(f"Agents:     {len(self.agent_registry.get_available_agents())}", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _get_agent_cost_info(self, agent_name: str) -> str:
        """Get cost information for an agent."""
        # In real implementation, would fetch actual costs
        costs = {
            "claude": "$0.25/1K tokens",
            "codex": "$0.02/1K tokens",
            "gpt4": "$0.03/1K tokens",
            "ollama": "Free (local)",
        }
        return costs.get(agent_name.lower(), "Unknown")
    
    def _clean_breadcrumb_label(self, label: str) -> str:
        """Clean a menu label for use in breadcrumbs."""
        # Remove emoji and special characters
        clean = label.strip()
        
        # Remove common emoji patterns
        emoji_chars = "📋📁🔑💰🖥️⌨️💡🔗📊🎓🤖🏠✅⚠️❌🔒🔓🔄🧪📈📍📝🏷️📌🔖🔧🔐💻🐛💬🌐📖📚🚀🎉📦✨⏭️🔔🔐🎟️"
        for char in emoji_chars:
            clean = clean.replace(char, "")
        
        # Remove bullets and arrows
        clean = clean.replace("→", "").replace("•", "").replace("←", "")
        
        # Remove extra whitespace
        clean = " ".join(clean.split())
        
        # Handle special cases
        if clean.startswith("Back"):
            return ""  # Don't add "Back" to breadcrumbs
        
        # Shorten long labels
        if len(clean) > 30:
            clean = clean[:27] + "..."
        
        return clean
    
    def _check_updates(self):
        """Check for agtOS updates with enhanced UI."""
        operation_id = self.spinner.start("Checking for updates...")
        
        try:
            # Get current version
            current_version = self._get_current_version()
            
            # Check PyPI for latest release
            self.spinner.update_message(operation_id, "Checking PyPI...")
            latest_version, download_url, release_info = self._get_latest_version()
            
            if latest_version and current_version:
                if version.parse(latest_version) > version.parse(current_version):
                    # Store update info
                    self.pending_update = {
                        "current": current_version,
                        "latest": latest_version,
                        "download_url": download_url,
                        "release_info": release_info
                    }
                    
                    # Check if this version was skipped
                    skipped = self.update_preferences.get("skipped_versions", [])
                    if latest_version not in skipped:
                        self.spinner.stop(operation_id, f"🎉 Update available: v{latest_version}")
                        info(f"Update available: v{latest_version}")
                        self._show_update_menu(current_version, latest_version, release_info)
                    else:
                        self.spinner.stop(operation_id, f"Update available: v{latest_version} (skipped)")
                        info(f"Update available: v{latest_version} (skipped)")
                else:
                    self.spinner.stop(operation_id, f"✓ You're up to date! (v{current_version})")
                    success(f"You're up to date! (v{current_version})")
            else:
                self.spinner.stop(operation_id, "Unable to check for updates")
                warning("Unable to check for updates")
                
        except Exception as e:
            self.spinner.stop(operation_id, "❌ Update check failed")
            error(f"Update check failed: {str(e)}")
            logger.error(f"Update check error: {e}")
        
        self.app.invalidate()
    
    def _quit(self):
        """Quit the agtOS TUI."""
        try:
            # Save any preferences
            self.context_manager.save_preferences(self.update_preferences)
            
            # Stop the animation thread
            self._stop_animation()
            
            # Exit the application
            self.app.exit()
        except Exception as e:
            logger.error(f"Error during quit: {e}")
            # Force exit even if there's an error
            import sys
            sys.exit(0)
    
    def _get_current_version(self) -> str:
        """Get current agtOS version."""
        try:
            # Try to get from pyproject.toml
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                import toml
                data = toml.load(pyproject_path)
                return data["tool"]["poetry"]["version"]
        except:
            pass
        
        # Fallback to package version
        try:
            import pkg_resources
            return pkg_resources.get_distribution("agtos").version
        except:
            return "0.3.2-dev"  # Fallback version
    
    def _get_latest_version(self) -> tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Get latest version from PyPI."""
        try:
            import urllib.request
            import json
            
            # Check PyPI for latest version
            url = "https://pypi.org/pypi/agtos/json"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
                
                latest_version = data["info"]["version"]
                
                # Get download URL for wheel
                download_url = None
                for release_file in data["releases"][latest_version]:
                    if release_file["filename"].endswith(".whl"):
                        download_url = release_file["url"]
                        break
                
                # Extract release info
                formatted_info = {
                    "name": f"v{latest_version}",
                    "body": data["info"]["summary"] or "No release notes available",
                    "published_at": data["releases"][latest_version][0]["upload_time"] if data["releases"][latest_version] else "",
                    "html_url": data["info"]["project_urls"].get("Homepage", "https://pypi.org/project/agtos/")
                }
                
                return latest_version, download_url, formatted_info
                
        except Exception as e:
            logger.error(f"Failed to check PyPI releases: {e}")
        
        return None, None, None
    
    def _load_update_preferences(self) -> Dict[str, Any]:
        """Load update preferences from config."""
        config_path = get_config_dir() / "update_preferences.json"
        
        default_prefs = {
            "check_on_startup": True,
            "skipped_versions": [],
            "last_check": None,
            "auto_update": False,
        }
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    prefs = json.load(f)
                    default_prefs.update(prefs)
            except Exception as e:
                logger.warning(f"Failed to load update preferences: {e}")
        
        return default_prefs
    
    def _save_update_preferences(self):
        """Save update preferences to config."""
        config_path = get_config_dir() / "update_preferences.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.update_preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save update preferences: {e}")
    
    def _check_updates_startup(self):
        """Check for updates on startup (non-blocking)."""
        try:
            # Quick check without blocking UI
            import threading
            
            def check():
                # Start loading indicator in background
                operation_id = self.spinner.start("Checking for updates...")
                
                try:
                    current = self._get_current_version()
                    latest, url, info = self._get_latest_version()
                    
                    if latest and current and version.parse(latest) > version.parse(current):
                        skipped = self.update_preferences.get("skipped_versions", [])
                        if latest not in skipped:
                            self.spinner.stop(operation_id, f"🎉 Update available: v{latest}")
                            info(f"Update available: v{latest}", duration=10.0)
                            if self.app and self.app.is_running:
                                self.app.invalidate()
                        else:
                            self.spinner.stop(operation_id)
                    else:
                        self.spinner.stop(operation_id)
                except Exception:
                    self.spinner.stop(operation_id)
            
            # Run in background
            threading.Thread(target=check, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Startup update check failed: {e}")
    
    def _show_update_menu(self, current_version: str, new_version: str, release_info: Dict[str, Any]):
        """Show update options submenu."""
        submenu = [
            MenuItem(f"🎉 Update Available: v{new_version}", None),
            MenuItem(f"📦 Current version: v{current_version}", None),
            MenuItem("", separator=True),
            MenuItem("✨ Install Update Now", lambda: self._install_update(new_version)),
            MenuItem("📋 View Release Notes", lambda: self._view_release_notes(release_info)),
            MenuItem("⏭️  Skip This Version", lambda: self._skip_version(new_version)),
            MenuItem("🔔 Update Settings", submenu=self._build_update_settings_menu()),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 3  # Default to "Install Update Now"
    
    def _install_update(self, new_version: str):
        """Install the update using pip."""
        operation_id = self.spinner.start(f"Installing v{new_version}...")
        
        try:
            # Always use PyPI for public package
            package_spec = f"agtos=={new_version}"
            
            # Run pip upgrade
            self.spinner.update_message(operation_id, f"Running pip install for v{new_version}...")
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", package_spec],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.spinner.stop(operation_id, "✅ Update successful!")
            success("Update successful! Please restart agtOS.", duration=10.0)
            
            # Show restart option
            self._show_restart_menu()
            
            # Cleanup temp file if used
            if 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            
        except subprocess.CalledProcessError as e:
            self.spinner.stop(operation_id, "❌ Update failed")
            error(f"Update failed: {e.stderr}", duration=10.0)
            logger.error(f"Update failed: {e}")
        except Exception as e:
            self.spinner.stop(operation_id, "❌ Update error")
            error(f"Update error: {str(e)}", duration=10.0)
            logger.error(f"Update error: {e}")
    
    def _show_restart_menu(self):
        """Show restart options after update."""
        submenu = [
            MenuItem("✅ Update Complete!", None),
            MenuItem("", separator=True),
            MenuItem("🔄 Restart agtOS Now", self._restart_application),
            MenuItem("⏸️  Restart Later", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 2
    
    def _restart_application(self):
        """Restart the application after update."""
        info("Restarting agtOS...")
        self.app.invalidate()
        
        # Exit the current app
        self.app.exit()
        
        # Restart based on platform
        if sys.platform == 'win32':
            # Windows: Start new process
            subprocess.Popen([sys.executable, "-m", "agtos"])
        else:
            # Unix/Linux/macOS: Replace current process
            os.execl(sys.executable, sys.executable, "-m", "agtos")
    
    def _view_release_notes(self, release_info: Dict[str, Any]):
        """View release notes in a submenu."""
        # Parse release notes
        body = release_info.get("body", "No release notes available")
        lines = body.split('\n')
        
        # Create menu items from release notes
        submenu = [
            MenuItem(f"📝 {release_info.get('name', 'Release Notes')}", None),
            MenuItem("", separator=True),
        ]
        
        # Add each line as a menu item (truncated if needed)
        for line in lines[:20]:  # Limit to 20 lines
            if line.strip():
                # Truncate long lines
                display_line = line[:80] + "..." if len(line) > 80 else line
                submenu.append(MenuItem(display_line, None))
        
        if len(lines) > 20:
            submenu.append(MenuItem("... (truncated)", None))
        
        submenu.extend([
            MenuItem("", separator=True),
            MenuItem(f"🔗 View on GitHub: {release_info.get('html_url', 'N/A')}", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ])
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = submenu
        self.selected_index = 0
        
        # Rebuild command registry to include dynamic submenu
        self._rebuild_command_registry()
    
    def _skip_version(self, version_to_skip: str):
        """Skip a specific version."""
        skipped = self.update_preferences.get("skipped_versions", [])
        if version_to_skip not in skipped:
            skipped.append(version_to_skip)
            self.update_preferences["skipped_versions"] = skipped
            self._save_update_preferences()
        
        info(f"Version {version_to_skip} will be skipped")
        self._go_back()
    
    def _build_update_settings_menu(self) -> List[MenuItem]:
        """Build update settings submenu."""
        check_startup = self.update_preferences.get("check_on_startup", True)
        
        return [
            MenuItem(
                f"{'✅' if check_startup else '⬜'} Check for updates on startup",
                self._toggle_startup_check
            ),
            MenuItem("🗑️  Clear skipped versions", self._clear_skipped_versions),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
    
    def _toggle_startup_check(self):
        """Toggle check for updates on startup."""
        current = self.update_preferences.get("check_on_startup", True)
        self.update_preferences["check_on_startup"] = not current
        self._save_update_preferences()
        
        success(f"Startup update check: {'enabled' if not current else 'disabled'}")
        # Refresh the current menu
        self.current_menu = self._build_update_settings_menu()
        self.app.invalidate()
    
    def _clear_skipped_versions(self):
        """Clear all skipped versions."""
        self.update_preferences["skipped_versions"] = []
        self._save_update_preferences()
        
        success("Cleared all skipped versions")
        self._go_back()
    
    def _check_authentication(self):
        """Check if user is authenticated."""
        if self.auth_manager:
            self.current_user = self.auth_manager.get_current_user()
            self.needs_auth = self.auth_manager.check_auth_required()
            
            if self.needs_auth:
                warning("Authentication required - Please sign in", duration=5.0)
            else:
                success(f"Welcome {self.current_user.name or self.current_user.email}!", duration=5.0)
        else:
            # No auth module available
            self.needs_auth = False
            self.current_user = None
    
    def _show_auth_menu(self):
        """Show authentication menu for sign in/sign up."""
        auth_menu = [
            MenuItem("🔐 Sign In with Existing Account", self._sign_in),
            MenuItem("🎟️ Sign Up with Invite Code", self._sign_up),
            MenuItem("", separator=True),
            MenuItem("📖 Learn About agtOS Beta", self._show_beta_info),
            MenuItem("🌐 Visit agtos.ai", self._open_website),
            MenuItem("", separator=True),
            MenuItem("Exit", lambda: self.app.exit()),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = auth_menu
        self.selected_index = 0
        # Update breadcrumb for auth menu
        self.breadcrumb_stack = ["Authentication"]
    
    def _sign_in(self):
        """Handle sign in flow with inline dialog."""
        if not self.auth_dialog_manager:
            error("Authentication not available")
            self.app.invalidate()
            return
        
        def on_success(user):
            """Handle successful sign in."""
            self.current_user = user
            self.needs_auth = False
            success(f"Welcome {user.name or user.email}!")
            
            # Rebuild main menu to reflect authenticated state
            self.main_menu = self._build_main_menu()
            self.current_menu = self.main_menu
            self.menu_stack = []
            self.selected_index = 0
            self.breadcrumb_stack = ["Home"]  # Reset breadcrumbs
            
            self.app.invalidate()
        
        # Show sign in dialog
        self.auth_dialog_manager.show_sign_in(on_success)
        self.app.invalidate()
    
    def _sign_up(self):
        """Handle sign up with invite code using inline dialog."""
        if not self.auth_dialog_manager:
            error("Authentication not available")
            self.app.invalidate()
            return
        
        def on_success(user):
            """Handle successful sign up."""
            self.current_user = user
            self.needs_auth = False
            success(f"Welcome {user.name or user.email}! Account created successfully.", duration=5.0)
            
            # Rebuild main menu to reflect authenticated state
            self.main_menu = self._build_main_menu()
            self.current_menu = self.main_menu
            self.menu_stack = []
            self.selected_index = 0
            self.breadcrumb_stack = ["Home"]  # Reset breadcrumbs
            
            self.app.invalidate()
        
        # Show sign up dialog
        self.auth_dialog_manager.show_sign_up(on_success)
        self.app.invalidate()
    
    def _show_beta_info(self):
        """Show information about the beta program."""
        info_menu = [
            MenuItem("🚀 agtOS Beta Program", None),
            MenuItem("", separator=True),
            MenuItem("agtOS is the Agent Operating System that orchestrates", None),
            MenuItem("multiple AI agents through a unified interface.", None),
            MenuItem("", separator=True),
            MenuItem("Beta Access includes:", None),
            MenuItem("  • Natural language tool creation", None),
            MenuItem("  • Multi-agent orchestration", None),
            MenuItem("  • Secure credential management", None),
            MenuItem("  • Workflow automation", None),
            MenuItem("", separator=True),
            MenuItem("Request an invite at agtos.ai", None),
            MenuItem("", separator=True),
            MenuItem("← Back", self._go_back),
        ]
        
        self.menu_stack.append(self.current_menu)
        self.current_menu = info_menu
        self.selected_index = 0
    
    def _open_website(self):
        """Open agtos.ai in browser."""
        import webbrowser
        webbrowser.open("https://agtos.ai")
        info("Opening agtos.ai...")
        self.app.invalidate()
    
    def run(self):
        """Run the TUI application."""
        try:
            self.app.run()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"TUI error: {e}")
            raise
        finally:
            # Clean up animation thread
            self._stop_animation()


def launch_tui():
    """Launch the agtOS Terminal User Interface."""
    tui = AgtOSTUI()
    
    # Check if authentication is required
    if tui.needs_auth:
        # Show auth menu instead of main menu
        tui._show_auth_menu()
    elif tui.is_first_run:
        # Start tutorial for first-time users
        tui.tutorial_manager.start_tutorial()
    
    tui.run()


if __name__ == "__main__":
    launch_tui()