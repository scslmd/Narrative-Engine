#!/usr/bin/env python3
"""Quality Check CLI Entry Point.

Usage:
    qc                          # Quality check on branch diff vs codex/main
    qc --latest-commit          # Quality check files from HEAD commit
    qc --recent-fallback        # Quality check recently modified files
    qc --adverse-only           # Only run adverse review
    qc --verbose                # Show review steps and analysis summary
    qc --allow-directories app  # Expand coding files under a directory target
    qc --help                   # Show help
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Sequence

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scripts.quality_check_engine import QualityCheckSkill

# Constants
CODING_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.svelte',
    '.java', '.go', '.rs', '.rb', '.php', '.cs', '.swift',
    '.kt', '.scala', '.r', '.R', '.ipynb', '.sql', '.rkt'
}

EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', 'dist', 'build', '.opencode'
}

DEFAULT_FILE_LIMIT = 10
DEFAULT_HOURS = 24
SECONDS_PER_HOUR = 3600
DEFAULT_BASE_REF = "codex/main"


def get_recent_files(limit: int = DEFAULT_FILE_LIMIT, hours: int = DEFAULT_HOURS) -> list[str]:
    """Get the most recently modified coding files."""
    recent_files = {}
    cutoff_time = datetime.now().timestamp() - (hours * SECONDS_PER_HOUR)

    for filepath in project_root.rglob('*'):
        if not _is_valid_coding_file(filepath):
            continue

        try:
            mtime = filepath.stat().st_mtime
            if mtime > cutoff_time:
                relative_path = filepath.relative_to(project_root).as_posix()
                if relative_path not in recent_files or recent_files[relative_path] < mtime:
                    recent_files[relative_path] = mtime
        except OSError:
            continue

    sorted_files = sorted(recent_files.items(), key=lambda x: x[1], reverse=True)
    return [f[0] for f in sorted_files[:limit]]


def _run_git_command(args: Sequence[str]) -> subprocess.CompletedProcess[str] | None:
    """Run a git command from the project root and return the completed process."""
    try:
        return subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            cwd=project_root,
            check=False,
        )
    except Exception:
        return None


def _is_valid_coding_file(filepath: Path) -> bool:
    """Check if filepath is a valid coding file."""
    if not filepath.is_file():
        return False
    if filepath.suffix not in CODING_EXTENSIONS:
        return False
    if any(exclude in filepath.parts for exclude in EXCLUDE_DIRS):
        return False
    return True


def _filter_detected_files(file_paths: Sequence[str]) -> list[str]:
    """Keep only existing coding files that should be reviewed."""
    filtered: list[str] = []
    seen: set[str] = set()

    for file_path in file_paths:
        candidate = file_path.strip()
        if not candidate:
            continue

        absolute_path = project_root / candidate
        if not _is_valid_coding_file(absolute_path):
            continue

        normalized = absolute_path.relative_to(project_root).as_posix()
        if normalized in seen:
            continue

        seen.add(normalized)
        filtered.append(normalized)

    return filtered


def get_branch_diff_files(base_ref: str = DEFAULT_BASE_REF) -> list[str]:
    """Get coding files changed on the current branch relative to a base ref."""
    result = _run_git_command(["git", "diff", "--name-only", f"{base_ref}...HEAD"])
    if result is None or result.returncode != 0:
        return []
    return _filter_detected_files(result.stdout.splitlines())


def get_latest_commit_files() -> list[str]:
    """Get coding files changed in the latest commit."""
    result = _run_git_command(["git", "show", "--name-only", "--format=", "HEAD"])
    if result is None or result.returncode != 0:
        return []
    return _filter_detected_files(result.stdout.splitlines())


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="qc",
        description="Quality Check Assessment Tool - reviews the latest generated branch changes by default",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  qc                    Run quality check on branch diff vs codex/main
  qc --branch-diff      Run quality check on branch diff vs codex/main
  qc --latest-commit    Run quality check on files changed in HEAD
  qc --recent-fallback  Run quality check on recently modified coding files
  qc app/main.py        Run quality check on one specific file
  qc --verbose          Show review steps and analysis summary
  qc --allow-directories frontend/src  Expand coding files under a directory
  qc --adverse-only     Only run adverse code review
  qc --files f1 f2      Specify specific files to check
  qc --help             Show this help message
"""
    )

    _add_parser_arguments(parser)
    return parser


def _add_parser_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments to the parser."""
    parser.add_argument(
        "--adverse-only",
        action="store_true",
        help="Only run the adverse code review"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show review steps, analyzer counts, and report mode before printing the full report"
    )

    parser.add_argument(
        "--files",
        nargs="+",
        help="Specify specific files to check (overrides auto-detection)"
    )

    parser.add_argument(
        "targets",
        nargs="*",
        help="Optional file path(s) to review directly without --files"
    )

    parser.add_argument(
        "--allow-directories",
        action="store_true",
        help="Allow explicit directory targets and expand coding files recursively"
    )

    parser.add_argument(
        "--git",
        action="store_true",
        help="Legacy alias for --branch-diff"
    )

    parser.add_argument(
        "--branch-diff",
        action="store_true",
        help=f"Review files changed on the current branch relative to {DEFAULT_BASE_REF}"
    )

    parser.add_argument(
        "--latest-commit",
        action="store_true",
        help="Review files changed in the most recent commit (HEAD)"
    )

    parser.add_argument(
        "--recent-fallback",
        action="store_true",
        help="Review recently modified coding files instead of git-derived changes"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )


def handle_help_command() -> None:
    """Display help information and exit."""
    help_text = """# Quality Check Assessment Tool

Automatically detects and assesses the latest generated code changes.

## Usage

```bash
qc                    # Check branch diff vs codex/main
qc --branch-diff      # Check branch diff vs codex/main
qc --latest-commit    # Check files changed in HEAD
qc --recent-fallback  # Check recently modified coding files
qc app/main.py        # Check one specific file
qc --verbose          # Show review steps and analysis summary
qc --allow-directories frontend/src  # Expand coding files under a directory target
qc --files f1 f2      # Check specific files
qc --adverse-only     # Only adverse review
```

## Features

- **Branch-aware default**: Reviews files changed on the current branch vs `codex/main`
- **Commit-aware mode**: Can review files changed in `HEAD`
- **Recent-files fallback**: Can fall back to recently modified coding files
- **Direct file targeting**: Can review one or more explicit file paths
- **Optional directory expansion**: Can recursively expand explicit directory targets when enabled
- **Verbose tracing**: Can print what review steps ran and what the analyzer found
- **Adverse review**: Critical examination as final step
- **Universal guidelines**: Works for any coding context
"""
    print(help_text)


def normalize_explicit_files(file_paths: Sequence[str], allow_directories: bool = False) -> list[str]:
    """Normalize explicit file paths to repo-relative coding files."""
    normalized_files: list[str] = []
    seen: set[str] = set()

    for file_path in file_paths:
        candidate = Path(file_path)
        absolute_path = candidate if candidate.is_absolute() else project_root / candidate

        if not absolute_path.exists():
            raise ValueError(f"Explicit target does not exist: {file_path}")

        if absolute_path.is_dir():
            if not allow_directories:
                raise ValueError(
                    f"Directory target is not allowed without --allow-directories: {file_path}"
                )

            for nested_path in sorted(absolute_path.rglob("*")):
                if not _is_valid_coding_file(nested_path):
                    continue

                relative_nested = nested_path.relative_to(project_root).as_posix()
                if relative_nested in seen:
                    continue

                seen.add(relative_nested)
                normalized_files.append(relative_nested)
            continue

        if not _is_valid_coding_file(absolute_path):
            raise ValueError(f"Explicit target is not a supported coding file: {file_path}")

        relative_path = absolute_path.relative_to(project_root).as_posix()
        if relative_path in seen:
            continue

        seen.add(relative_path)
        normalized_files.append(relative_path)

    if not normalized_files:
        raise ValueError("No supported coding files were found in the explicit targets provided.")

    return normalized_files


def detect_files_to_check(args) -> tuple[str, list[str]]:
    """Detect which files to check based on arguments."""
    if args.files:
        return ("specified files", normalize_explicit_files(args.files, args.allow_directories))

    if args.targets:
        return ("direct file targets", normalize_explicit_files(args.targets, args.allow_directories))

    if args.latest_commit:
        files = get_latest_commit_files()
        if files:
            return ("latest commit files", files)
        print("\nNo files found in HEAD. Using recent modified coding files instead.\n")
        return ("recent modified coding files (fallback)", get_recent_files())

    if args.recent_fallback:
        return ("recent modified coding files", get_recent_files())

    if args.branch_diff or args.git:
        files = get_branch_diff_files()
        if files:
            return (f"branch diff files vs {DEFAULT_BASE_REF}", files)
        latest_commit_files = get_latest_commit_files()
        if latest_commit_files:
            print(f"\nNo branch-diff files found vs {DEFAULT_BASE_REF}. Using latest commit files instead.\n")
            return ("latest commit files (fallback)", latest_commit_files)
        print("\nNo branch-diff or latest-commit files found. Using recent modified coding files instead.\n")
        return ("recent modified coding files (fallback)", get_recent_files())

    files = get_branch_diff_files()
    if files:
        return (f"branch diff files vs {DEFAULT_BASE_REF}", files)

    latest_commit_files = get_latest_commit_files()
    if latest_commit_files:
        print(f"\nNo branch-diff files found vs {DEFAULT_BASE_REF}. Using latest commit files instead.\n")
        return ("latest commit files (fallback)", latest_commit_files)

    print("\nNo branch-diff or latest-commit files found. Using recent modified coding files instead.\n")
    return ("recent modified coding files (fallback)", get_recent_files())


def format_file_list_display(files: list[str], prefix: str) -> str:
    """Format file list for display with truncation."""
    display_files = files[:5]
    suffix = '...' if len(files) > 5 else ''
    return f"\n{prefix}: {', '.join(display_files)}{suffix}\n"


def run_quality_assessment(args, files_to_check: list[str]) -> None:
    """Run the quality assessment and display results."""
    skill = QualityCheckSkill()

    if args.verbose:
        _print_verbose_assessment_intro(args, files_to_check)
        analysis_results = skill.analyze_files(files_to_check) if files_to_check else []
        _print_verbose_analysis_summary(analysis_results)

    if args.adverse_only:
        if args.verbose:
            print("[verbose] Review mode: adverse-only")
            print("[verbose] Steps: analyze selected files -> generate concrete adverse findings -> print report\n")
        report = skill.run_adverse_review(files_to_check, "general")
    else:
        if args.verbose:
            print("[verbose] Review mode: full quality check with adverse review")
            print("[verbose] Steps: analyze selected files -> score dimensions -> list issues -> run adverse review -> print report\n")
        report = skill.run_quality_check_with_adverse_review("general", files_to_check)

    print(report)


def _print_verbose_assessment_intro(args, files_to_check: list[str]) -> None:
    """Print verbose execution details before the review report."""
    print("[verbose] scripts/qc.py verbose mode enabled")
    print(f"[verbose] Explicit files flag used: {bool(args.files)}")
    print(f"[verbose] Direct targets used: {bool(args.targets)}")
    print(f"[verbose] Directory expansion enabled: {args.allow_directories}")
    print(f"[verbose] Adverse-only mode: {args.adverse_only}")
    print(f"[verbose] File count selected: {len(files_to_check)}")


def _print_verbose_analysis_summary(analysis_results) -> None:
    """Print a compact analyzer summary for the selected files."""
    print("[verbose] Analyzer pass:")
    if not analysis_results:
        print("[verbose]   No file contents were analyzed.\n")
        return

    error_count = 0
    warning_count = 0
    info_count = 0

    for result in analysis_results:
        file_issue_count = len(result.issues)
        print(f"[verbose]   {result.file_path}: {file_issue_count} issue(s)")
        for issue in result.issues:
            if issue.severity == "error":
                error_count += 1
            elif issue.severity == "warning":
                warning_count += 1
            else:
                info_count += 1

    print(
        f"[verbose] Summary: errors={error_count}, warnings={warning_count}, info={info_count}\n"
    )


def main() -> None:
    """Main entry point for the quality check CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle help command
    if args.files and args.files[0] == '/help':
        handle_help_command()
        return
    if args.targets and args.targets[0] == '/help':
        handle_help_command()
        return

    try:
        detection_mode, files_to_check = detect_files_to_check(args)
    except ValueError as exc:
        parser.error(str(exc))
        return

    # Display which files are being checked
    _display_files_info(detection_mode, files_to_check)

    # Run quality assessment
    run_quality_assessment(args, files_to_check)


def _display_files_info(detection_mode: str, files_to_check: list[str]) -> None:
    """Display information about which files are being checked."""
    if files_to_check:
        print(format_file_list_display(files_to_check, f"Checking {detection_mode}"))
    else:
        print(f"\nNo files found for {detection_mode}. Running general quality check.\n")


if __name__ == "__main__":
    main()
