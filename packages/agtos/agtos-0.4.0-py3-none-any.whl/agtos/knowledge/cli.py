"""CLI knowledge acquisition for agtos.

This module provides AI-first capabilities for understanding command-line interfaces
through automated discovery, help text parsing, and pattern recognition. It enables
agentctl to learn how to use any CLI tool by extracting documentation, examples,
and usage patterns.

The CLIKnowledge class serves as the foundation for agtos's ability to create
plugins that wrap existing CLI tools, making them accessible through natural language
interfaces while preserving their full functionality.
"""
import subprocess
import re
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..knowledge_store import get_knowledge_store


class CLIKnowledge:
    """Acquire knowledge about CLI tools.
    
    This class provides methods to discover, analyze, and understand command-line
    interfaces through various techniques including help text parsing, man page
    extraction, shell completion analysis, and pattern recognition.
    
    The acquired knowledge is cached in the knowledge store for efficient reuse
    and can be used to generate plugin code that properly interfaces with the CLI.
    """
    
    def __init__(self):
        self.store = get_knowledge_store()
    
    def get_help_text(self, command: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get and parse help text from a CLI tool."""
        knowledge = {
            "command": command,
            "available": False,
            "help_text": "",
            "subcommands": [],
            "global_flags": [],
            "examples": []
        }
        
        # Check if command exists
        check = subprocess.run(["which", command], capture_output=True)
        if check.returncode != 0:
            return knowledge
        
        knowledge["available"] = True
        
        # Try different help flags
        help_flags = ["--help", "-h", "help", "-?"]
        
        for flag in help_flags:
            try:
                result = subprocess.run(
                    [command, flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    knowledge["help_text"] = result.stdout
                    break
            except:
                continue
        
        # Parse help text for common patterns
        if knowledge["help_text"]:
            # Extract subcommands
            subcommand_match = re.findall(
                r'^\s{2,}(\w+)\s+\w+.*$',
                knowledge["help_text"],
                re.MULTILINE
            )
            knowledge["subcommands"] = list(set(subcommand_match))[:20]
            
            # Extract global flags
            flag_match = re.findall(
                r'(-{1,2}[\w-]+)(?:\s+<?[\w_]+>?)?\s+\w+',
                knowledge["help_text"]
            )
            knowledge["global_flags"] = list(set(flag_match))[:20]
            
            # Extract examples
            example_section = re.search(
                r'(?:Examples?|EXAMPLES?):(.*?)(?:\n\n|$)',
                knowledge["help_text"],
                re.DOTALL
            )
            if example_section:
                examples = re.findall(
                    r'(?:^|\n)\s*(?:\$\s*)?(' + command + r'[^\n]+)',
                    example_section.group(1)
                )
                knowledge["examples"] = examples[:5]
        
        return knowledge
    
    def get_subcommand_help(self, command: str, subcommand: str) -> str:
        """Get help for a specific subcommand."""
        try:
            result = subprocess.run(
                [command, subcommand, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass
        return ""
    
    def discover_cli_patterns(self, command: str, use_cache: bool = True) -> Dict[str, Any]:
        """Discover common usage patterns for a CLI."""
        # Check cache first
        if use_cache:
            cached = self.store.retrieve("cli", command)
            if cached:
                return cached["data"]
        
        knowledge = self.get_help_text(command, use_cache=False)
        
        if not knowledge["available"]:
            return knowledge
        
        # Analyze subcommands for patterns
        patterns = {
            "crud_operations": [],
            "auth_required": False,
            "config_file": None,
            "common_workflows": []
        }
        
        # Check for CRUD operations
        crud_keywords = {
            "create": ["create", "add", "new", "init"],
            "read": ["list", "get", "show", "describe", "ls"],
            "update": ["update", "edit", "modify", "set"],
            "delete": ["delete", "remove", "rm", "destroy"]
        }
        
        for operation, keywords in crud_keywords.items():
            for subcommand in knowledge["subcommands"]:
                if any(keyword in subcommand.lower() for keyword in keywords):
                    patterns["crud_operations"].append({
                        "operation": operation,
                        "command": subcommand
                    })
        
        # Check for auth patterns
        auth_keywords = ["login", "auth", "token", "key", "credential"]
        if any(keyword in str(knowledge).lower() for keyword in auth_keywords):
            patterns["auth_required"] = True
        
        # Check for config file
        config_patterns = ["--config", "-c", "config-file", ".config"]
        for pattern in config_patterns:
            if pattern in knowledge["help_text"]:
                patterns["config_file"] = pattern
                break
        
        knowledge["patterns"] = patterns
        
        # Store in cache
        self.store.store(
            type="cli",
            name=command,
            data=knowledge,
            source="cli_discovery",
            ttl_hours=720  # 30 days for CLI knowledge
        )
        
        return knowledge
    
    def get_man_page(self, command: str) -> Optional[str]:
        """Get and parse man page for a command."""
        try:
            # Try to get man page
            result = subprocess.run(
                ["man", command],
                capture_output=True,
                text=True,
                env={**os.environ, "MANPAGER": "cat"}
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass
        return None
    
    def discover_command_examples(self, command: str) -> List[Dict[str, str]]:
        """Extract examples from help text and man pages."""
        examples = []
        
        # Get examples from help text
        help_knowledge = self.get_help_text(command)
        if help_knowledge.get("examples"):
            for ex in help_knowledge["examples"]:
                examples.append({
                    "command": ex,
                    "source": "help_text",
                    "description": ""
                })
        
        # Get examples from man page
        man_page = self.get_man_page(command)
        if man_page:
            # Look for EXAMPLES section
            example_section = re.search(
                r'(?:EXAMPLES?|Examples?)\n(.*?)(?:\n[A-Z]+|\Z)',
                man_page,
                re.DOTALL | re.MULTILINE
            )
            if example_section:
                # Extract command examples
                cmd_examples = re.findall(
                    r'^\s*\$?\s*(' + command + r'[^\n]+)',
                    example_section.group(1),
                    re.MULTILINE
                )
                for ex in cmd_examples[:5]:  # Limit to 5 examples
                    if ex not in [e["command"] for e in examples]:
                        examples.append({
                            "command": ex.strip(),
                            "source": "man_page",
                            "description": ""
                        })
        
        # Store examples in knowledge store
        for example in examples:
            self.store.add_example(
                type="cli",
                name=command,
                example=example["command"],
                description=example["description"],
                tags=[example["source"]]
            )
        
        return examples
    
    def analyze_cli_completions(self, command: str) -> Dict[str, Any]:
        """Analyze shell completions to discover hidden commands/options."""
        completions = {
            "bash_completion": None,
            "zsh_completion": None,
            "discovered_commands": [],
            "discovered_options": []
        }
        
        # Try to find completion files
        completion_paths = [
            f"/usr/share/bash-completion/completions/{command}",
            f"/etc/bash_completion.d/{command}",
            f"/opt/homebrew/share/bash-completion/completions/{command}",
            f"/usr/local/share/bash-completion/completions/{command}"
        ]
        
        for path in completion_paths:
            if Path(path).exists():
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                        completions["bash_completion"] = path
                        
                        # Extract commands/subcommands
                        cmd_matches = re.findall(
                            r'(?:commands?|COMMANDS?)["\']?\s*[=:]\s*["\']([^"\']+)',
                            content
                        )
                        for match in cmd_matches:
                            commands = match.split()
                            completions["discovered_commands"].extend(commands)
                        
                        # Extract options
                        opt_matches = re.findall(
                            r'--[\w-]+',
                            content
                        )
                        completions["discovered_options"].extend(opt_matches)
                        
                        break
                except:
                    pass
        
        # Deduplicate
        completions["discovered_commands"] = list(set(completions["discovered_commands"]))
        completions["discovered_options"] = list(set(completions["discovered_options"]))
        
        return completions