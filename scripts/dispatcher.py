#!/usr/bin/env python3
"""Slash Command Dispatcher

A command dispatcher that handles slash commands like /quality-check.

Usage:
    python -m dispatcher /quality-check
    python -m dispatcher /quality-check frontend
    python -m dispatcher /quality-check merge
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Dict, Callable, Any, Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SlashCommandDispatcher:
    """Dispatches slash commands to their handlers."""

    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self):
        """Register built-in commands."""
        # Register quality-check command
        self.register("quality-check", self._handle_quality_check)
        # Register help command
        self.register("help", self._handle_help)
        # Register list command
        self.register("list", self._handle_list)

    def register(self, name: str, handler: Callable):
        """Register a command handler."""
        self.commands[name] = handler

    def dispatch(self, command: str, *args, **kwargs) -> str:
        """Dispatch a command to its handler."""
        # Parse the command
        parts = command.strip().split()

        if not parts:
            return "No command provided. Use /help for available commands."

        # Get command name (remove leading /)
        cmd_part = parts[0]
        if cmd_part.startswith("/"):
            cmd_part = cmd_part[1:]

        cmd_name = cmd_part.lower()

        # Get arguments
        cmd_args = parts[1:] if len(parts) > 1 else []

        # Find handler
        if cmd_name not in self.commands:
            return f"Unknown command: {cmd_name}. Use /help for available commands."

        # Execute handler
        try:
            return self.commands[cmd_name](cmd_args, **kwargs)
        except Exception as e:
            return f"Error executing command {cmd_name}: {e}"

    def _handle_quality_check(self, args: list[str], **kwargs) -> str:
        """Handle the /quality-check command."""
        from scripts.quality_check_engine import QualityCheckSkill

        skill = QualityCheckSkill()

        # Parse arguments
        context = "general"
        files_changed = None
        adverse_only = False

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ["general", "frontend", "backend", "merge"]:
                context = arg
            elif arg == "--adverse-only":
                adverse_only = True
            elif arg == "--files":
                files_changed = args[i + 1:] if i + 1 < len(args) else []
                break
            i += 1

        # Run appropriate check
        if adverse_only:
            return skill.run_adverse_review(files_changed, context)
        else:
            return skill.run_quality_check_with_adverse_review(context, files_changed)

    def _handle_help(self, args: list[str], **kwargs) -> str:
        """Handle the /help command."""
        help_text = [
            "# Available Commands",
            "",
            "## Quality Check",
            "",
            "`/quality-check [context]` - Run quality check assessment",
            "",
            "Contexts:",
            "- `general` - General quality check (default)",
            "- `frontend` - Frontend-specific quality check",
            "- `backend` - Backend-specific quality check",
            "- `merge` - Pre-merge quality validation",
            "",
            "Options:",
            "- `--adverse-only` - Only run adverse code review",
            "- `--files file1 file2` - Specify changed files",
            "",
            "Examples:",
            "- `/quality-check` - Run general quality check",
            "- `/quality-check frontend` - Run frontend quality check",
            "- `/quality-check merge` - Run pre-merge validation",
            "- `/quality-check --adverse-only` - Only adverse review",
            "",
            "## Other Commands",
            "",
            "`/help` - Show this help message",
            "",
            "`/list` - List all available commands",
            ""
        ]
        return "\n".join(help_text)

    def _handle_list(self, args: list[str], **kwargs) -> str:
        """Handle the /list command."""
        list_text = [
            "# Available Commands",
            ""
        ]

        for cmd_name in sorted(self.commands.keys()):
            list_text.append(f"- `/{cmd_name}`")

        return "\n".join(list_text)


def main():
    parser = argparse.ArgumentParser(
        description="Slash Command Dispatcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m dispatcher /quality-check
  python -m dispatcher /quality-check frontend
  python -m dispatcher /quality-check merge
  python -m dispatcher /help
  python -m dispatcher /list
"""
    )

    parser.add_argument(
        "command",
        nargs="+",
        help="Command to execute (e.g., /quality-check frontend)"
    )

    args = parser.parse_args()

    # Create dispatcher
    dispatcher = SlashCommandDispatcher()

    # Dispatch command
    command_str = " ".join(args.command)
    result = dispatcher.dispatch(command_str)

    # Print result
    print(result)


if __name__ == "__main__":
    main()
