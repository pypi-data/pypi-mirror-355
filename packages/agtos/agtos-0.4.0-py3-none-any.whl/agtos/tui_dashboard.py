"""Status dashboard view for the agtOS TUI.

This module provides a real-time dashboard showing:
- Active AI agent operations
- Running system processes
- Recent completed operations
- System metrics and costs

AI_CONTEXT:
    The dashboard gives users visibility into what the system is doing,
    helping them track costs and monitor operations. It auto-refreshes
    every second to show real-time status.
"""

import time
import threading
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from prompt_toolkit.layout import HSplit, VSplit, Window, FormattedTextControl
from prompt_toolkit.layout.containers import Container
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.widgets import Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import Dimension

from .operation_manager import get_operation_manager, OperationType, OperationStatus
from .metamcp.registry import ServiceRegistry
from .utils import get_logger

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = get_logger(__name__)


class DashboardView:
    """Real-time status dashboard for agtOS.
    
    AI_CONTEXT:
        This view provides a comprehensive overview of system activity.
        It's designed to be the "mission control" for agtOS operations.
    """
    
    def __init__(self, app, parent_tui):
        """Initialize the dashboard view.
        
        Args:
            app: The prompt_toolkit application
            parent_tui: The parent TUI instance
        """
        self.app = app
        self.parent_tui = parent_tui
        self.operation_manager = get_operation_manager()
        self.visible = False
        self.start_time = time.time()
        self.selected_section = 0  # Which section is selected
        self.scroll_offset = 0  # Scroll position in current section
        
        # Subscribe to operation updates
        self.operation_manager.add_listener(self._on_operations_changed)
        
        # Start refresh thread
        self._start_refresh_thread()
    
    def _start_refresh_thread(self):
        """Start thread to refresh dashboard every second."""
        def refresh():
            while True:
                time.sleep(1)
                if self.visible and self.app and self.app.is_running:
                    self.app.invalidate()
        
        thread = threading.Thread(target=refresh, daemon=True)
        thread.start()
    
    def _on_operations_changed(self):
        """Called when operations change."""
        if self.visible and self.app and self.app.is_running:
            self.app.invalidate()
    
    def get_container(self) -> Container:
        """Get the dashboard container."""
        return HSplit([
            # Header
            Window(
                FormattedTextControl(self._render_header),
                height=3,
                style='class:dashboard.header'
            ),
            # Main content area with sections
            VSplit([
                # Left column - Active operations and processes
                HSplit([
                    self._create_section(
                        "Active Operations",
                        self._render_active_operations,
                        selected=(self.selected_section == 0)
                    ),
                    self._create_section(
                        "System Processes",
                        self._render_system_processes,
                        height=8,
                        selected=(self.selected_section == 1)
                    ),
                ], width=Dimension(weight=1)),
                
                # Right column - Recent activity and metrics
                HSplit([
                    self._create_section(
                        "Recent Activity",
                        self._render_recent_activity,
                        selected=(self.selected_section == 2)
                    ),
                    self._create_section(
                        "System Metrics",
                        self._render_system_metrics,
                        height=12,
                        selected=(self.selected_section == 3)
                    ),
                ], width=Dimension(weight=1)),
            ]),
            # Footer with controls
            Window(
                FormattedTextControl(self._render_footer),
                height=2,
                style='class:dashboard.footer'
            ),
        ])
    
    def _create_section(
        self,
        title: str,
        content_renderer: Callable,
        height: Optional[int] = None,
        selected: bool = False
    ) -> Container:
        """Create a dashboard section with title and content."""
        border_style = 'class:dashboard.section.selected' if selected else 'class:dashboard.section'
        
        return Frame(
            Window(
                FormattedTextControl(content_renderer),
                wrap_lines=True,
                height=Dimension(min=height) if height else None,
            ),
            title=title,
            style=border_style
        )
    
    def _render_header(self) -> FormattedText:
        """Render the dashboard header."""
        uptime = self._format_duration(time.time() - self.start_time)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return FormattedText([
            ('class:dashboard.title', '  📊 agtOS Status Dashboard'),
            ('', '    '),
            ('class:dashboard.time', f'Time: {current_time}'),
            ('', '    '),
            ('class:dashboard.uptime', f'Uptime: {uptime}'),
        ])
    
    def _render_active_operations(self) -> FormattedText:
        """Render active operations section."""
        operations = self.operation_manager.get_active_operations()
        ai_ops = [op for op in operations if op.type == OperationType.AI_AGENT]
        
        lines = []
        
        if not ai_ops:
            lines.append(('class:dashboard.empty', '  No active AI operations\n'))
        else:
            for op in ai_ops[:5]:  # Show max 5
                # Progress bar
                progress = op.progress or 0
                bar_width = 20
                filled = int(progress * bar_width)
                bar = '█' * filled + '░' * (bar_width - filled)
                
                # Duration
                duration = self._format_duration(time.time() - op.start_time)
                
                lines.extend([
                    ('class:dashboard.operation.name', f'  {op.name}\n'),
                    ('class:dashboard.operation.desc', f'    {op.description}\n'),
                    ('', f'    [{bar}] {progress*100:.0f}%  {duration}\n'),
                    ('', '\n')
                ])
            
            if len(operations) > 5:
                lines.append(('class:dashboard.more', f'  ... and {len(operations) - 5} more\n'))
        
        return FormattedText(lines)
    
    def _render_system_processes(self) -> FormattedText:
        """Render system processes section."""
        operations = self.operation_manager.get_active_operations()
        sys_ops = [op for op in operations if op.type == OperationType.SYSTEM_PROCESS]
        
        lines = []
        
        if not sys_ops:
            lines.append(('class:dashboard.empty', '  No active system processes\n'))
        else:
            for op in sys_ops[:3]:  # Show max 3
                duration = self._format_duration(time.time() - op.start_time)
                command = op.metadata.get('command', '')[:40] + '...' if len(op.metadata.get('command', '')) > 40 else op.metadata.get('command', '')
                
                lines.extend([
                    ('class:dashboard.process.name', f'  {op.metadata.get("process", op.name)}: '),
                    ('class:dashboard.process.cmd', f'{command}\n'),
                    ('class:dashboard.process.time', f'    Running for {duration}\n'),
                    ('', '\n')
                ])
        
        return FormattedText(lines)
    
    def _render_recent_activity(self) -> FormattedText:
        """Render recent activity section."""
        recent = self.operation_manager.get_recent_operations(10)
        
        lines = []
        
        if not recent:
            lines.append(('class:dashboard.empty', '  No recent activity\n'))
        else:
            for op in reversed(recent):  # Show newest first
                # Time ago
                time_ago = self._format_time_ago(op.end_time)
                
                # Status icon
                status_icon = '✅' if op.status == OperationStatus.COMPLETED else '❌'
                
                # Cost if applicable
                cost_str = f' (${op.cost:.4f})' if op.cost else ''
                
                lines.extend([
                    ('', f'  {status_icon} '),
                    ('class:dashboard.recent.name', op.name),
                    ('class:dashboard.recent.cost', cost_str),
                    ('', '\n'),
                    ('class:dashboard.recent.time', f'    {time_ago}'),
                    ('class:dashboard.recent.duration', f' • {self._format_duration(op.duration)}'),
                    ('', '\n\n')
                ])
        
        return FormattedText(lines)
    
    def _render_system_metrics(self) -> FormattedText:
        """Render system metrics section."""
        stats = self.operation_manager.get_statistics()
        
        # Get tool count from registry if available
        try:
            registry = ServiceRegistry()
            tool_count = sum(len(svc.tools) for svc in registry.services.values())
        except:
            tool_count = 87  # Default
        
        lines = [
            ('class:dashboard.metric.label', '  Active Operations: '),
            ('class:dashboard.metric.value', f'{stats["active_count"]}\n'),
            ('class:dashboard.metric.label', '  Completed Today: '),
            ('class:dashboard.metric.value', f'{stats["completed_count"]}\n'),
            ('class:dashboard.metric.label', '  Available Tools: '),
            ('class:dashboard.metric.value', f'{tool_count}\n'),
            ('', '\n'),
        ]
        
        # System resources if psutil available
        if PSUTIL_AVAILABLE:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                lines.extend([
                    ('class:dashboard.metric.section', '  📊 System Resources:\n'),
                    ('class:dashboard.metric.label', '  CPU Usage: '),
                    ('class:dashboard.metric.value', f'{cpu_percent:.1f}%\n'),
                    ('class:dashboard.metric.label', '  Memory: '),
                    ('class:dashboard.metric.value', f'{memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f}GB / {memory.total/1024/1024/1024:.1f}GB)\n'),
                    ('', '\n'),
                ])
            except Exception as e:
                logger.debug(f"Failed to get system metrics: {e}")
        
        lines.extend([
            ('class:dashboard.metric.section', '  💰 Session Costs:\n'),
            ('class:dashboard.metric.label', '  Total: '),
            ('class:dashboard.metric.cost', f'${stats["total_cost"]:.4f}\n'),
            ('', '\n'),
        ])
        
        # Cost breakdown by agent
        if stats["cost_by_agent"]:
            lines.append(('class:dashboard.metric.section', '  Cost by Agent:\n'))
            for agent, cost in sorted(stats["cost_by_agent"].items(), key=lambda x: x[1], reverse=True):
                lines.extend([
                    ('class:dashboard.metric.label', f'  {agent}: '),
                    ('class:dashboard.metric.cost', f'${cost:.4f}\n')
                ])
        
        return FormattedText(lines)
    
    def _render_footer(self) -> FormattedText:
        """Render the dashboard footer."""
        return FormattedText([
            ('', '  '),
            ('class:dashboard.help', 'Tab: Switch sections  ↑↓: Scroll  C: Clear history  R: Reset costs  ESC: Back to menu  Ctrl+D: Dismiss'),
        ])
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m {seconds%60:.0f}s"
        else:
            hours = seconds / 3600
            mins = (seconds % 3600) / 60
            return f"{hours:.0f}h {mins:.0f}m"
    
    def _format_time_ago(self, timestamp: float) -> str:
        """Format timestamp as time ago."""
        if not timestamp:
            return "Unknown"
        
        seconds_ago = time.time() - timestamp
        
        if seconds_ago < 60:
            return f"{seconds_ago:.0f}s ago"
        elif seconds_ago < 3600:
            return f"{seconds_ago/60:.0f}m ago"
        elif seconds_ago < 86400:
            return f"{seconds_ago/3600:.0f}h ago"
        else:
            return f"{seconds_ago/86400:.0f}d ago"
    
    def get_key_bindings(self) -> KeyBindings:
        """Get key bindings for the dashboard."""
        kb = KeyBindings()
        
        @kb.add('tab')
        def switch_section(event):
            """Switch between dashboard sections."""
            self.selected_section = (self.selected_section + 1) % 4
            self.scroll_offset = 0
        
        @kb.add('up')
        def scroll_up(event):
            """Scroll up in current section."""
            self.scroll_offset = max(0, self.scroll_offset - 1)
        
        @kb.add('down')
        def scroll_down(event):
            """Scroll down in current section."""
            self.scroll_offset += 1
        
        @kb.add('c')
        def clear_history(event):
            """Clear completed operations history."""
            self.operation_manager.completed_operations = []
            if hasattr(self.parent_tui, 'toast_manager'):
                from .tui_toast import success
                success("Cleared operation history")
        
        @kb.add('r')
        def reset_costs(event):
            """Reset session costs."""
            self.operation_manager.reset_session()
            if hasattr(self.parent_tui, 'toast_manager'):
                from .tui_toast import success
                success("Reset session costs")
        
        @kb.add('escape')
        def close_dashboard(event):
            """Close the dashboard."""
            self.hide()
            self.parent_tui.dashboard_visible = False
            self.parent_tui.app.invalidate()
        
        return kb
    
    def show(self):
        """Show the dashboard."""
        self.visible = True
        self.selected_section = 0
        self.scroll_offset = 0
        self.app.invalidate()
    
    def hide(self):
        """Hide the dashboard."""
        self.visible = False
        self.app.invalidate()
    
    def get_style_dict(self) -> Dict[str, str]:
        """Get styles for the dashboard."""
        return {
            # Headers and titles
            'dashboard.header': 'bg:#1a1a1a #ffffff',
            'dashboard.title': '#00ff88 bold',
            'dashboard.time': '#888888',
            'dashboard.uptime': '#666666',
            
            # Sections
            'dashboard.section': 'bg:#0d0d0d #888888',
            'dashboard.section.selected': 'bg:#0d0d0d #00ff88',
            
            # Operations
            'dashboard.operation.name': '#00aaff bold',
            'dashboard.operation.desc': '#cccccc',
            'dashboard.empty': '#666666 italic',
            'dashboard.more': '#888888 italic',
            
            # Processes
            'dashboard.process.name': '#ffaa00 bold',
            'dashboard.process.cmd': '#aaaaaa',
            'dashboard.process.time': '#666666',
            
            # Recent activity
            'dashboard.recent.name': '#ffffff',
            'dashboard.recent.cost': '#00ff00',
            'dashboard.recent.time': '#666666',
            'dashboard.recent.duration': '#888888',
            
            # Metrics
            'dashboard.metric.section': '#00ff88 bold',
            'dashboard.metric.label': '#aaaaaa',
            'dashboard.metric.value': '#ffffff bold',
            'dashboard.metric.cost': '#00ff00 bold',
            
            # Footer
            'dashboard.footer': 'bg:#1a1a1a #888888',
            'dashboard.help': '#666666',
        }