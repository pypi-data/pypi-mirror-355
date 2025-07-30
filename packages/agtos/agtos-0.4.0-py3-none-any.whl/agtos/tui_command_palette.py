"""Terminal User Interface Command Palette for agtOS.

This module provides a command palette (Ctrl+P) for quick access to any action
in the TUI, similar to VS Code's command palette.

AI_CONTEXT:
    The command palette provides:
    - Quick access to any menu action via fuzzy search
    - Command categories and keyboard shortcuts display
    - Recently used commands tracking
    - Smart ordering based on usage frequency
    - Modal overlay UI with search input
"""

import json
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from prompt_toolkit.layout import Float, Window, FormattedTextControl, HSplit, VSplit
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app

from .config import get_config_dir
from .utils import get_logger
from .metamcp.fuzzy_match import fuzzy_match_tools

logger = get_logger(__name__)


@dataclass
class Command:
    """Represents a command in the palette."""
    id: str  # Unique identifier
    label: str  # Display label
    category: str  # Category (e.g., "Navigation", "Tools", "Settings")
    action: Optional[Callable]  # Action to execute
    shortcut: Optional[str] = None  # Keyboard shortcut if any
    path: List[str] = None  # Menu path to reach this command
    hint: Optional[str] = None  # Additional hint text
    usage_count: int = 0  # Track usage frequency
    last_used: Optional[datetime] = None  # Track recency


class CommandRegistry:
    """Registry for all available commands.
    
    AI_CONTEXT:
        This class maintains a registry of all available commands from menus,
        tracks usage statistics, and provides search functionality.
    """
    
    def __init__(self):
        """Initialize the command registry."""
        self.commands: Dict[str, Command] = {}
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        self._load_usage_stats()
    
    def register_command(self, command: Command):
        """Register a command in the registry."""
        self.commands[command.id] = command
        
        # Apply saved usage stats if available
        if command.id in self.usage_stats:
            stats = self.usage_stats[command.id]
            command.usage_count = stats.get("count", 0)
            last_used_str = stats.get("last_used")
            if last_used_str:
                command.last_used = datetime.fromisoformat(last_used_str)
    
    def clear(self):
        """Clear all registered commands (useful for rebuilding)."""
        self.commands.clear()
    
    def search(self, query: str, limit: int = 20) -> List[Command]:
        """Search commands using fuzzy matching."""
        if not query:
            # Return recent commands when no query
            return self._get_recent_commands(limit)
        
        # Collect all command labels and IDs for fuzzy matching
        command_info = [(cmd.label, cmd.id) for cmd in self.commands.values()]
        labels = [label for label, _ in command_info]
        
        # Fuzzy match on labels
        matches = fuzzy_match_tools(query, labels, max_suggestions=limit * 2, threshold=0.3)
        
        # Convert matches back to commands
        results = []
        matched_ids = set()
        
        for matched_label, score in matches:
            # Find the command with this label
            for label, cmd_id in command_info:
                if label == matched_label and cmd_id not in matched_ids:
                    results.append(self.commands[cmd_id])
                    matched_ids.add(cmd_id)
                    break
        
        # Also search in categories and hints
        query_lower = query.lower()
        for cmd in self.commands.values():
            if cmd.id not in matched_ids:
                if (query_lower in cmd.category.lower() or 
                    (cmd.hint and query_lower in cmd.hint.lower())):
                    results.append(cmd)
                    matched_ids.add(cmd.id)
        
        # Sort by relevance and usage
        results.sort(key=lambda c: (
            -c.usage_count,  # Most used first
            c.last_used is None,  # Recently used first
            -(c.last_used.timestamp() if c.last_used else 0)
        ))
        
        return results[:limit]
    
    def _get_recent_commands(self, limit: int) -> List[Command]:
        """Get recently used commands."""
        # Filter commands that have been used
        used_commands = [cmd for cmd in self.commands.values() if cmd.usage_count > 0]
        
        # Sort by recency and usage
        used_commands.sort(key=lambda c: (
            c.last_used is None,  # Recently used first
            -(c.last_used.timestamp() if c.last_used else 0),
            -c.usage_count  # Then by usage count
        ))
        
        return used_commands[:limit]
    
    def record_usage(self, command_id: str):
        """Record that a command was used."""
        if command_id in self.commands:
            cmd = self.commands[command_id]
            cmd.usage_count += 1
            cmd.last_used = datetime.now()
            
            # Update persistent stats
            self.usage_stats[command_id] = {
                "count": cmd.usage_count,
                "last_used": cmd.last_used.isoformat()
            }
            self._save_usage_stats()
    
    def _load_usage_stats(self):
        """Load usage statistics from disk."""
        stats_file = get_config_dir() / "command_usage.json"
        if stats_file.exists():
            try:
                with open(stats_file) as f:
                    self.usage_stats = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load command usage stats: {e}")
                self.usage_stats = {}
        else:
            self.usage_stats = {}
    
    def _save_usage_stats(self):
        """Save usage statistics to disk."""
        stats_file = get_config_dir() / "command_usage.json"
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save command usage stats: {e}")
    
    def get_categories(self) -> Dict[str, List[Command]]:
        """Get commands organized by category."""
        categories = defaultdict(list)
        for cmd in self.commands.values():
            categories[cmd.category].append(cmd)
        
        # Sort commands within each category
        for category in categories:
            categories[category].sort(key=lambda c: (-c.usage_count, c.label))
        
        return dict(categories)


class CommandPalette:
    """Command palette UI component.
    
    AI_CONTEXT:
        This class provides the UI for the command palette, including:
        - Modal overlay with search input
        - Filtered command list display
        - Keyboard navigation
        - Command execution
    """
    
    def __init__(self, registry: CommandRegistry, app=None, tui=None):
        """Initialize the command palette."""
        self.registry = registry
        self.app = app or get_app()
        self.tui = tui  # Reference to parent TUI for navigation
        self.visible = False
        self.search_buffer = TextArea(
            multiline=False,
            height=1,
            prompt="Search commands: ",
            style="class:command-palette.input",
            focusable=True,
        )
        self.selected_index = 0
        self.filtered_commands: List[Command] = []
        
        # Set up key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()
        
        # Update filtered commands when search changes
        self.search_buffer.buffer.on_text_changed += self._on_search_changed
    
    def _setup_key_bindings(self):
        """Set up key bindings for the command palette."""
        @self.kb.add('escape')
        def close_palette(event):
            self.hide()
        
        @self.kb.add('up')
        def move_up(event):
            if self.selected_index > 0:
                self.selected_index -= 1
                self.app.invalidate()
        
        @self.kb.add('down')
        def move_down(event):
            if self.selected_index < len(self.filtered_commands) - 1:
                self.selected_index += 1
                self.app.invalidate()
        
        @self.kb.add('enter')
        def execute_command(event):
            if 0 <= self.selected_index < len(self.filtered_commands):
                cmd = self.filtered_commands[self.selected_index]
                self.execute_command(cmd)
    
    def _on_search_changed(self, _):
        """Handle search text changes."""
        query = self.search_buffer.text.strip()
        self.filtered_commands = self.registry.search(query)
        self.selected_index = 0
        self.app.invalidate()
    
    def show(self):
        """Show the command palette."""
        self.visible = True
        self.search_buffer.text = ""
        self.filtered_commands = self.registry.search("")
        self.selected_index = 0
        self.app.layout.focus(self.search_buffer)
        self.app.invalidate()
    
    def hide(self):
        """Hide the command palette."""
        self.visible = False
        self.app.invalidate()
    
    def execute_command(self, command: Command):
        """Execute a command and hide the palette."""
        self.hide()
        
        # Record usage
        self.registry.record_usage(command.id)
        
        # If command has a path and TUI reference, navigate to it first
        if command.path and self.tui:
            # Navigate through the menu structure
            self.tui._navigate_to_command(command)
        
        # Execute the action
        if command.action:
            try:
                command.action()
            except Exception as e:
                logger.error(f"Failed to execute command {command.id}: {e}")
                # In a real app, would show error toast
    
    def get_dialog_float(self) -> Optional[Float]:
        """Get the float container for the command palette."""
        if not self.visible:
            return None
        
        # Create the content
        content = self._create_dialog_content()
        
        # Wrap in a frame
        frame = Frame(
            content,
            title="Command Palette",
            style="class:command-palette.frame",
        )
        
        return Float(
            content=frame,
            transparent=False,
            top=5,  # Position from top
            left=10,  # Center horizontally with margin
            right=10,
            height=Dimension(min=10, max=30, preferred=20),
        )
    
    def _create_dialog_content(self) -> HSplit:
        """Create the dialog content."""
        # Search input at top
        search_section = self.search_buffer
        
        # Command list
        command_list = Window(
            FormattedTextControl(
                lambda: self._render_commands(),
                focusable=False,
            ),
            style="class:command-palette.list",
        )
        
        # Help text at bottom
        help_text = Window(
            FormattedTextControl(
                FormattedText([
                    ('class:command-palette.help', '↑↓: Navigate  Enter: Execute  Esc: Close')
                ])
            ),
            height=1,
            style="class:command-palette.help",
        )
        
        return HSplit([
            search_section,
            Window(height=1),  # Separator
            command_list,
            Window(height=1),  # Separator
            help_text,
        ])
    
    def _render_commands(self) -> FormattedText:
        """Render the filtered command list."""
        if not self.filtered_commands:
            return FormattedText([
                ('class:command-palette.empty', 'No commands found')
            ])
        
        lines = []
        
        # Group by category for better organization
        current_category = None
        
        for i, cmd in enumerate(self.filtered_commands):
            # Show category header if it changes
            if cmd.category != current_category:
                if current_category is not None:
                    lines.append(('', '\n'))
                lines.append(('class:command-palette.category', f'  {cmd.category}\n'))
                current_category = cmd.category
            
            # Selection indicator
            is_selected = i == self.selected_index
            if is_selected:
                lines.append(('class:command-palette.selected', '  > '))
            else:
                lines.append(('', '    '))
            
            # Command label
            style = 'class:command-palette.selected' if is_selected else ''
            lines.append((style, cmd.label))
            
            # Keyboard shortcut if available
            if cmd.shortcut:
                padding = 50 - len(cmd.label)
                lines.append(('', ' ' * max(1, padding)))
                lines.append(('class:command-palette.shortcut', f'[{cmd.shortcut}]'))
            
            # Usage indicator (for frequently used commands)
            if cmd.usage_count > 5:
                lines.append(('class:command-palette.frequent', ' ★'))
            
            lines.append(('', '\n'))
        
        return FormattedText(lines)
    
    def get_style_dict(self) -> Dict[str, str]:
        """Get style definitions for the command palette."""
        return {
            'command-palette.frame': 'bg:#1e1e1e #ffffff',
            'command-palette.input': 'bg:#2d2d2d #ffffff',
            'command-palette.list': 'bg:#1e1e1e',
            'command-palette.category': '#888888 bold',
            'command-palette.selected': 'bg:#094771 #ffffff',
            'command-palette.shortcut': '#888888',
            'command-palette.frequent': '#ffd700',
            'command-palette.empty': '#888888 italic',
            'command-palette.help': '#666666',
        }


def build_command_registry_from_menu(menu_items, registry: CommandRegistry, path: List[str] = None):
    """Build command registry from menu structure.
    
    AI_CONTEXT:
        This function recursively traverses the menu structure and registers
        all actionable items as commands in the registry.
    """
    if path is None:
        path = []
    
    for item in menu_items:
        if item.separator:
            continue
        
        # Determine category from path
        if not path:
            category = "Main"
        elif any(keyword in path[0].lower() for keyword in ["credential", "api", "key"]):
            category = "Credentials"
        elif "project" in path[0].lower():
            category = "Projects"
        elif "workflow" in path[0].lower():
            category = "Workflows"
        elif any(keyword in path[0].lower() for keyword in ["help", "doc", "tutorial", "tip"]):
            category = "Help"
        elif "agent" in path[0].lower():
            category = "Agents"
        elif any(keyword in path[0].lower() for keyword in ["update", "setting", "preference"]):
            category = "Settings"
        elif "server" in path[0].lower() or "status" in path[0].lower():
            category = "System"
        else:
            category = "Tools"
        
        # Create command ID from path and label
        cmd_id = "_".join(path + [item.label]).replace(" ", "_").replace("/", "_").lower()
        
        # Skip back navigation items and separators
        if "back" in item.label.lower() or item.label.startswith("←") or not item.label.strip():
            continue
        
        # Skip non-actionable info items
        if item.label.startswith("📖") or item.label.startswith("📊") or item.label.startswith("💡"):
            if not item.action and not item.submenu:
                continue
        
        # Register command if it has an action
        if item.action:
            # Add keyboard shortcut hints
            shortcut = None
            if "open claude" in item.label.lower():
                shortcut = "Main Action"
            elif "search" in item.label.lower() and "/" in item.label:
                shortcut = "/"
            
            cmd = Command(
                id=cmd_id,
                label=item.label,
                category=category,
                action=item.action,
                shortcut=shortcut,
                path=path.copy(),
                hint=item.hint,
            )
            registry.register_command(cmd)
        
        # Also register submenu items for navigation
        elif item.submenu:
            # Register as a navigation command
            cmd = Command(
                id=cmd_id + "_menu",
                label=f"Navigate to {item.label}",
                category="Navigation",
                action=None,  # Will be handled by navigation
                shortcut=None,
                path=path.copy() + [item.label],
                hint=f"Open {item.label} submenu",
            )
            registry.register_command(cmd)
        
        # Recursively process submenus
        if item.submenu:
            build_command_registry_from_menu(
                item.submenu,
                registry,
                path + [item.label]
            )