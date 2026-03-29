from __future__ import annotations

from scripts.quality_check_engine import QualityCheckSkill


def test_run_adverse_review_includes_concrete_findings_for_analyzed_file(tmp_path) -> None:
    target = tmp_path / "sample.tsx"
    target.write_text(
        "\n".join(
            [
                "export function Sample() {",
                "  const unsafe = value as SomeType;",
                "  return <div>Coming soon</div>;",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    skill = QualityCheckSkill()
    report = skill.run_adverse_review([str(target)], "general")

    assert "### Concrete Findings" in report
    assert "sample.tsx" in report
    assert "Type assertion found" in report
    assert "Placeholder or prototype text found" in report


def test_run_adverse_review_reports_when_no_concrete_findings_exist(tmp_path) -> None:
    target = tmp_path / "clean.py"
    target.write_text(
        "\n".join(
            [
                "def add(a: int, b: int) -> int:",
                "    return a + b",
            ]
        ),
        encoding="utf-8",
    )

    skill = QualityCheckSkill()
    report = skill.run_adverse_review([str(target)], "general")

    assert "No concrete adverse findings were detected by automated file analysis." in report
