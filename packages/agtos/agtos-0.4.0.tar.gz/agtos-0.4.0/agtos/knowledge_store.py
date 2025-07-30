"""Knowledge store for caching and managing acquired knowledge.

This module provides persistent storage for CLI, API, and package knowledge
to avoid repeated discovery and enable knowledge sharing.
"""
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import hashlib


class KnowledgeStore:
    """SQLite-based storage for acquired knowledge."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the knowledge store."""
        if db_path is None:
            # Default to user's home directory
            db_path = Path.home() / ".agtos" / "knowledge.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main knowledge table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    metadata TEXT,
                    UNIQUE(type, name)
                )
            """)
            
            # Examples table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    example TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_type_name ON knowledge(type, name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_expires ON knowledge(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_examples_type_name ON examples(type, name)")
            
            conn.commit()
    
    def store(self, type: str, name: str, data: Dict[str, Any], 
              source: str = "unknown", ttl_hours: int = 720,
              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store knowledge in the database."""
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge 
                    (type, name, data, source, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    type,
                    name,
                    json.dumps(data),
                    source,
                    expires_at,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing knowledge: {e}", file=sys.stderr)
            return False
    
    def retrieve(self, type: str, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve knowledge from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT data, source, created_at, expires_at, metadata
                    FROM knowledge
                    WHERE type = ? AND name = ? AND expires_at > ?
                """, (type, name, datetime.now()))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "data": json.loads(row[0]),
                        "source": row[1],
                        "created_at": row[2],
                        "expires_at": row[3],
                        "metadata": json.loads(row[4]) if row[4] else None
                    }
        except Exception as e:
            print(f"Error retrieving knowledge: {e}", file=sys.stderr)
        
        return None
    
    def add_example(self, type: str, name: str, example: str,
                    description: str = "", tags: Optional[List[str]] = None) -> bool:
        """Add an example to the knowledge store."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO examples (type, name, example, description, tags)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    type,
                    name,
                    example,
                    description,
                    json.dumps(tags) if tags else None
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding example: {e}", file=sys.stderr)
            return False
    
    def get_examples(self, type: str, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get examples for a specific knowledge item."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT example, description, tags, created_at
                    FROM examples
                    WHERE type = ? AND name = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (type, name, limit))
                
                examples = []
                for row in cursor.fetchall():
                    examples.append({
                        "example": row[0],
                        "description": row[1],
                        "tags": json.loads(row[2]) if row[2] else [],
                        "created_at": row[3]
                    })
                return examples
        except Exception as e:
            print(f"Error getting examples: {e}", file=sys.stderr)
            return []
    
    def search(self, query: str, type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search knowledge by name or content.
        
        AI_CONTEXT: This search function performs a multi-field text search across
        the knowledge database. It searches in:
        - name field (exact and partial matches)
        - data field (JSON content is searched as text)
        
        The search is case-insensitive and returns results ordered by creation date
        (newest first). Results are limited to 20 entries to prevent memory issues.
        
        Key implementation details:
        - Uses SQLite's LIKE operator with % wildcards for partial matching
        - Filters out expired entries automatically (expires_at > now)
        - Returns simplified results (no full data field) for performance
        - Handles database errors gracefully by returning empty list
        
        The function is designed for interactive search where users want to find
        relevant knowledge entries quickly without loading full content.
        
        Args:
            query: Search string (will be wrapped with % for partial matching)
            type: Optional filter by knowledge type (e.g., 'cli', 'api', 'package')
        
        Returns:
            List of knowledge entries with: type, name, source, created_at
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if type:
                    cursor.execute("""
                        SELECT type, name, source, created_at
                        FROM knowledge
                        WHERE type = ? AND (name LIKE ? OR data LIKE ?)
                        AND expires_at > ?
                        ORDER BY created_at DESC
                        LIMIT 20
                    """, (type, f"%{query}%", f"%{query}%", datetime.now()))
                else:
                    cursor.execute("""
                        SELECT type, name, source, created_at
                        FROM knowledge
                        WHERE (name LIKE ? OR data LIKE ?)
                        AND expires_at > ?
                        ORDER BY created_at DESC
                        LIMIT 20
                    """, (f"%{query}%", f"%{query}%", datetime.now()))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "type": row[0],
                        "name": row[1],
                        "source": row[2],
                        "created_at": row[3]
                    })
                return results
        except Exception as e:
            print(f"Error searching knowledge: {e}", file=sys.stderr)
            return []
    
    def clean_expired(self) -> int:
        """Remove expired knowledge entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM knowledge
                    WHERE expires_at < ?
                """, (datetime.now(),))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error cleaning expired entries: {e}", file=sys.stderr)
            return 0
    
    def export(self, output_path: Path) -> bool:
        """Export the entire knowledge base."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all non-expired knowledge
                cursor.execute("""
                    SELECT type, name, data, source, created_at, expires_at, metadata
                    FROM knowledge
                    WHERE expires_at > ?
                """, (datetime.now(),))
                
                knowledge_items = []
                for row in cursor.fetchall():
                    knowledge_items.append({
                        "type": row[0],
                        "name": row[1],
                        "data": json.loads(row[2]),
                        "source": row[3],
                        "created_at": row[4],
                        "expires_at": row[5],
                        "metadata": json.loads(row[6]) if row[6] else None
                    })
                
                # Get all examples
                cursor.execute("SELECT * FROM examples")
                examples = []
                for row in cursor.fetchall():
                    examples.append({
                        "type": row[1],
                        "name": row[2],
                        "example": row[3],
                        "description": row[4],
                        "tags": json.loads(row[5]) if row[5] else [],
                        "created_at": row[6]
                    })
                
                # Create export data
                export_data = {
                    "version": "1.0",
                    "exported_at": datetime.now().isoformat(),
                    "knowledge": knowledge_items,
                    "examples": examples
                }
                
                # Write to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error exporting knowledge: {e}", file=sys.stderr)
            return False
    
    def import_from(self, input_path: Path) -> int:
        """Import knowledge from an export file."""
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            imported_count = 0
            
            # Import knowledge items
            for item in data.get("knowledge", []):
                if self.store(
                    type=item["type"],
                    name=item["name"],
                    data=item["data"],
                    source=item.get("source", "import"),
                    metadata=item.get("metadata")
                ):
                    imported_count += 1
            
            # Import examples
            for example in data.get("examples", []):
                self.add_example(
                    type=example["type"],
                    name=example["name"],
                    example=example["example"],
                    description=example.get("description", ""),
                    tags=example.get("tags", [])
                )
            
            return imported_count
        except Exception as e:
            print(f"Error importing knowledge: {e}", file=sys.stderr)
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge store."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count by type
                cursor.execute("""
                    SELECT type, COUNT(*) as count
                    FROM knowledge
                    WHERE expires_at > ?
                    GROUP BY type
                """, (datetime.now(),))
                
                type_counts = {}
                for row in cursor.fetchall():
                    type_counts[row[0]] = row[1]
                
                # Total counts
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN expires_at > ? THEN 1 END) as active,
                        COUNT(CASE WHEN expires_at <= ? THEN 1 END) as expired
                    FROM knowledge
                """, (datetime.now(), datetime.now()))
                
                total_row = cursor.fetchone()
                
                # Example count
                cursor.execute("SELECT COUNT(*) FROM examples")
                example_count = cursor.fetchone()[0]
                
                # Database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    "total_entries": total_row[0],
                    "active_entries": total_row[1],
                    "expired_entries": total_row[2],
                    "entries_by_type": type_counts,
                    "total_examples": example_count,
                    "database_size_bytes": db_size,
                    "database_path": str(self.db_path)
                }
        except Exception as e:
            print(f"Error getting stats: {e}", file=sys.stderr)
            return {}
    
    def clear_all(self) -> bool:
        """Clear all knowledge (use with caution)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM knowledge")
                cursor.execute("DELETE FROM examples")
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing knowledge: {e}", file=sys.stderr)
            return False
    
    def clear_expired(self) -> int:
        """Alias for clean_expired for backward compatibility."""
        return self.clean_expired()


# Singleton instance
_knowledge_store = None


def get_knowledge_store(db_path: Optional[Path] = None) -> KnowledgeStore:
    """Get the singleton knowledge store instance."""
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = KnowledgeStore(db_path)
    return _knowledge_store


def reset_knowledge_store():
    """Reset the knowledge store instance."""
    global _knowledge_store
    _knowledge_store = None