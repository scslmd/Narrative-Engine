#!/usr/bin/env python3
"""Run validation checks in parallel."""

from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def run_command(name: str, cmd: list[str], cwd: str | None = None) -> tuple[str, bool]:
    """Run a command and return (output, success)."""
    try:
        # Use shell=True on Windows for npm/node commands
        use_shell = sys.platform == "win32" and cmd[0] in ("npm", "node")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes per command
            shell=use_shell,
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        # Add success/failure indicator to output
        if success:
            output = f"[{name}] SUCCESS\n{output}" if output else f"[{name}] SUCCESS"
        else:
            output = f"[{name}] FAILED (exit code {result.returncode})\n{output}"
        return output, success
    except subprocess.TimeoutExpired:
        return f"[{name}] TIMEOUT after 300 seconds", False
    except Exception as e:
        return f"[{name}] ERROR: {e}", False


def main() -> int:
    """Run all validation checks in parallel."""
    print("Running validation checks in parallel...\n")

    commands = [
        ("Backend Tests", ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"], None),
        ("Frontend Lint", ["npm", "run", "lint"], "frontend"),
        ("Frontend Typecheck", ["npm", "run", "typecheck"], "frontend"),
        ("Frontend Build", ["npm", "run", "build"], "frontend"),
    ]

    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_command, name, cmd, cwd): name
            for name, cmd, cwd in commands
        }

        for future in as_completed(futures):
            name = futures[future]
            output, success = future.result()
            results.append((name, output, success))
            status = "[PASS]" if success else "[FAIL]"
            print(f"{status}: {name}\n")

    # Summary
    print("=" * 50)
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("\n[SUCCESS] All validation checks PASSED!")
        return 0
    else:
        print("\n[FAILURE] Some validation checks FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
