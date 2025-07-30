"""Interactive tutorial system for agtOS TUI.

This module provides an interactive tutorial experience for first-time users
that teaches navigation, search, and key features of the TUI.

AI_CONTEXT:
    The tutorial system is designed to be:
    - Interactive: Users practice each action as they learn
    - Skippable: Can exit at any time with Escape
    - Repeatable: Can be accessed from the help menu
    - Progress-aware: Tracks which steps have been completed
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from pathlib import Path
from datetime import datetime
import json

from prompt_toolkit.layout import Window, FormattedTextControl, HSplit, VSplit
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.containers import Container, ConditionalContainer
from prompt_toolkit.filters import Condition

from .config import get_config_dir
from .utils import get_logger

logger = get_logger(__name__)


class TutorialStep:
    """Represents a single step in the tutorial."""
    
    def __init__(
        self,
        title: str,
        content: List[str],
        action: str,
        validation: Optional[Callable[[], bool]] = None,
        hint: Optional[str] = None,
        practice_prompt: Optional[str] = None
    ):
        """Initialize a tutorial step.
        
        Args:
            title: Step title
            content: Lines of explanation
            action: Required action to complete step
            validation: Function to validate completion
            hint: Optional hint for the user
            practice_prompt: Optional prompt for practice
        """
        self.title = title
        self.content = content
        self.action = action
        self.validation = validation
        self.hint = hint
        self.practice_prompt = practice_prompt
        self.completed = False


class TutorialManager:
    """Manages the interactive tutorial experience."""
    
    def __init__(self, app: Application):
        """Initialize tutorial manager.
        
        Args:
            app: The main TUI application
        """
        self.app = app
        self.current_step = 0
        self.tutorial_active = False
        self.progress = self._load_progress()
        self.completion_callbacks: List[Callable] = []
        
        # Tutorial visibility filter
        self.visible = Condition(lambda: self.tutorial_active)
        
        # Create tutorial steps
        self.steps = self._create_tutorial_steps()
        
        # Key bindings for tutorial
        self.kb = KeyBindings()
        self._setup_key_bindings()
    
    def _create_tutorial_steps(self) -> List[TutorialStep]:
        """Create the tutorial steps."""
        return [
            TutorialStep(
                title="Welcome to agtOS! 🎉",
                content=[
                    "agtOS is your Agent Operating System - a powerful interface",
                    "for orchestrating AI agents and automating tasks.",
                    "",
                    "This quick tutorial will show you the basics.",
                    "",
                    "You can exit anytime by pressing Escape."
                ],
                action="Press Enter to continue",
                validation=lambda: True,
                practice_prompt="Press Enter to begin your journey"
            ),
            
            TutorialStep(
                title="Navigation Basics 🧭",
                content=[
                    "Use the arrow keys to navigate:",
                    "",
                    "  ↑ Up Arrow    - Move up in the menu",
                    "  ↓ Down Arrow  - Move down in the menu",
                    "  Enter         - Select an item",
                    "  Escape        - Go back or exit",
                    "",
                    "Try it now!"
                ],
                action="Use ↓ to move down",
                validation=lambda: True,  # Will be validated by key press
                practice_prompt="Press the Down Arrow key",
                hint="Use the ↓ key on your keyboard"
            ),
            
            TutorialStep(
                title="Smart Search 🔍",
                content=[
                    "Finding what you need is easy with search:",
                    "",
                    "  /  - Start searching (from anywhere!)",
                    "",
                    "Search is fuzzy - type part of any menu item",
                    "to find it instantly across all menus.",
                    "",
                    "This is the fastest way to navigate!"
                ],
                action="Press / to search",
                validation=lambda: True,
                practice_prompt="Press the / key to activate search",
                hint="The / key is usually near your right Shift key"
            ),
            
            TutorialStep(
                title="Primary Actions 🚀",
                content=[
                    "The most important menu items:",
                    "",
                    "1. 'Open Claude' - Launch the AI orchestrator",
                    "   This is where the magic happens!",
                    "",
                    "2. 'Browse Workflows' - Pre-built automation",
                    "   Complex tasks made simple",
                    "",
                    "3. 'Configure Credentials' - API keys & auth",
                    "   Securely connect to services"
                ],
                action="Explore these after the tutorial",
                validation=lambda: True,
                practice_prompt="Press Enter to continue"
            ),
            
            TutorialStep(
                title="Understanding Costs 💰",
                content=[
                    "Some menu items show cost information:",
                    "",
                    "  • $0.25/1K tokens - API-based pricing",
                    "  • Free (local) - Runs on your machine",
                    "",
                    "Use 'View Agent Costs' for detailed pricing.",
                    "",
                    "Pro tip: Local agents are free but need",
                    "more setup. Cloud agents work instantly."
                ],
                action="Remember to check costs",
                validation=lambda: True,
                practice_prompt="Press Enter to continue"
            ),
            
            TutorialStep(
                title="Getting Help 📚",
                content=[
                    "Help is always available:",
                    "",
                    "  • Bottom bar shows current shortcuts",
                    "  • 'Help & Documentation' in main menu",
                    "  • 'Show Tutorial' to replay this guide",
                    "",
                    "The search feature (/) is your best friend!",
                    "Try searching for 'help' or 'tutorial'."
                ],
                action="You're ready to go!",
                validation=lambda: True,
                practice_prompt="Press Enter to complete the tutorial"
            ),
        ]
    
    def _setup_key_bindings(self):
        """Set up tutorial-specific key bindings."""
        # These will be merged with main app bindings
        
        @self.kb.add('escape', filter=self.visible)
        def exit_tutorial(event):
            self.exit_tutorial()
        
        @self.kb.add('enter', filter=self.visible)
        def next_step(event):
            if self.current_step < len(self.steps) - 1:
                self.complete_current_step()
            else:
                self.complete_tutorial()
        
        @self.kb.add('down', filter=self.visible)
        def handle_down(event):
            # For the navigation step
            if self.current_step == 1:  # Navigation basics step
                self.complete_current_step()
        
        @self.kb.add('/', filter=self.visible)
        def handle_search(event):
            # For the search step
            if self.current_step == 2:  # Search step
                self.complete_current_step()
    
    def start_tutorial(self, force: bool = False):
        """Start the interactive tutorial.
        
        Args:
            force: Force tutorial even if completed before
        """
        if not force and self.progress.get("completed", False):
            # Tutorial was completed before
            return
        
        self.tutorial_active = True
        self.current_step = 0
        self.app.invalidate()
    
    def complete_current_step(self):
        """Mark current step as completed and move to next."""
        if self.current_step < len(self.steps):
            self.steps[self.current_step].completed = True
            self.current_step += 1
            
            # Save progress
            self.progress["last_step"] = self.current_step
            self._save_progress()
            
            self.app.invalidate()
    
    def complete_tutorial(self):
        """Complete the tutorial."""
        self.progress["completed"] = True
        self.progress["completed_at"] = datetime.now().isoformat()
        self._save_progress()
        
        # Mark as not first run
        self._mark_not_first_run()
        
        # Run completion callbacks
        for callback in self.completion_callbacks:
            callback()
        
        self.exit_tutorial()
    
    def exit_tutorial(self):
        """Exit the tutorial."""
        self.tutorial_active = False
        self.app.invalidate()
    
    def on_completion(self, callback: Callable):
        """Register a callback for tutorial completion."""
        self.completion_callbacks.append(callback)
    
    def get_tutorial_overlay(self) -> Optional[Container]:
        """Get the tutorial overlay container.
        
        Returns:
            Container for tutorial overlay or None if not active
        """
        if not self.tutorial_active or self.current_step >= len(self.steps):
            return None
        
        step = self.steps[self.current_step]
        
        # Build tutorial content
        lines = []
        
        # Progress indicator
        progress = f"Step {self.current_step + 1} of {len(self.steps)}"
        lines.append(('class:tutorial.progress', f"  {progress}  "))
        lines.append(('', '\n\n'))
        
        # Title
        lines.append(('class:tutorial.title', f"  {step.title}  "))
        lines.append(('', '\n\n'))
        
        # Content
        for line in step.content:
            lines.append(('class:tutorial.content', f"  {line}  "))
            lines.append(('', '\n'))
        
        lines.append(('', '\n'))
        
        # Practice prompt
        if step.practice_prompt:
            lines.append(('class:tutorial.prompt', f"  ▶ {step.practice_prompt}  "))
            lines.append(('', '\n'))
        
        # Hint
        if step.hint and self.current_step > 0:  # Don't show hint on first step
            lines.append(('', '\n'))
            lines.append(('class:tutorial.hint', f"  💡 Hint: {step.hint}  "))
            lines.append(('', '\n'))
        
        # Navigation help
        lines.append(('', '\n'))
        lines.append(('class:tutorial.nav', "  Press Escape to exit tutorial  "))
        
        # Create window with border
        content = Window(
            FormattedTextControl(FormattedText(lines)),
            style='class:tutorial.window',
            height=Dimension(min=15, max=25),
            width=Dimension(min=60, max=80),
        )
        
        # Center the tutorial window
        return VSplit([
            Window(width=Dimension(weight=1)),  # Left padding
            HSplit([
                Window(height=Dimension(weight=1)),  # Top padding
                content,
                Window(height=Dimension(weight=1)),  # Bottom padding
            ]),
            Window(width=Dimension(weight=1)),  # Right padding
        ])
    
    def get_style_dict(self) -> Dict[str, str]:
        """Get tutorial-specific styles."""
        return {
            'tutorial.window': 'bg:#1a1a1a #ffffff',
            'tutorial.progress': '#888888',
            'tutorial.title': '#00ff00 bold',
            'tutorial.content': '#ffffff',
            'tutorial.prompt': '#00aaff bold',
            'tutorial.hint': '#ffaa00 italic',
            'tutorial.nav': '#888888 italic',
        }
    
    def _load_progress(self) -> Dict[str, Any]:
        """Load tutorial progress from disk."""
        progress_file = get_config_dir() / "tutorial_progress.json"
        
        if progress_file.exists():
            try:
                with open(progress_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load tutorial progress: {e}")
        
        return {}
    
    def _save_progress(self):
        """Save tutorial progress to disk."""
        progress_file = get_config_dir() / "tutorial_progress.json"
        
        try:
            with open(progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tutorial progress: {e}")
    
    def _mark_not_first_run(self):
        """Mark that this is not the first run."""
        first_run_file = get_config_dir() / ".first_run"
        
        # Remove the file to indicate not first run
        if first_run_file.exists():
            try:
                first_run_file.unlink()
            except Exception as e:
                logger.error(f"Failed to remove first run marker: {e}")


def is_first_run() -> bool:
    """Check if this is the first run of agtOS.
    
    Returns:
        True if first run, False otherwise
    """
    first_run_file = get_config_dir() / ".first_run"
    config_dir = get_config_dir()
    
    # Check if config directory is new (less than 2 files)
    if not config_dir.exists() or len(list(config_dir.iterdir())) < 2:
        # Create first run marker
        first_run_file.touch()
        return True
    
    # Check for explicit first run marker
    return first_run_file.exists()


def create_first_run_marker():
    """Create a marker file for first run."""
    first_run_file = get_config_dir() / ".first_run"
    first_run_file.touch()


def reset_tutorial():
    """Reset tutorial progress for testing."""
    progress_file = get_config_dir() / "tutorial_progress.json"
    if progress_file.exists():
        progress_file.unlink()
    
    # Recreate first run marker
    create_first_run_marker()