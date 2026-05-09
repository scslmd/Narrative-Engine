"""Run API migration verification checks and emit a markdown report."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
report_path = project_root / "docs" / "api-migration" / "verification_report.md"


def run_check(name: str, cmd: list[str], cwd: Path | None = None, timeout_s: int = 300) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout_s}s"


def main() -> None:
    checks: list[tuple[str, list[str], Path | None, int]] = [
        (
            "Backend Parallel Cluster",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "-n",
                "auto",
                "--dist=loadfile",
                "--basetemp=.tmp_xdist",
                "--ignore=tests/test_audit_logging.py",
                "--ignore=tests/test_rate_limiting.py",
                "--ignore=tests/test_smoke.py",
                "--ignore=tests/test_local_executor_manuscript_assist.py",
                "--ignore=tests/test_story_generation_e2e.py",
            ],
            None,
            300,
        ),
        (
            "Backend Serial Tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "-n",
                "0",
                "tests/test_audit_logging.py",
                "tests/test_rate_limiting.py",
                "tests/test_persistence.py::test_local_executor_persists_pipeline_step_records",
                "tests/test_smoke.py",
                "tests/test_local_executor_manuscript_assist.py",
                "tests/test_story_generation_e2e.py",
                "tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters",
            ],
            None,
            240,
        ),
        ("Frontend Lint", ["cmd", "/c", "npm.cmd", "run", "lint"], project_root / "frontend", 300),
        ("Frontend TypeCheck", ["cmd", "/c", "npm.cmd", "run", "typecheck"], project_root / "frontend", 300),
        ("Frontend Build", ["cmd", "/c", "npm.cmd", "run", "build"], project_root / "frontend", 300),
        ("Frontend Tests", ["cmd", "/c", "npm.cmd", "run", "test"], project_root / "frontend", 300),
    ]

    results: list[tuple[str, bool, str]] = []
    for name, cmd, cwd, timeout_s in checks:
        ok, output = run_check(name, cmd, cwd=cwd, timeout_s=timeout_s)
        results.append((name, ok, output))

    lines = [
        "# API Migration Verification Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| # | Check | Status | Output Summary |",
        "|---|---|---|---|",
    ]
    for idx, (name, ok, output) in enumerate(results, 1):
        status = "PASS" if ok else "FAIL"
        summary = output[:200].replace("\n", " ").replace("|", "\\|")
        lines.append(f"| {idx} | {name} | {status} | {summary} |")

    all_passed = all(ok for _, ok, _ in results)
    lines.extend(
        [
            "",
            "## Overall",
            "",
            f"Result: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}")
    raise SystemExit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
