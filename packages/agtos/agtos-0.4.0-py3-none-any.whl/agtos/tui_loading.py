"""Loading indicators and spinner components for the TUI.

This module provides reusable loading components for the agtOS Terminal User Interface.
It includes spinner animations and loading messages for operations that take time.

AI_CONTEXT:
    Loading indicators are crucial for user experience in terminal interfaces.
    This module provides:
    - Animated spinners with customizable frames
    - Loading messages with context
    - Thread-safe operation updates
    - Automatic cleanup on completion
"""

import threading
import time
from typing import Optional, List, Callable
from dataclasses import dataclass

try:
    from prompt_toolkit.application import get_app
except ImportError:
    # Handle case where prompt_toolkit is not installed
    def get_app():
        return None


@dataclass
class LoadingState:
    """Represents the state of a loading operation."""
    active: bool = False
    message: str = "Loading..."
    spinner_index: int = 0
    start_time: float = 0.0
    operation_id: Optional[str] = None


class LoadingSpinner:
    """Thread-safe loading spinner for TUI operations.
    
    AI_CONTEXT:
        This spinner runs in a separate thread to avoid blocking the UI.
        It updates the application display at regular intervals.
        Multiple spinners can run simultaneously with different messages.
    """
    
    # Unicode spinner frames for smooth animation
    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    # Alternative spinner styles
    SPINNER_STYLES = {
        'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        'line': ['|', '/', '-', '\\'],
        'arrow': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
        'circle': ['◐', '◓', '◑', '◒'],
        'bounce': ['⠁', '⠂', '⠄', '⠂'],
        'pulse': ['∙', '●', '⬤', '●'],
    }
    
    def __init__(self, style: str = 'dots'):
        """Initialize the spinner with a specific style."""
        self.style = style
        self.frames = self.SPINNER_STYLES.get(style, self.SPINNER_STYLES['dots'])
        self.loading_states: dict[str, LoadingState] = {}
        self._lock = threading.Lock()
        self._animation_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self, message: str = "Loading...", operation_id: Optional[str] = None) -> str:
        """Start a loading spinner with a message.
        
        Args:
            message: The loading message to display
            operation_id: Optional ID to track specific operations
            
        Returns:
            operation_id: The ID of this loading operation
        """
        if operation_id is None:
            operation_id = f"op_{int(time.time() * 1000)}"
        
        with self._lock:
            self.loading_states[operation_id] = LoadingState(
                active=True,
                message=message,
                start_time=time.time(),
                operation_id=operation_id
            )
            
            # Start animation thread if not running
            if self._animation_thread is None or not self._animation_thread.is_alive():
                self._stop_event.clear()
                self._animation_thread = threading.Thread(
                    target=self._animate,
                    daemon=True
                )
                self._animation_thread.start()
        
        return operation_id
    
    def stop(self, operation_id: str, final_message: Optional[str] = None):
        """Stop a specific loading operation.
        
        Args:
            operation_id: The ID of the operation to stop
            final_message: Optional message to show briefly before clearing
        """
        with self._lock:
            if operation_id in self.loading_states:
                if final_message:
                    self.loading_states[operation_id].message = final_message
                    self.loading_states[operation_id].active = False
                    # Keep it visible briefly
                    threading.Timer(0.5, lambda: self._remove_operation(operation_id)).start()
                else:
                    del self.loading_states[operation_id]
                
                # Stop animation thread if no more operations
                if not any(state.active for state in self.loading_states.values()):
                    self._stop_event.set()
    
    def _remove_operation(self, operation_id: str):
        """Remove an operation from tracking."""
        with self._lock:
            if operation_id in self.loading_states:
                del self.loading_states[operation_id]
    
    def update_message(self, operation_id: str, new_message: str):
        """Update the message for a running operation."""
        with self._lock:
            if operation_id in self.loading_states:
                self.loading_states[operation_id].message = new_message
    
    def get_display_text(self) -> Optional[str]:
        """Get the current display text for all active spinners."""
        with self._lock:
            if not self.loading_states:
                return None
            
            lines = []
            for state in self.loading_states.values():
                if state.active:
                    frame = self.frames[state.spinner_index % len(self.frames)]
                    elapsed = time.time() - state.start_time
                    elapsed_str = f" ({elapsed:.1f}s)" if elapsed > 2.0 else ""
                    lines.append(f"{frame} {state.message}{elapsed_str}")
                else:
                    # Show final message without spinner
                    lines.append(f"✓ {state.message}")
            
            return '\n'.join(lines) if lines else None
    
    def _animate(self):
        """Animation thread that updates spinner frames."""
        while not self._stop_event.is_set():
            try:
                app = get_app()
                if app and app.is_running:
                    with self._lock:
                        # Update spinner indices
                        for state in self.loading_states.values():
                            if state.active:
                                state.spinner_index += 1
                    
                    # Trigger UI refresh
                    app.invalidate()
                
                # Sleep for animation frame rate
                time.sleep(0.1)  # 10 FPS
                
            except Exception:
                # Ignore errors in animation thread
                pass


class LoadingContext:
    """Context manager for loading operations.
    
    Usage:
        with LoadingContext(spinner, "Checking updates...") as ctx:
            # Do some work
            ctx.update("Found 3 updates...")
            # More work
        # Automatically stops when exiting context
    """
    
    def __init__(self, spinner: LoadingSpinner, message: str):
        self.spinner = spinner
        self.message = message
        self.operation_id: Optional[str] = None
    
    def __enter__(self):
        self.operation_id = self.spinner.start(self.message)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.operation_id:
            if exc_type is None:
                self.spinner.stop(self.operation_id)
            else:
                self.spinner.stop(self.operation_id, f"❌ {self.message} failed")
    
    def update(self, message: str):
        """Update the loading message."""
        if self.operation_id:
            self.spinner.update_message(self.operation_id, message)


def run_with_spinner(
    func: Callable,
    message: str,
    spinner: Optional[LoadingSpinner] = None,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
) -> any:
    """Run a function with a loading spinner.
    
    Args:
        func: The function to run
        message: Loading message to display
        spinner: Optional spinner instance (creates one if not provided)
        success_message: Message to show on success
        error_message: Message template for errors (use {error} placeholder)
        
    Returns:
        The result of the function
        
    Raises:
        Any exception from the function
    """
    if spinner is None:
        spinner = LoadingSpinner()
    
    operation_id = spinner.start(message)
    
    try:
        result = func()
        final_msg = success_message or f"✓ {message} complete"
        spinner.stop(operation_id, final_msg)
        return result
    except Exception as e:
        if error_message:
            final_msg = error_message.format(error=str(e))
        else:
            final_msg = f"❌ {message} failed: {str(e)}"
        spinner.stop(operation_id, final_msg)
        raise


class ProgressIndicator:
    """Progress indicator for operations with known steps.
    
    AI_CONTEXT:
        Unlike spinners, progress indicators show discrete steps.
        Useful for multi-stage operations where progress is measurable.
    """
    
    def __init__(self, total_steps: int, message: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.message = message
        self.spinner = LoadingSpinner()
        self.operation_id: Optional[str] = None
    
    def start(self):
        """Start the progress indicator."""
        self.operation_id = self.spinner.start(self._get_message())
    
    def advance(self, steps: int = 1):
        """Advance the progress by a number of steps."""
        self.current_step = min(self.current_step + steps, self.total_steps)
        if self.operation_id:
            self.spinner.update_message(self.operation_id, self._get_message())
    
    def complete(self, message: Optional[str] = None):
        """Mark the operation as complete."""
        if self.operation_id:
            final_msg = message or f"✓ {self.message} complete"
            self.spinner.stop(self.operation_id, final_msg)
    
    def _get_message(self) -> str:
        """Get the current progress message."""
        percentage = (self.current_step / self.total_steps) * 100
        bar_length = 20
        filled = int(bar_length * self.current_step / self.total_steps)
        bar = '█' * filled + '░' * (bar_length - filled)
        return f"{self.message} [{bar}] {percentage:.0f}%"


# Global spinner instance for convenience
_global_spinner = None


def get_spinner() -> LoadingSpinner:
    """Get the global spinner instance."""
    global _global_spinner
    if _global_spinner is None:
        _global_spinner = LoadingSpinner()
    return _global_spinner


def show_loading(message: str) -> str:
    """Show a loading message using the global spinner."""
    return get_spinner().start(message)


def hide_loading(operation_id: str, final_message: Optional[str] = None):
    """Hide a loading message."""
    get_spinner().stop(operation_id, final_message)