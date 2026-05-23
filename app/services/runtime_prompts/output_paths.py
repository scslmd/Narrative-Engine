from __future__ import annotations

from pathlib import Path


def architect_output_path(project_dir: Path) -> Path:
    return project_dir / "exports" / "p100_architect_output.md"


def sequence_output_path(project_dir: Path) -> Path:
    return project_dir / "sequences.json"


def chapter_output_path(project_dir: Path, chapter_id: str | None = None) -> Path:
    if chapter_id:
        out_dir = project_dir / "chapters"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f"{chapter_id}.md"
    return project_dir / "chapter.md"


def story_bible_output_path(project_dir: Path) -> Path:
    return project_dir / "story_bible.json"


__all__ = [
    "architect_output_path",
    "sequence_output_path",
    "chapter_output_path",
    "story_bible_output_path",
]
