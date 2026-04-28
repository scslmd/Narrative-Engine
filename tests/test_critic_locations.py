from __future__ import annotations

import json

from app.services.consistency_critic import Violation, CriticResult


def test_violation_accepts_location_fields():
    v = Violation(
        character="Hero",
        issue="Wrong voice",
        suggestion="Use simpler vocabulary",
        line_start=10,
        line_end=12,
        quote="The hero expostulated with great fervor",
    )
    assert v.line_start == 10
    assert v.line_end == 12
    assert v.quote == "The hero expostulated with great fervor"


def test_violation_defaults_locations_to_none():
    v = Violation(
        character="Hero",
        issue="Wrong voice",
        suggestion="Use simpler vocabulary",
    )
    assert v.line_start is None
    assert v.line_end is None
    assert v.quote is None


def test_backward_compat_old_violation_without_locations():
    """Simulate old LLM response that doesn't include location fields."""
    old_response = json.dumps({
        "passed": False,
        "violations": [
            {"character": "Hero", "issue": "Wrong voice", "suggestion": "Fix it"}
        ],
    })
    data = json.loads(old_response)
    for v in data.get("violations", []):
        viol = Violation(
            character=v["character"],
            issue=v["issue"],
            suggestion=v["suggestion"],
        )
    assert viol.line_start is None
    assert viol.line_end is None
    assert viol.quote is None


def test_critic_prompt_includes_location_fields_in_json_schema():
    from app.services.runtime_prompts import build_critic_check_request

    req = build_critic_check_request(
        draft_text="Some draft text here.",
        character_bios={"Hero": "brave knight"},
        default_model="test-model",
    )
    system = req.messages[0].content
    assert "line_start" in system
    assert "line_end" in system
    assert "quote" in system


def test_critic_user_message_has_numbered_lines():
    from app.services.runtime_prompts import build_critic_check_request

    draft = "Line one.\nLine two.\nLine three."
    req = build_critic_check_request(
        draft_text=draft,
        character_bios={"Hero": "brave knight"},
        default_model="test-model",
    )
    user = req.messages[1].content
    assert "1: Line one" in user
    assert "2: Line two" in user
    assert "3: Line three" in user


def test_critic_truncates_long_draft_at_500_lines():
    from app.services.runtime_prompts import build_critic_check_request

    draft = "\n".join([f"Line {i}" for i in range(600)])
    req = build_critic_check_request(
        draft_text=draft,
        character_bios={"Hero": "brave knight"},
        default_model="test-model",
    )
    user = req.messages[1].content
    assert "501: Line 500" not in user  # line 501 (0-indexed 500) excluded
    assert "more lines truncated" in user  # truncation note present


def test_rewrite_prompt_includes_location_info():
    critic_result = CriticResult(
        passed=False,
        violations=[
            Violation(
                character="Hero",
                issue="Wrong voice",
                suggestion="Use simpler vocabulary",
                line_start=10,
                line_end=12,
                quote="The hero expostulated with great fervor",
            ),
            Violation(
                character="Villain",
                issue="Out of character",
                suggestion="Make more sinister",
                line_start=45,
                line_end=47,
                quote="The villain smiled warmly and offered help",
            ),
        ],
    )

    violation_lines = []
    for v in critic_result.violations[:3]:
        if v.line_start is not None and v.quote is not None:
            violation_lines.append(
                f"- {v.character} (lines {v.line_start}-{v.line_end}): {v.issue}\n"
                f'  Quote: "{v.quote}"\n'
                f"  Fix: {v.suggestion}"
            )
        else:
            violation_lines.append(f"- {v.character}: {v.issue} -> {v.suggestion}")

    violation_summary = "\n".join(violation_lines)
    assert "lines 10-12" in violation_summary
    assert 'Quote: "The hero expostulated' in violation_summary
    assert "Fix: Use simpler vocabulary" in violation_summary


def test_rewrite_prompt_degrades_without_locations():
    critic_result = CriticResult(
        passed=False,
        violations=[
            Violation(
                character="Hero",
                issue="Wrong voice",
                suggestion="Fix it",
            ),
        ],
    )

    violation_lines = []
    for v in critic_result.violations[:3]:
        if v.line_start is not None and v.quote is not None:
            violation_lines.append(
                f"- {v.character} (lines {v.line_start}-{v.line_end}): {v.issue}\n"
                f'  Quote: "{v.quote}"\n'
                f"  Fix: {v.suggestion}"
            )
        else:
            violation_lines.append(f"- {v.character}: {v.issue} -> {v.suggestion}")

    violation_summary = "\n".join(violation_lines)
    assert "- Hero: Wrong voice -> Fix it" in violation_summary
    assert "lines" not in violation_summary
