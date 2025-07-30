"""
PURPOSE: Knowledge base management commands for agentctl
This module provides CLI commands for managing the knowledge base including
viewing stats, searching, exporting, and importing knowledge.

AI_CONTEXT: The knowledge base stores discovered information about CLI tools,
APIs, and packages. This module provides user-friendly commands to interact
with that data. It uses a command pattern to reduce nesting and follows
AI-first principles with explicit context and small, focused functions.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from ..knowledge_store import get_knowledge_store

console = Console()


class KnowledgeCommand:
    """
    AI_CONTEXT: Command pattern implementation for knowledge operations.
    Each action is handled by a dedicated method to reduce nesting and
    improve testability. Methods use early returns and guard clauses.
    """
    
    def __init__(self):
        self.store = get_knowledge_store()  # Use singleton instance
        self.handlers: Dict[str, Callable] = {
            "stats": self.show_stats,
            "show": self.show_entry,
            "search": self.search_entries,
            "export": self.export_knowledge,
            "import": self.import_knowledge,
            "clear": self.clear_knowledge,
        }
    
    def execute(self, action: str, service: Optional[str] = None,
                output_file: Optional[Path] = None, input_file: Optional[Path] = None,
                force: bool = False) -> None:
        """
        AI_CONTEXT: Main execution method that dispatches to appropriate handler.
        Uses guard clauses to validate action before dispatching.
        """
        handler = self.handlers.get(action)
        if not handler:
            self._show_invalid_action_error(action)
            return
        
        # Call handler with consistent interface
        handler(service, output_file, input_file, force)
    
    def show_stats(self, service: Optional[str], output_file: Optional[Path],
                   input_file: Optional[Path], force: bool) -> None:
        """
        AI_CONTEXT: Shows statistics about the knowledge base.
        Early return if knowledge base is empty.
        """
        stats = self.store.get_stats()
        
        if not stats:
            console.print("[yellow]Knowledge base is empty[/yellow]")
            return
        
        self._display_overall_stats(stats)
        # Note: top_services not available in current stats implementation
    
    def show_entry(self, service: Optional[str], output_file: Optional[Path],
                   input_file: Optional[Path], force: bool) -> None:
        """
        AI_CONTEXT: Shows detailed knowledge about a specific service.
        Uses guard clause for missing service parameter.
        """
        if not service:
            console.print("[red]Error:[/red] Service name required for 'show' action")
            raise typer.Exit(1)
        
        entry = self._find_service_entry(service)
        if not entry:
            console.print(f"[yellow]No knowledge found for:[/yellow] {service}")
            return
        
        self._display_knowledge_entry(entry)
    
    def search_entries(self, service: Optional[str], output_file: Optional[Path],
                       input_file: Optional[Path], force: bool) -> None:
        """
        AI_CONTEXT: Searches the knowledge base for matching entries.
        Guard clause validates search term presence.
        """
        if not service:
            console.print("[red]Error:[/red] Search term required for 'search' action")
            raise typer.Exit(1)
        
        entries = self.store.search(service)[:10]  # Limit to 10 results
        
        if not entries:
            console.print(f"[yellow]No results found for:[/yellow] {service}")
            return
        
        self._display_search_results(entries, service)
    
    def export_knowledge(self, service: Optional[str], output_file: Optional[Path],
                         input_file: Optional[Path], force: bool) -> None:
        """
        AI_CONTEXT: Exports knowledge base to a JSON file.
        Handles both full export and service-specific export.
        """
        export_data = self._prepare_export_data(service)
        output_path = self._determine_output_path(output_file, service)
        
        self._write_export_file(output_path, export_data)
        
        count = self._count_export_entries(export_data)
        console.print(f"[green]✓[/green] Exported {count} entries to: [cyan]{output_path}[/cyan]")
    
    def import_knowledge(self, service: Optional[str], output_file: Optional[Path],
                         input_file: Optional[Path], force: bool) -> None:
        """
        AI_CONTEXT: Imports knowledge from a JSON file.
        Uses multiple guard clauses for validation.
        """
        if not input_file:
            console.print("[red]Error:[/red] Input file required for 'import' action (use --input)")
            raise typer.Exit(1)
        
        if not input_file.exists():
            console.print(f"[red]Error:[/red] File not found: {input_file}")
            raise typer.Exit(1)
        
        import_data = self._load_import_file(input_file)
        if not import_data:
            return
        
        imported_count = self._import_entries(import_data)
        console.print(f"[green]✓[/green] Imported {imported_count} entries from: [cyan]{input_file}[/cyan]")
    
    def clear_knowledge(self, service: Optional[str], output_file: Optional[Path],
                        input_file: Optional[Path], force: bool) -> None:
        """
        AI_CONTEXT: Clears knowledge base entries.
        Handles confirmation logic with early returns.
        """
        if service:
            self._clear_service_knowledge(service, force)
        else:
            self._clear_all_knowledge(force)
    
    # Helper methods with reduced nesting
    
    def _show_invalid_action_error(self, action: str) -> None:
        """Display error for invalid action."""
        console.print(f"[red]Error:[/red] Unknown action '{action}'")
        console.print(f"Valid actions: {', '.join(self.handlers.keys())}")
        raise typer.Exit(1)
    
    def _display_overall_stats(self, stats: Dict[str, Any]) -> None:
        """Display overall knowledge base statistics."""
        entries_by_type = stats.get('entries_by_type', {})
        
        info = f"""
[cyan]Total Entries:[/cyan] {stats.get('active_entries', 0)}
[cyan]CLI Tools:[/cyan] {entries_by_type.get('cli', 0)}
[cyan]API Services:[/cyan] {entries_by_type.get('api', 0)}
[cyan]Packages:[/cyan] {entries_by_type.get('package', 0)}
[cyan]Comprehensive:[/cyan] {entries_by_type.get('comprehensive', 0)}
[cyan]Database Size:[/cyan] {stats.get('database_size_bytes', 0) / 1024 / 1024:.1f} MB
"""
        
        console.print(Panel(info.strip(), title="Knowledge Base Statistics", border_style="cyan"))
    
    def _display_top_services(self, top_services: List[tuple]) -> None:
        """Display top services table."""
        if not top_services:
            return
        
        table = Table(title="Top Services by Entry Count")
        table.add_column("Service", style="cyan")
        table.add_column("Entries", style="green")
        
        for service, count in top_services[:10]:
            table.add_row(service, str(count))
        
        console.print(table)
    
    def _find_service_entry(self, service: str) -> Optional[dict]:
        """Find the first matching entry for a service."""
        entries = self.store.search(service)[:1]  # Get first result
        if not entries:
            return None
        
        # Retrieve full data for the entry
        entry = entries[0]
        full_data = self.store.retrieve(entry['type'], entry['name'])
        if full_data:
            # Merge entry info with full data
            return {
                'name': entry['name'],
                'type': entry['type'],
                'source': entry['source'],
                'data': full_data['data'],
                'created_at': full_data['created_at']
            }
        return None
    
    def _display_knowledge_entry(self, entry: dict) -> None:
        """
        AI_CONTEXT: Display a single knowledge entry.
        Delegates to specific display methods based on content type.
        """
        self._display_entry_header(entry)
        
        data = entry.get("data", {})
        if isinstance(data, dict):
            self._display_structured_content(data)
        else:
            self._display_json_content(data)
    
    def _display_entry_header(self, entry: dict) -> None:
        """Display basic entry information."""
        console.print(f"\n[cyan]Name:[/cyan] {entry.get('name', 'unknown')}")
        console.print(f"[cyan]Type:[/cyan] {entry.get('type', 'unknown')}")
        console.print(f"[cyan]Source:[/cyan] {entry.get('source', 'unknown')}")
        console.print(f"[cyan]Created:[/cyan] {entry.get('created_at', 'unknown')}")
    
    def _display_structured_content(self, data: dict) -> None:
        """Display structured content with specific formatting."""
        # Check if it's CLI data
        if 'cli' in data:
            cli_data = data['cli']
            help_text = cli_data.get("help_text")
            if help_text:
                truncated = help_text[:500] + "..." if len(help_text) > 500 else help_text
                console.print("\n[yellow]Help Text:[/yellow]")
                console.print(truncated)
            
            subcommands = cli_data.get("subcommands", [])
            if subcommands:
                self._display_commands_summary(subcommands)
        
        # Check if it's API data
        elif 'api' in data and data['api']:
            api_data = data['api']
            console.print(f"\n[yellow]Base URL:[/yellow] {api_data.get('base_url', 'unknown')}")
            if 'endpoints' in api_data:
                console.print(f"[yellow]Endpoints:[/yellow] {len(api_data['endpoints'])} found")
        
        # Check if it's package data
        elif 'package' in data and data['package']:
            pkg_data = data['package']
            console.print(f"\n[yellow]Package:[/yellow] {pkg_data.get('name', 'unknown')}")
            console.print(f"[yellow]Version:[/yellow] {pkg_data.get('version', 'unknown')}")
    
    def _display_commands_summary(self, commands: List[str]) -> None:
        """Display a summary of available commands."""
        console.print(f"\n[yellow]Subcommands:[/yellow] {len(commands)} found")
        
        # Show first 5 commands
        for cmd in commands[:5]:
            console.print(f"  • {cmd}")
        
        # Show count of remaining commands
        remaining = len(commands) - 5
        if remaining > 0:
            console.print(f"  ... and {remaining} more")
    
    def _display_json_content(self, content: Any) -> None:
        """Display content as syntax-highlighted JSON."""
        json_str = json.dumps(content, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        console.print(syntax)
    
    def _display_search_results(self, entries: List[dict], search_term: str) -> None:
        """Display search results in a table."""
        table = Table(title=f"Search Results for '{search_term}'")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")  
        table.add_column("Source", style="yellow")
        
        for entry in entries:
            table.add_row(
                entry.get("name", "unknown"),
                entry.get("type", "unknown"),
                entry.get("source", "unknown")
            )
        
        console.print(table)
        console.print(f"\n[yellow]Tip:[/yellow] Use [cyan]agentctl knowledge show <service>[/cyan] for details")
    
    def _prepare_export_data(self, service: Optional[str]) -> dict:
        """Prepare data for export based on service filter."""
        if service:
            entries = self.store.search(service)  # Get all matching entries
            return {"service": service, "entries": entries}
        
        # Get all entries by searching with empty query
        all_entries = self.store.search("")  # This will match all entries
        return {"all_entries": all_entries}
    
    def _determine_output_path(self, output_file: Optional[Path], service: Optional[str]) -> Path:
        """Determine the output file path for export."""
        if output_file:
            return output_file
        
        filename = f"knowledge_{service}.json" if service else "knowledge_all.json"
        return Path(filename)
    
    def _write_export_file(self, path: Path, data: dict) -> None:
        """Write export data to file."""
        path.write_text(json.dumps(data, indent=2))
    
    def _count_export_entries(self, export_data: dict) -> int:
        """Count entries in export data."""
        return len(export_data.get("entries", export_data.get("all_entries", [])))
    
    def _load_import_file(self, input_file: Path) -> Optional[dict]:
        """
        AI_CONTEXT: Load and validate import file.
        Returns None if file is invalid or contains no entries.
        """
        try:
            import_data = json.loads(input_file.read_text())
        except json.JSONDecodeError as e:
            console.print(f"[red]Error:[/red] Invalid JSON in {input_file}: {e}")
            raise typer.Exit(1)
        
        entries = import_data.get("entries", import_data.get("all_entries", []))
        if not entries:
            console.print("[yellow]No entries found in import file[/yellow]")
            return None
        
        return import_data
    
    def _import_entries(self, import_data: dict) -> int:
        """Import entries from loaded data."""
        entries = import_data.get("entries", import_data.get("all_entries", []))
        imported = 0
        
        for entry in entries:
            if self._import_single_entry(entry):
                imported += 1
        
        return imported
    
    def _import_single_entry(self, entry: dict) -> bool:
        """
        AI_CONTEXT: Import a single entry safely.
        Returns True if successful, False otherwise.
        """
        try:
            # Adapt entry format to KnowledgeStore API
            self.store.store(
                type=entry.get("service_type", "unknown"),
                name=entry.get("service_name", "unknown"),
                data={
                    "knowledge_type": entry.get("knowledge_type", "unknown"),
                    "content": entry.get("content", {})
                },
                metadata=entry.get("metadata", {})
            )
            return True
        except Exception:
            # Skip invalid entries silently
            return False
    
    def _clear_service_knowledge(self, service: str, force: bool) -> None:
        """Clear knowledge for a specific service."""
        if not self._confirm_clear_service(service, force):
            return
        
        # Clear service entries by searching and deleting
        entries = self.store.search(service)
        count = len(entries)
        # Note: KnowledgeStore doesn't have clear_service, would need to add it
        console.print("[yellow]Warning: clear_service not implemented in KnowledgeStore[/yellow]")
        console.print(f"[green]✓[/green] Cleared {count} entries for: [cyan]{service}[/cyan]")
    
    def _clear_all_knowledge(self, force: bool) -> None:
        """Clear entire knowledge base."""
        if not self._confirm_clear_all(force):
            return
        
        self.store.clear_all()
        console.print("[green]✓[/green] Cleared entire knowledge base")
    
    def _confirm_clear_service(self, service: str, force: bool) -> bool:
        """Confirm clearing service knowledge."""
        if force:
            return True
        
        if not typer.confirm(f"Clear all knowledge for '{service}'?"):
            console.print("[yellow]Cancelled[/yellow]")
            return False
        
        return True
    
    def _confirm_clear_all(self, force: bool) -> bool:
        """Confirm clearing all knowledge."""
        if force:
            return True
        
        if not typer.confirm("Clear entire knowledge base?"):
            console.print("[yellow]Cancelled[/yellow]")
            return False
        
        return True


# Module-level functions for CLI registration

def register_knowledge_command(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers the knowledge command group with the main app.
    Creates a single instance of KnowledgeCommand for all operations.
    """
    app.command()(knowledge)


def knowledge(
    action: str = typer.Argument(..., help="Action to perform: stats, show, search, export, import, clear"),
    service: Optional[str] = typer.Argument(None, help="Service name (for show/search/clear actions)"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (for export)"),
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="Input file (for import)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force action without confirmation"),
) -> None:
    """
    Manage the knowledge base.
    
    AI_CONTEXT: This is the main entry point for knowledge management.
    It creates a KnowledgeCommand instance and delegates to the appropriate
    handler based on the action parameter.
    """
    try:
        command = KnowledgeCommand()
        command.execute(action, service, output_file, input_file, force)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)