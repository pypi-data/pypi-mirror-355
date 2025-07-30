"""Session and context management for Meta-MCP server.

AI_CONTEXT:
    This module handles session persistence and context management for the
    Meta-MCP server. It provides methods to:
    
    - Save and restore conversation context
    - Manage authentication tokens across sessions
    - Track user preferences and service configurations
    - Clean up expired data
    
    The session management ensures continuity across server restarts and
    enables features like context preservation and workflow recording.
    
    Navigation:
    - _restore_session_context: Called during server initialization
    - _save_session_context: Called periodically and on shutdown
    - Token management methods handle auth persistence
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionMixin:
    """Mixin class containing session management methods.
    
    AI_CONTEXT: This mixin is designed to be used with MetaMCPServer.
    It provides all session and context persistence logic while keeping
    the main server class focused on core functionality.
    """
    
    def _restore_session_context(self) -> None:
        """Restore previous session context from persistence.
        
        AI_CONTEXT: Loads the last conversation, preferences, and any saved
        authentication tokens from the previous session. This enables seamless
        continuation of work across server restarts.
        
        The method attempts to restore:
        1. Last conversation ID and messages
        2. User preferences (enabled services, etc.)
        3. Authentication tokens (if not expired)
        4. Workflow recording state
        """
        try:
            # Get last conversation ID from preferences
            last_conversation_id = self.context_manager.get_preference("last_conversation_id")
            
            if last_conversation_id:
                # Restore conversation messages
                messages = self.context_manager.restore_context(last_conversation_id)
                if messages:
                    self.current_conversation_id = last_conversation_id
                    self.conversation_messages = messages
                    logger.info(f"Restored {len(messages)} messages from previous session")
                    
                    # Show helpful message about restored context
                    if self.debug:
                        logger.info(f"Restored conversation: {last_conversation_id}")
                        logger.info(f"Last activity: {messages[-1]['timestamp'] if messages else 'unknown'}")
            
            # Restore any saved API tokens
            self._restore_saved_tokens()
            
            # Restore service preferences
            saved_services = self.context_manager.get_preference("enabled_services", [])
            if saved_services:
                logger.info(f"Restored {len(saved_services)} service preferences")
                
        except Exception as e:
            logger.error(f"Failed to restore session context: {e}")
    
    def _save_session_context(self) -> None:
        """Save current session context for future restoration.
        
        AI_CONTEXT: Persists the current conversation, active services, and
        any authentication tokens. Called on graceful shutdown or periodically
        during long-running sessions.
        
        The method saves:
        1. Current conversation ID and messages
        2. List of enabled services
        3. User preferences
        4. Active authentication tokens
        
        It also performs cleanup of expired data to prevent database bloat.
        """
        try:
            # Save current conversation if any
            if self.current_conversation_id and self.conversation_messages:
                self.context_manager.save_context(
                    self.current_conversation_id,
                    self.conversation_messages
                )
                
                # Save as last active conversation
                self.context_manager.set_preference(
                    "last_conversation_id",
                    self.current_conversation_id
                )
                
                logger.info(f"Saved {len(self.conversation_messages)} messages to context")
            
            # Save enabled services
            enabled_services = list(self.registry.services.keys())
            self.context_manager.set_preference("enabled_services", enabled_services)
            
            # Save workflow recorder state if active
            if self._workflow_recorder and self._workflow_recorder.recording:
                workflow_state = {
                    "name": self._workflow_recorder.workflow_name,
                    "description": self._workflow_recorder.workflow_description,
                    "step_count": len(self._workflow_recorder.steps)
                }
                self.context_manager.set_preference("active_workflow", workflow_state)
                logger.info(f"Saved active workflow state: {workflow_state['name']}")
            
            # Cleanup expired tokens
            cleaned = self.context_manager.cleanup_expired_tokens()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired tokens")
                
        except Exception as e:
            logger.error(f"Failed to save session context: {e}")
    
    def _restore_saved_tokens(self) -> None:
        """Restore saved authentication tokens from context manager.
        
        AI_CONTEXT: Retrieves tokens saved in previous sessions and makes them
        available to the auth manager. Only non-expired tokens are restored.
        
        This method integrates with the AuthManager to ensure tokens are
        properly validated and refreshed if needed.
        """
        try:
            # Use auth manager's built-in restore functionality
            self.auth_manager.restore_tokens_from_context()
            
            # Log token restoration stats if method exists
            if hasattr(self.auth_manager, 'get_active_token_count'):
                active_tokens = self.auth_manager.get_active_token_count()
                if active_tokens > 0:
                    logger.info(f"Restored {active_tokens} active authentication tokens")
                    
        except Exception as e:
            logger.error(f"Failed to restore tokens: {e}")
    
    def _clear_session_context(self) -> None:
        """Clear the current session context.
        
        AI_CONTEXT: Used when starting a fresh session or when the user
        explicitly requests to clear context. This removes conversation
        history but preserves authentication tokens and preferences.
        """
        try:
            # Clear conversation data
            self.current_conversation_id = None
            self.conversation_messages = []
            
            # Remove last conversation preference
            self.context_manager.set_preference("last_conversation_id", None)
            
            # Clear active workflow if any
            self.context_manager.set_preference("active_workflow", None)
            
            logger.info("Cleared session context")
            
        except Exception as e:
            logger.error(f"Failed to clear session context: {e}")
    
    def _get_session_summary(self) -> dict:
        """Get a summary of the current session state.
        
        AI_CONTEXT: Provides a snapshot of the current session including
        conversation length, active services, and authentication status.
        Used for debugging and status reporting.
        
        Returns:
            Dictionary with session summary information
        """
        authenticated_services = []
        if hasattr(self.auth_manager, 'get_authenticated_services'):
            authenticated_services = self.auth_manager.get_authenticated_services()
        
        return {
            "conversation_id": self.current_conversation_id,
            "message_count": len(self.conversation_messages),
            "active_services": list(self.registry.services.keys()),
            "authenticated_services": authenticated_services,
            "cache_size": self.cache.size(),
            "uptime_seconds": int((datetime.now() - self.stats["start_time"]).total_seconds()),
            "workflow_recording": bool(self._workflow_recorder and self._workflow_recorder.recording)
        }