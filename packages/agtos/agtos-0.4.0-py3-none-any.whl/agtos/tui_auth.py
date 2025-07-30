"""Terminal User Interface Authentication Dialog for agtOS.

This module provides inline authentication dialogs for the TUI.

AI_CONTEXT:
    This module implements modal authentication dialogs that appear within
    the TUI without breaking the user experience. It provides:
    - Sign in dialog with email/password fields
    - Sign up dialog with email/password/invite code fields
    - Tab navigation between fields
    - Error message display
    - Visual styling with borders and proper spacing
"""

from typing import Optional, Callable, Tuple
from enum import Enum
from prompt_toolkit.layout import FloatContainer, Float, Window, FormattedTextControl, HSplit, VSplit
from prompt_toolkit.layout.containers import Container
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.key_binding import KeyBindings, focus_next, focus_previous
from prompt_toolkit.styles import Style
from prompt_toolkit.application import get_app


class AuthMode(Enum):
    """Authentication mode."""
    SIGN_IN = "sign_in"
    SIGN_UP = "sign_up"


class AuthDialog:
    """Inline authentication dialog for the TUI.
    
    AI_CONTEXT:
        This class provides a modal dialog for authentication that appears
        over the main TUI content. It handles both sign in and sign up flows
        with proper field navigation and error display.
    """
    
    def __init__(
        self,
        mode: AuthMode = AuthMode.SIGN_IN,
        on_submit: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ):
        """Initialize the auth dialog.
        
        Args:
            mode: Authentication mode (sign in or sign up)
            on_submit: Callback when form is submitted
            on_cancel: Callback when dialog is cancelled
        """
        self.mode = mode
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.error_message = ""
        self.is_visible = False
        
        # Create input fields
        self.email_field = TextArea(
            height=1,
            multiline=False,
            style="class:input",
            scrollbar=False,
            focus_on_click=True,
        )
        
        self.password_field = TextArea(
            height=1,
            multiline=False,
            password=True,
            style="class:input",
            scrollbar=False,
            focus_on_click=True,
        )
        
        self.invite_field = TextArea(
            height=1,
            multiline=False,
            style="class:input",
            scrollbar=False,
            focus_on_click=True,
        ) if mode == AuthMode.SIGN_UP else None
        
        # Create key bindings
        self.kb = self._create_key_bindings()
        
    def _create_key_bindings(self) -> KeyBindings:
        """Create key bindings for the dialog."""
        kb = KeyBindings()
        
        # Tab navigation
        kb.add('tab')(focus_next)
        kb.add('s-tab')(focus_previous)
        
        # Submit on Enter (when in last field)
        @kb.add('enter')
        def submit(event):
            # Check if we're in the last field
            current_focus = event.app.layout.current_window
            if self.mode == AuthMode.SIGN_IN:
                if current_focus == self.password_field.window:
                    self._handle_submit()
            else:  # SIGN_UP
                if current_focus == self.invite_field.window:
                    self._handle_submit()
        
        # Cancel on Escape
        @kb.add('escape')
        def cancel(event):
            self._handle_cancel()
        
        return kb
    
    def _handle_submit(self):
        """Handle form submission."""
        # Validate fields
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()
        
        if not email:
            self.error_message = "Email is required"
            return
        
        if not password:
            self.error_message = "Password is required"
            return
        
        if self.mode == AuthMode.SIGN_UP:
            invite_code = self.invite_field.text.strip()
            if not invite_code:
                self.error_message = "Invite code is required"
                return
        else:
            invite_code = None
        
        # Clear error and submit
        self.error_message = ""
        if self.on_submit:
            self.on_submit(email, password, invite_code)
    
    def _handle_cancel(self):
        """Handle dialog cancellation."""
        self.clear()
        if self.on_cancel:
            self.on_cancel()
    
    def show(self):
        """Show the dialog."""
        self.is_visible = True
        self.error_message = ""
        # Focus email field
        app = get_app()
        if app:
            app.layout.focus(self.email_field)
    
    def hide(self):
        """Hide the dialog."""
        self.is_visible = False
        self.clear()
    
    def clear(self):
        """Clear all fields."""
        self.email_field.text = ""
        self.password_field.text = ""
        if self.invite_field:
            self.invite_field.text = ""
        self.error_message = ""
    
    def set_error(self, message: str):
        """Set error message."""
        self.error_message = message
    
    def create_dialog_container(self) -> Container:
        """Create the dialog container layout."""
        # Dialog title
        title = "Sign In to agtOS" if self.mode == AuthMode.SIGN_IN else "Sign Up for agtOS"
        
        # Build field rows
        field_rows = [
            # Title
            Window(
                FormattedTextControl(
                    FormattedText([('class:dialog-title', f'  {title}  ')])
                ),
                height=1,
                align='center',
            ),
            Window(height=1),  # Spacer
            
            # Email field
            Window(
                FormattedTextControl(
                    FormattedText([('class:label', '  Email:')])
                ),
                height=1,
            ),
            VSplit([
                Window(width=2),  # Indent
                self.email_field,
                Window(width=2),  # Padding
            ]),
            Window(height=1),  # Spacer
            
            # Password field
            Window(
                FormattedTextControl(
                    FormattedText([('class:label', '  Password:')])
                ),
                height=1,
            ),
            VSplit([
                Window(width=2),  # Indent
                self.password_field,
                Window(width=2),  # Padding
            ]),
        ]
        
        # Add invite code field for sign up
        if self.mode == AuthMode.SIGN_UP:
            field_rows.extend([
                Window(height=1),  # Spacer
                Window(
                    FormattedTextControl(
                        FormattedText([('class:label', '  Invite Code:')])
                    ),
                    height=1,
                ),
                VSplit([
                    Window(width=2),  # Indent
                    self.invite_field,
                    Window(width=2),  # Padding
                ]),
            ])
        
        # Error message (if any)
        if self.error_message:
            field_rows.extend([
                Window(height=1),  # Spacer
                Window(
                    FormattedTextControl(
                        FormattedText([('class:error', f'  ⚠️  {self.error_message}')])
                    ),
                    height=1,
                    align='center',
                ),
            ])
        
        # Instructions
        field_rows.extend([
            Window(height=1),  # Spacer
            Window(
                FormattedTextControl(
                    FormattedText([
                        ('class:status', '  Tab/Shift+Tab: Navigate  Enter: Submit  Esc: Cancel')
                    ])
                ),
                height=1,
                align='center',
            ),
        ])
        
        # Create the dialog content
        dialog_content = HSplit(field_rows)
        
        # Wrap in a frame with border
        framed_dialog = Frame(
            dialog_content,
            title="",
            style="class:dialog-frame",
        )
        
        # Return the framed dialog directly
        return framed_dialog
    
    def create_float(self) -> Float:
        """Create the floating dialog element."""
        dialog_width = 60
        dialog_height = 15 if self.mode == AuthMode.SIGN_IN else 17
        
        # Create a window with specific dimensions containing the dialog
        dialog_window = Window(
            width=Dimension(preferred=dialog_width),
            height=Dimension(preferred=dialog_height),
            content=self.create_dialog_container(),
        )
        
        return Float(
            content=dialog_window,
            # Center horizontally
            left=None,
            right=None,
            # Position vertically
            top=5,
            transparent=False,
        )
    
    def get_style_extensions(self) -> dict:
        """Get style extensions for the dialog."""
        return {
            'dialog-frame': 'bg:#1a1a1a fg:#ffffff',
            'dialog-title': '#00ff00 bold',
            'label': '#00aaff',
            'input': 'bg:#2a2a2a fg:#ffffff',
            'error': '#ff5555',
        }


class AuthDialogManager:
    """Manages authentication dialogs within the TUI.
    
    AI_CONTEXT:
        This class integrates auth dialogs with the main TUI application,
        handling the display logic and authentication flow.
    """
    
    def __init__(self, auth_manager, app):
        """Initialize the dialog manager.
        
        Args:
            auth_manager: AuthManager instance for authentication
            app: The main TUI application
        """
        self.auth_manager = auth_manager
        self.app = app
        self.current_dialog = None
        self.dialog_visible = False
        
    def show_sign_in(self, on_success: Optional[Callable] = None):
        """Show the sign in dialog.
        
        Args:
            on_success: Callback when authentication succeeds
        """
        def handle_submit(email: str, password: str, invite_code: Optional[str]):
            # Attempt login
            user, error = self.auth_manager.login(email, password)
            
            if user:
                # Success - hide dialog and call success callback
                self.current_dialog.hide()
                self.dialog_visible = False
                if on_success:
                    on_success(user)
                self.app.invalidate()
            else:
                # Show error
                self.current_dialog.set_error(error or "Login failed")
                self.app.invalidate()
        
        def handle_cancel():
            self.dialog_visible = False
            self.current_dialog = None
            self.app.invalidate()
        
        # Create and show dialog
        self.current_dialog = AuthDialog(
            mode=AuthMode.SIGN_IN,
            on_submit=handle_submit,
            on_cancel=handle_cancel
        )
        self.current_dialog.show()
        self.dialog_visible = True
        self.app.invalidate()
    
    def show_sign_up(self, on_success: Optional[Callable] = None):
        """Show the sign up dialog.
        
        Args:
            on_success: Callback when authentication succeeds
        """
        def handle_submit(email: str, password: str, invite_code: Optional[str]):
            # Attempt signup
            user, error = self.auth_manager.signup_with_invite(
                email, password, invite_code or ""
            )
            
            if user:
                # Success - hide dialog and call success callback
                self.current_dialog.hide()
                self.dialog_visible = False
                if on_success:
                    on_success(user)
                self.app.invalidate()
            else:
                # Show error
                self.current_dialog.set_error(error or "Signup failed")
                self.app.invalidate()
        
        def handle_cancel():
            self.dialog_visible = False
            self.current_dialog = None
            self.app.invalidate()
        
        # Create and show dialog
        self.current_dialog = AuthDialog(
            mode=AuthMode.SIGN_UP,
            on_submit=handle_submit,
            on_cancel=handle_cancel
        )
        self.current_dialog.show()
        self.dialog_visible = True
        self.app.invalidate()
    
    def get_dialog_float(self) -> Optional[Float]:
        """Get the current dialog float if visible."""
        if self.dialog_visible and self.current_dialog:
            return self.current_dialog.create_float()
        return None
    
    def get_style_extensions(self) -> dict:
        """Get style extensions for dialogs."""
        if self.current_dialog:
            return self.current_dialog.get_style_extensions()
        return {}