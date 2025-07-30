"""Toast notification system for the TUI.

This module provides a toast notification component that displays temporary messages
with automatic dismissal and slide animations.

AI_CONTEXT:
    Toast notifications provide non-intrusive feedback for user actions.
    They appear in the top-right corner and auto-dismiss after a timeout.
    Multiple toasts can stack vertically with proper spacing.
    Users can dismiss toasts manually with click/key interaction.
"""

import time
import threading
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from collections import deque

try:
    from prompt_toolkit.application import get_app
    from prompt_toolkit.layout import Window, FormattedTextControl, Container
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.layout.dimension import Dimension
except ImportError:
    # Handle case where prompt_toolkit is not installed
    def get_app():
        return None


class ToastType(Enum):
    """Types of toast notifications with associated icons and colors."""
    SUCCESS = ("✅", "success")
    ERROR = ("❌", "error")
    INFO = ("ℹ️", "info")
    WARNING = ("⚠️", "warning")


@dataclass
class Toast:
    """Represents a single toast notification."""
    message: str
    type: ToastType
    duration: float = 3.0
    created_at: float = 0.0
    dismissing: bool = False
    dismiss_at: float = 0.0
    id: str = ""
    on_dismiss: Optional[Callable] = None
    
    def __post_init__(self):
        """Initialize timestamps and ID."""
        if not self.created_at:
            self.created_at = time.time()
        if not self.dismiss_at:
            self.dismiss_at = self.created_at + self.duration
        if not self.id:
            self.id = f"toast_{int(self.created_at * 1000)}"


class ToastManager:
    """Manages toast notifications for the TUI.
    
    AI_CONTEXT:
        The ToastManager handles the lifecycle of toast notifications:
        - Queue management for multiple toasts
        - Automatic dismissal after timeout
        - Slide animations for appearance/disappearance
        - Thread-safe operations
        - Integration with prompt_toolkit layout
    """
    
    MAX_TOASTS = 5  # Maximum number of visible toasts
    SLIDE_DURATION = 0.3  # Duration of slide animation in seconds
    VERTICAL_SPACING = 1  # Lines between toasts
    
    def __init__(self):
        """Initialize the toast manager."""
        self._toasts: deque[Toast] = deque(maxlen=self.MAX_TOASTS)
        self._lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def show(
        self,
        message: str,
        type: ToastType = ToastType.INFO,
        duration: float = 3.0,
        on_dismiss: Optional[Callable] = None
    ) -> str:
        """Show a toast notification.
        
        Args:
            message: The message to display
            type: Type of toast (success, error, info, warning)
            duration: How long to show the toast in seconds
            on_dismiss: Optional callback when toast is dismissed
            
        Returns:
            toast_id: The ID of the created toast
        """
        toast = Toast(
            message=message,
            type=type,
            duration=duration,
            on_dismiss=on_dismiss
        )
        
        with self._lock:
            self._toasts.append(toast)
            
            # Start cleanup thread if not running
            if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
                self._stop_event.clear()
                self._cleanup_thread = threading.Thread(
                    target=self._cleanup_loop,
                    daemon=True
                )
                self._cleanup_thread.start()
        
        # Trigger UI refresh
        app = get_app()
        if app and app.is_running:
            app.invalidate()
            
        return toast.id
    
    def dismiss(self, toast_id: str):
        """Manually dismiss a toast by ID."""
        with self._lock:
            for toast in self._toasts:
                if toast.id == toast_id and not toast.dismissing:
                    toast.dismissing = True
                    toast.dismiss_at = time.time() + self.SLIDE_DURATION
                    if toast.on_dismiss:
                        threading.Thread(target=toast.on_dismiss, daemon=True).start()
                    break
        
        # Trigger UI refresh
        app = get_app()
        if app and app.is_running:
            app.invalidate()
    
    def dismiss_all(self):
        """Dismiss all active toasts."""
        with self._lock:
            for toast in self._toasts:
                if not toast.dismissing:
                    toast.dismissing = True
                    toast.dismiss_at = time.time() + self.SLIDE_DURATION
                    if toast.on_dismiss:
                        threading.Thread(target=toast.on_dismiss, daemon=True).start()
    
    def get_toast_windows(self) -> List[Tuple[Window, int, int]]:
        """Get window components for all active toasts.
        
        Returns:
            List of (window, row_offset, col_offset) tuples for positioning
        """
        windows = []
        
        with self._lock:
            current_time = time.time()
            visible_toasts = []
            
            # Filter visible toasts
            for toast in self._toasts:
                if toast.dismissing:
                    # Keep showing during slide-out animation
                    if current_time < toast.dismiss_at:
                        visible_toasts.append(toast)
                else:
                    # Check if should start dismissing
                    if current_time >= toast.dismiss_at:
                        toast.dismissing = True
                        toast.dismiss_at = current_time + self.SLIDE_DURATION
                        if toast.on_dismiss:
                            threading.Thread(target=toast.on_dismiss, daemon=True).start()
                    visible_toasts.append(toast)
            
            # Create windows for visible toasts
            row_offset = 2  # Start 2 rows from top
            
            for i, toast in enumerate(visible_toasts):
                # Calculate slide offset
                slide_offset = self._calculate_slide_offset(toast, current_time)
                
                # Create formatted text with proper styling
                icon, style_class = toast.type.value
                formatted_text = FormattedText([
                    (f'class:toast.{style_class}', f' {icon} {toast.message} ')
                ])
                
                # Create window
                window = Window(
                    content=FormattedTextControl(formatted_text),
                    height=Dimension(min=1, max=1),
                    width=Dimension(min=len(toast.message) + 5, max=50),
                    style=f'class:toast.{style_class}.bg',
                    dont_extend_width=True,
                    dont_extend_height=True,
                )
                
                # Calculate position (right-aligned with slide effect)
                col_offset = -len(toast.message) - 7 + slide_offset  # Right edge with padding
                
                windows.append((window, row_offset, col_offset))
                row_offset += 1 + self.VERTICAL_SPACING
        
        return windows
    
    def _calculate_slide_offset(self, toast: Toast, current_time: float) -> int:
        """Calculate horizontal slide offset for animation."""
        if toast.dismissing:
            # Slide out to the right
            progress = (current_time - (toast.dismiss_at - self.SLIDE_DURATION)) / self.SLIDE_DURATION
            progress = min(1.0, max(0.0, progress))
            return int(progress * 60)  # Slide 60 chars to the right
        else:
            # Slide in from the right
            age = current_time - toast.created_at
            if age < self.SLIDE_DURATION:
                progress = age / self.SLIDE_DURATION
                progress = min(1.0, max(0.0, progress))
                return int((1.0 - progress) * 60)  # Start 60 chars to the right
        
        return 0  # No offset when fully visible
    
    def _cleanup_loop(self):
        """Background thread to remove dismissed toasts."""
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                with self._lock:
                    # Remove fully dismissed toasts
                    self._toasts = deque(
                        (t for t in self._toasts 
                         if not (t.dismissing and current_time >= t.dismiss_at)),
                        maxlen=self.MAX_TOASTS
                    )
                    
                    # Stop thread if no more toasts
                    if not self._toasts:
                        self._stop_event.set()
                
                # Trigger UI refresh if app is running
                app = get_app()
                if app and app.is_running:
                    app.invalidate()
                
                # Sleep briefly
                time.sleep(0.1)
                
            except Exception:
                # Ignore errors in cleanup thread
                pass
    
    def get_style_dict(self) -> dict:
        """Get style definitions for toast notifications."""
        return {
            # Success style
            'toast.success': '#00ff00',
            'toast.success.bg': 'bg:#1a3d1a',
            
            # Error style
            'toast.error': '#ff0000',
            'toast.error.bg': 'bg:#3d1a1a',
            
            # Info style
            'toast.info': '#00aaff',
            'toast.info.bg': 'bg:#1a2a3d',
            
            # Warning style
            'toast.warning': '#ffaa00',
            'toast.warning.bg': 'bg:#3d2a1a',
        }
    
    def stop(self):
        """Stop the toast manager and cleanup threads."""
        self._stop_event.set()
        self.dismiss_all()


# Global toast manager instance
_toast_manager: Optional[ToastManager] = None


def get_toast_manager() -> ToastManager:
    """Get the global toast manager instance."""
    global _toast_manager
    if _toast_manager is None:
        _toast_manager = ToastManager()
    return _toast_manager


# Convenience functions for showing toasts
def success(message: str, duration: float = 3.0, on_dismiss: Optional[Callable] = None) -> str:
    """Show a success toast."""
    return get_toast_manager().show(message, ToastType.SUCCESS, duration, on_dismiss)


def error(message: str, duration: float = 5.0, on_dismiss: Optional[Callable] = None) -> str:
    """Show an error toast (longer duration by default)."""
    return get_toast_manager().show(message, ToastType.ERROR, duration, on_dismiss)


def info(message: str, duration: float = 3.0, on_dismiss: Optional[Callable] = None) -> str:
    """Show an info toast."""
    return get_toast_manager().show(message, ToastType.INFO, duration, on_dismiss)


def warning(message: str, duration: float = 4.0, on_dismiss: Optional[Callable] = None) -> str:
    """Show a warning toast."""
    return get_toast_manager().show(message, ToastType.WARNING, duration, on_dismiss)