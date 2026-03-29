# Quality Check Integration Hook

from __future__ import annotations

"""Quality Check Integration Hook

This module provides the integration hook for automatically triggering quality checks
when coding tasks are completed.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    CODING = "coding"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    OTHER = "other"


@dataclass
class TaskInfo:
    """Information about a completed task."""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    context: str = "general"
    files_changed: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class QualityCheckIntegration:
    """
    Integration hook for automatic quality check triggering.

    This class provides the mechanism to automatically trigger quality checks
    when coding tasks are completed.
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path(__file__).parent / "skills"
        self.enabled = True
        self.delay_ms = 1000
        self.conditions = [
            lambda task: task.status == TaskStatus.COMPLETED,
            lambda task: task.task_type == TaskType.CODING,
        ]
        self.callbacks: list[Callable[[TaskInfo], None]] = []
        self._quality_check_module = None

    def register_callback(self, callback: Callable[[TaskInfo], None]):
        """Register a callback to be called when quality check is triggered."""
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[TaskInfo], None]):
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def should_trigger(self, task: TaskInfo) -> bool:
        """Check if quality check should be triggered for this task."""
        if not self.enabled:
            return False

        for condition in self.conditions:
            if not condition(task):
                return False

        return True

    def on_task_complete(self, task_info: Dict[str, Any]) -> Optional[str]:
        """
        Called when a coding task is completed.

        Args:
            task_info: Dictionary containing task information

        Returns:
            Quality check report if triggered, None otherwise
        """
        # Convert dict to TaskInfo object
        task = TaskInfo(
            task_id=task_info.get("task_id", "unknown"),
            task_type=TaskType(task_info.get("task_type", "other")),
            status=TaskStatus(task_info.get("status", "pending")),
            context=task_info.get("context", "general"),
            files_changed=task_info.get("files_changed", []),
            timestamp=task_info.get("timestamp", time.time())
        )

        if not self.should_trigger(task):
            return None

        # Load quality check skill
        self._load_quality_check_skill()

        # Generate quality check report
        report = self._generate_quality_check_report(task)

        # Call registered callbacks
        for callback in self.callbacks:
            try:
                callback(task)
            except Exception as e:
                print(f"Error in quality check callback: {e}")

        return report

    def _load_quality_check_skill(self):
        """Load the quality check skill module."""
        if self._quality_check_module is not None:
            return

        try:
            # Try to import the quality check skill
            import sys
            sys.path.insert(0, str(self.skills_dir.parent))
            from quality_check import QualityCheckSkill
            self._quality_check_module = QualityCheckSkill()
        except ImportError as e:
            print(f"Warning: Could not load quality check skill: {e}")
            self._quality_check_module = None

    def _generate_quality_check_report(self, task: TaskInfo) -> str:
        """Generate a quality check report for the completed task."""
        if self._quality_check_module is None:
            return self._generate_fallback_report(task)

        # Use the combined method that includes adverse review
        return self._quality_check_module.run_quality_check_with_adverse_review(
            task.context,
            task.files_changed
        )

    def _generate_fallback_report(self, task: TaskInfo) -> str:
        """Generate a fallback quality check report."""
        report = [
            "# Quality Check Assessment",
            "",
            f"**Context:** {task.context}",
            "",
            "## Introduction",
            "",
            "This quality check evaluates your work against 10 universal quality dimensions.",
            "Each dimension is scored 0-2, with a target of 80% (17/20).",
            "",
            "## Dimension Assessment",
            ""
        ]

        dimensions = [
            ("Contract Adherence", [
                "Use exact interfaces/endpoints defined by the system",
                "Do not invent workarounds for uncertain contracts",
                "Preserve naming conventions at appropriate boundaries",
                "Do not rename fields just for convenience"
            ]),
            ("Architectural Consistency", [
                "Use shared utilities and clients instead of duplicating configuration",
                "Maintain consistency in error handling, state management, and data flow",
                "Do not reinvent patterns that already exist",
                "Extend existing abstractions rather than creating parallel ones"
            ]),
            ("State Correctness", [
                "Source of truth is explicit and singular",
                "State survives edge cases (deep links, refreshes, restarts)",
                "Avoid fragile parsing or brittle assumptions",
                "Route/state remain synchronized across navigation methods"
            ]),
            ("Production Readiness", [
                "No console logs in user-facing code paths",
                "No dead buttons or non-functional CTAs",
                "No placeholder data or 'for now' assumptions",
                "Every user-facing action has a real implementation"
            ]),
            ("Error Resilience", [
                "Loading states are explicit",
                "Empty states are explicit and suggest next steps",
                "Error states are recoverable where possible",
                "Meaningful error categories are distinguished",
                "Service layer handles technical details; presentation layer handles display"
            ]),
            ("UX Polish", [
                "Labels and messages are readable and intentional",
                "Disabled states prevent invalid actions proactively",
                "No encoding artifacts or awkward interactions",
                "Buttons do what they claim",
                "State transitions feel deliberate"
            ]),
            ("Type Safety", [
                "Avoid excessive type casting",
                "Do not collapse rich shapes into lossy substitutes without reason",
                "Functions return established types whenever possible",
                "Component interfaces are explicit and narrow"
            ]),
            ("Static Analyzability", [
                "Avoid dynamic patterns that defeat optimization or detection",
                "Use explicit conditional branches over dynamic string interpolation where tools matter",
                "Keep styling and configuration aligned with tool expectations"
            ]),
            ("Boundary Discipline", [
                "Mock/test mode is explicit and contained",
                "Mock data matches real types",
                "Live mode does not keep mock-only artifacts",
                "Boundaries are explicit, not leaky"
            ]),
            ("Maintainability", [
                "Changes reduce duplication, not increase it",
                "Intent is obvious without reverse-engineering",
                "Future extensions are easier after the change",
                "Logic is centralized when it appears in multiple places"
            ])
        ]

        for dimension_name, checklist in dimensions:
            report.append(f"### {dimension_name}")
            report.append("")
            for item in checklist:
                report.append(f"- [ ] {item}")
            report.append("")
            report.append(f"**Score (0-2):** _Enter your score for {dimension_name}_")
            report.append("")

        report.extend([
            "## Automatic Failure Conditions",
            "",
            "Work is NOT high quality if ANY of these are true:",
            "",
            "- [ ] Automated checks fail",
            "- [ ] Prototype artifacts remain in user-visible paths",
            "- [ ] Dead or non-functional UI elements exist",
            "- [ ] Configuration duplication exists where sharing is possible",
            "- [ ] Placeholder assumptions remain in merged flows",
            "- [ ] Visible artifacts (encoding, mojibake) remain",
            "- [ ] Mock behavior leaks into live flows unnecessarily",
            "",
            "## Final Self-Check",
            "",
            "Before declaring work complete, answer these with 'yes':",
            "",
            "- [ ] Does every action have a real implementation?",
            "- [ ] Does every interface match the contract?",
            "- [ ] Did I remove all prototype artifacts?",
            "- [ ] Did I avoid duplicating existing utilities?",
            "- [ ] Can the flow survive edge cases?",
            "- [ ] Are all states (loading, empty, error) explicit?",
            "- [ ] Is the surface free of artifacts and brittle patterns?",
            "- [ ] Did all automated checks pass?",
            "",
            "**If any answer is 'no,' the work is not complete.**",
            ""
        ])

        return "\n".join(report)


def create_integration(skills_dir: Optional[Path] = None) -> QualityCheckIntegration:
    """Factory function to create a quality check integration instance."""
    return QualityCheckIntegration(skills_dir)


# Example usage
if __name__ == "__main__":
    # Create integration
    integration = create_integration()

    # Simulate task completion
    task_info = {
        "task_id": "test-task-123",
        "task_type": "coding",
        "status": "completed",
        "context": "frontend",
        "files_changed": [
            "frontend/src/components/Button.tsx",
            "frontend/src/services/api.ts"
        ]
    }

    # Trigger quality check
    report = integration.on_task_complete(task_info)

    if report:
        print(report)
    else:
        print("Quality check not triggered (conditions not met)")
