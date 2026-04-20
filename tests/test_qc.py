from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from scripts import qc


def _make_args(
    *,
    files: list[str] | None = None,
    targets: list[str] | None = None,
    git: bool = False,
    branch_diff: bool = False,
    latest_commit: bool = False,
    recent_fallback: bool = False,
    allow_directories: bool = False,
) -> Namespace:
    return Namespace(
        files=files,
        targets=targets or [],
        git=git,
        branch_diff=branch_diff,
        latest_commit=latest_commit,
        recent_fallback=recent_fallback,
        allow_directories=allow_directories,
        adverse_only=False,
        verbose=False,
    )


def test_get_branch_diff_files_filters_to_existing_coding_files(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(qc, "project_root", tmp_path)

    app_file = tmp_path / "app.py"
    app_file.write_text("print('ok')\n", encoding="utf-8")
    docs_file = tmp_path / "README.md"
    docs_file.write_text("# docs\n", encoding="utf-8")

    def fake_run_git_command(args: list[str]):
        class Result:
            returncode = 0
            stdout = "app.py\nREADME.md\ndeleted.ts\n"

        return Result()

    monkeypatch.setattr(qc, "_run_git_command", fake_run_git_command)

    assert qc.get_branch_diff_files() == ["app.py"]


def test_detect_files_to_check_defaults_to_branch_diff(monkeypatch) -> None:
    monkeypatch.setattr(qc, "get_branch_diff_files", lambda: ["frontend/src/App.tsx"])
    monkeypatch.setattr(qc, "get_latest_commit_files", lambda: ["scripts/qc.py"])
    monkeypatch.setattr(qc, "get_recent_files", lambda: ["tests/test_qc.py"])

    mode, files = qc.detect_files_to_check(_make_args())

    assert mode == f"branch diff files vs {qc.DEFAULT_BASE_REF}"
    assert files == ["frontend/src/App.tsx"]


def test_detect_files_to_check_uses_latest_commit_flag(monkeypatch) -> None:
    monkeypatch.setattr(qc, "get_latest_commit_files", lambda: ["scripts/qc.py"])
    monkeypatch.setattr(qc, "get_recent_files", lambda: ["tests/test_qc.py"])

    mode, files = qc.detect_files_to_check(_make_args(latest_commit=True))

    assert mode == "latest commit files"
    assert files == ["scripts/qc.py"]


def test_detect_files_to_check_falls_back_to_latest_commit_before_recent(monkeypatch) -> None:
    monkeypatch.setattr(qc, "get_branch_diff_files", lambda: [])
    monkeypatch.setattr(qc, "get_latest_commit_files", lambda: ["scripts/qc.py"])
    monkeypatch.setattr(qc, "get_recent_files", lambda: ["tests/test_qc.py"])

    mode, files = qc.detect_files_to_check(_make_args())

    assert mode == "latest commit files (fallback)"
    assert files == ["scripts/qc.py"]


def test_detect_files_to_check_falls_back_to_recent_when_git_sources_are_empty(monkeypatch) -> None:
    monkeypatch.setattr(qc, "get_branch_diff_files", lambda: [])
    monkeypatch.setattr(qc, "get_latest_commit_files", lambda: [])
    monkeypatch.setattr(qc, "get_recent_files", lambda: ["tests/test_qc.py"])

    mode, files = qc.detect_files_to_check(_make_args())

    assert mode == "recent modified coding files (fallback)"
    assert files == ["tests/test_qc.py"]


def test_normalize_explicit_files_returns_repo_relative_coding_files(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(qc, "project_root", tmp_path)

    source_file = tmp_path / "frontend" / "src" / "App.tsx"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("export function App() { return null }\n", encoding="utf-8")

    normalized = qc.normalize_explicit_files([
        "frontend/src/App.tsx",
        str(source_file),
    ])

    assert normalized == ["frontend/src/App.tsx"]


def test_detect_files_to_check_uses_direct_file_targets(monkeypatch) -> None:
    monkeypatch.setattr(qc, "normalize_explicit_files", lambda file_paths, allow_directories=False: ["qc.py"])

    mode, files = qc.detect_files_to_check(_make_args(targets=["qc.py"]))

    assert mode == "direct file targets"
    assert files == ["qc.py"]


def test_parser_accepts_single_direct_file_target() -> None:
    parser = qc.create_parser()

    args = parser.parse_args(["qc.py"])

    assert args.targets == ["qc.py"]


def test_parser_accepts_multiple_direct_file_targets() -> None:
    parser = qc.create_parser()

    args = parser.parse_args(["qc.py", "frontend/src/App.tsx"])

    assert args.targets == ["qc.py", "frontend/src/App.tsx"]


def test_parser_accepts_verbose_flag() -> None:
    parser = qc.create_parser()

    args = parser.parse_args(["--verbose", "qc.py"])

    assert args.verbose is True
    assert args.targets == ["qc.py"]


def test_normalize_explicit_files_rejects_directory_without_flag(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(qc, "project_root", tmp_path)

    source_dir = tmp_path / "frontend" / "src"
    source_dir.mkdir(parents=True)

    try:
        qc.normalize_explicit_files(["frontend/src"])
    except ValueError as exc:
        assert "--allow-directories" in str(exc)
    else:
        raise AssertionError("Expected ValueError for directory target without flag")


def test_normalize_explicit_files_expands_directory_with_flag(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(qc, "project_root", tmp_path)

    source_dir = tmp_path / "frontend" / "src"
    source_dir.mkdir(parents=True)
    (source_dir / "App.tsx").write_text("export function App() { return null }\n", encoding="utf-8")
    (source_dir / "api.ts").write_text("export const api = {}\n", encoding="utf-8")
    (source_dir / "README.md").write_text("# docs\n", encoding="utf-8")

    normalized = qc.normalize_explicit_files(["frontend/src"], allow_directories=True)

    assert normalized == ["frontend/src/api.ts", "frontend/src/App.tsx"]


def test_normalize_explicit_files_rejects_missing_target(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(qc, "project_root", tmp_path)

    try:
        qc.normalize_explicit_files(["missing.py"])
    except ValueError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing explicit target")


def test_normalize_explicit_files_rejects_non_coding_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(qc, "project_root", tmp_path)

    docs_file = tmp_path / "README.md"
    docs_file.write_text("# docs\n", encoding="utf-8")

    try:
        qc.normalize_explicit_files(["README.md"])
    except ValueError as exc:
        assert "not a supported coding file" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-coding explicit target")


def test_print_verbose_analysis_summary_outputs_issue_counts(capsys) -> None:
    issue = qc.QualityCheckSkill().analyze_file(
        "sample.tsx",
        "export function Sample() {\n  console.log('x')\n  return <div>Coming soon</div>\n}\n",
    )

    qc._print_verbose_analysis_summary([issue])
    captured = capsys.readouterr()

    assert "[verbose] Analyzer pass:" in captured.out
    assert "sample.tsx: 2 issue(s)" in captured.out
    assert "warnings=2" in captured.out
