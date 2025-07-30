"""Context preservation module for agtos.

This module provides a SQLite-based context manager for storing and retrieving
conversation history, tokens, and project-specific contexts. It integrates with
the existing credential providers for secure token storage.

AI_CONTEXT: This module manages conversation persistence across sessions,
storing contexts in SQLite with secure token storage via keychain integration.
Key features include project-specific contexts, auto-save/restore, and
integration with existing credential providers.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from ..config import get_config_dir
from ..providers.keychain import KeychainProvider
from ..utils import get_logger

logger = get_logger(__name__)

# Configure SQLite to use ISO format for datetime to avoid deprecation warning
sqlite3.register_adapter(datetime, lambda val: val.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda val: datetime.fromisoformat(val.decode()))


class ContextManager:
    """Manages conversation contexts and secure token storage.
    
    AI_CONTEXT: Central class for persisting conversation state across sessions.
    Uses SQLite for structured data storage and keychain for secure tokens.
    Supports project-specific contexts and automatic save/restore functionality.
    """
    
    def __init__(self, project_name: Optional[str] = None):
        """Initialize the ContextManager.
        
        Args:
            project_name: Optional project name for context isolation.
                         If not provided, uses a global context.
        
        AI_CONTEXT: Creates SQLite database in config directory and initializes
        tables for conversations, tokens, and preferences. Project name enables
        context isolation between different projects.
        """
        self.project_name = project_name or "global"
        self.db_path = get_config_dir() / "contexts.db"
        self.keychain = KeychainProvider()
        
        # Ensure config directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Only log if not in quiet mode
        if not os.environ.get('AGTOS_QUIET'):
            logger.info(f"ContextManager initialized for project: {self.project_name}")
    
    def _init_database(self) -> None:
        """Initialize the SQLite database schema.
        
        AI_CONTEXT: Creates three tables:
        1. conversations: Stores conversation history with timestamps
        2. tokens: Stores token metadata (actual tokens in keychain)
        3. preferences: Stores project-specific preferences
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_name, conversation_id, id)
                )
            """)
            
            # Tokens table (metadata only, actual tokens in keychain)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    token_name TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_name, token_name)
                )
            """)
            
            # Preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_name, key)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_project 
                ON conversations(project_name, conversation_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tokens_project 
                ON tokens(project_name, token_name)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections.
        
        AI_CONTEXT: Ensures proper connection handling with automatic
        rollback on errors and cleanup on exit.
        """
        conn = sqlite3.connect(str(self.db_path), detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save_context(self, conversation_id: str, messages: List[Dict[str, Any]]) -> None:
        """Save conversation context to the database.
        
        Args:
            conversation_id: Unique identifier for the conversation
            messages: List of message dictionaries with 'role' and 'content'
        
        AI_CONTEXT: Saves each message in the conversation with metadata.
        Automatically timestamps entries and handles duplicate prevention.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear existing messages for this conversation
                cursor.execute("""
                    DELETE FROM conversations 
                    WHERE project_name = ? AND conversation_id = ?
                """, (self.project_name, conversation_id))
                
                # Insert new messages
                for message in messages:
                    metadata = json.dumps({
                        k: v for k, v in message.items() 
                        if k not in ['role', 'content']
                    })
                    
                    cursor.execute("""
                        INSERT INTO conversations 
                        (project_name, conversation_id, role, content, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        self.project_name,
                        conversation_id,
                        message.get('role', 'user'),
                        message.get('content', ''),
                        metadata if metadata != '{}' else None
                    ))
                
                conn.commit()
                logger.info(f"Saved {len(messages)} messages for conversation {conversation_id}")
                
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            raise
    
    def restore_context(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Restore conversation context from the database.
        
        Args:
            conversation_id: Unique identifier for the conversation
        
        Returns:
            List of message dictionaries with role, content, and metadata
        
        AI_CONTEXT: Retrieves all messages for a conversation in chronological
        order, reconstructing metadata from JSON storage.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT role, content, metadata, created_at
                    FROM conversations
                    WHERE project_name = ? AND conversation_id = ?
                    ORDER BY id ASC
                """, (self.project_name, conversation_id))
                
                messages = []
                for row in cursor.fetchall():
                    message = {
                        'role': row['role'],
                        'content': row['content'],
                        'timestamp': row['created_at']
                    }
                    
                    # Merge metadata if present
                    if row['metadata']:
                        metadata = json.loads(row['metadata'])
                        message.update(metadata)
                    
                    messages.append(message)
                
                logger.info(f"Restored {len(messages)} messages for conversation {conversation_id}")
                return messages
                
        except Exception as e:
            logger.error(f"Failed to restore context: {e}")
            return []
    
    def save_token(self, token_name: str, token_value: str, 
                   service_name: str, expires_at: Optional[datetime] = None) -> None:
        """Save a secure token using keychain storage.
        
        Args:
            token_name: Unique name for the token
            token_value: The actual token value (stored in keychain)
            service_name: Service this token is for (e.g., 'openai', 'github')
            expires_at: Optional expiration timestamp
        
        AI_CONTEXT: Stores token metadata in SQLite but actual token value
        in system keychain for security. Integrates with KeychainProvider.
        """
        try:
            # Store token in keychain
            keychain_key = f"{self.project_name}_{token_name}"
            self.keychain.set_secret(keychain_key, token_value)
            
            # Store metadata in database
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO tokens 
                    (project_name, token_name, service_name, expires_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (self.project_name, token_name, service_name, expires_at))
                
                conn.commit()
                logger.info(f"Saved token {token_name} for service {service_name}")
                
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            raise
    
    def get_token(self, token_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Retrieve a token and its metadata.
        
        Args:
            token_name: Name of the token to retrieve
        
        Returns:
            Tuple of (token_value, metadata) or None if not found
        
        AI_CONTEXT: Retrieves token from keychain and metadata from SQLite.
        Checks expiration and returns None for expired tokens.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT service_name, expires_at, created_at, updated_at
                    FROM tokens
                    WHERE project_name = ? AND token_name = ?
                """, (self.project_name, token_name))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Check if token is expired
                if row['expires_at'] is not None:
                    if isinstance(row['expires_at'], str):
                        expires = datetime.fromisoformat(row['expires_at'])
                    else:
                        expires = row['expires_at']
                    if expires < datetime.now():
                        logger.warning(f"Token {token_name} has expired")
                        return None
                
                # Retrieve token from keychain
                keychain_key = f"{self.project_name}_{token_name}"
                token_value = self.keychain.get_secret(keychain_key)
                
                if not token_value:
                    return None
                
                metadata = {
                    'service_name': row['service_name'],
                    'expires_at': row['expires_at'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                
                return (token_value, metadata)
                
        except Exception as e:
            logger.error(f"Failed to retrieve token: {e}")
            return None
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a project-specific preference.
        
        Args:
            key: Preference key
            value: Preference value (will be JSON serialized)
        
        AI_CONTEXT: Stores arbitrary preferences as JSON-serialized values.
        Useful for persisting user settings, API endpoints, or feature flags.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                value_json = json.dumps(value)
                cursor.execute("""
                    INSERT OR REPLACE INTO preferences 
                    (project_name, key, value, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (self.project_name, key, value_json))
                
                conn.commit()
                logger.debug(f"Set preference {key} for project {self.project_name}")
                
        except Exception as e:
            logger.error(f"Failed to set preference: {e}")
            raise
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a project-specific preference.
        
        Args:
            key: Preference key
            default: Default value if preference not found
        
        Returns:
            The preference value or default
        
        AI_CONTEXT: Retrieves and deserializes preference values.
        Returns default if key not found or deserialization fails.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT value FROM preferences
                    WHERE project_name = ? AND key = ?
                """, (self.project_name, key))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row['value'])
                
                return default
                
        except Exception as e:
            logger.error(f"Failed to get preference: {e}")
            return default
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations for the current project.
        
        Returns:
            List of conversation metadata dictionaries
        
        AI_CONTEXT: Returns summary of all conversations including ID,
        message count, and last activity timestamp.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        conversation_id,
                        COUNT(*) as message_count,
                        MIN(created_at) as started_at,
                        MAX(created_at) as last_activity
                    FROM conversations
                    WHERE project_name = ?
                    GROUP BY conversation_id
                    ORDER BY last_activity DESC
                """, (self.project_name,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'conversation_id': row['conversation_id'],
                        'message_count': row['message_count'],
                        'started_at': row['started_at'],
                        'last_activity': row['last_activity']
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages.
        
        Args:
            conversation_id: ID of conversation to delete
        
        Returns:
            True if deleted, False otherwise
        
        AI_CONTEXT: Permanently removes all messages for a conversation.
        Does not affect tokens or preferences.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM conversations
                    WHERE project_name = ? AND conversation_id = ?
                """, (self.project_name, conversation_id))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    logger.info(f"Deleted conversation {conversation_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False
    
    def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from database and keychain.
        
        Returns:
            Number of tokens cleaned up
        
        AI_CONTEXT: Maintenance method to remove expired tokens.
        Cleans both database entries and keychain storage.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Find expired tokens
                cursor.execute("""
                    SELECT token_name, service_name
                    FROM tokens
                    WHERE project_name = ? 
                    AND expires_at IS NOT NULL 
                    AND expires_at < CURRENT_TIMESTAMP
                """, (self.project_name,))
                
                expired_tokens = cursor.fetchall()
                
                # Clean up each expired token
                for token in expired_tokens:
                    keychain_key = f"{self.project_name}_{token['token_name']}"
                    try:
                        self.keychain.delete_secret(keychain_key)
                    except Exception:
                        pass  # Token might already be gone
                
                # Remove from database
                cursor.execute("""
                    DELETE FROM tokens
                    WHERE project_name = ? 
                    AND expires_at IS NOT NULL 
                    AND expires_at < CURRENT_TIMESTAMP
                """, (self.project_name,))
                
                cleaned = cursor.rowcount
                conn.commit()
                
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired tokens")
                
                return cleaned
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0