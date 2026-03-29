# Quality Check Skill

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import re


"""Quality Check Skill

This module provides the `/quality-check` slash command skill for interactive
quality assessment of code changes.
"""


class QualityDimension(Enum):
    """Quality dimensions for assessment."""
    CONTRACT_ADHERENCE = ("Contract Adherence", "contract_adherence")
    ARCHITECTURAL_CONSISTENCY = ("Architectural Consistency", "architectural_consistency")
    STATE_CORRECTNESS = ("State Correctness", "state_correctness")
    PRODUCTION_READINESS = ("Production Readiness", "production_readiness")
    ERROR_RESILIENCE = ("Error Resilience", "error_resilience")
    UX_POLISH = ("UX Polish", "ux_polish")
    TYPE_SAFETY = ("Type Safety", "type_safety")
    STATIC_ANALYZABILITY = ("Static Analyzability", "static_analyzability")
    BOUNDARY_DISCIPLINE = ("Boundary Discipline", "boundary_discipline")
    MAINTAINABILITY = ("Maintainability", "maintainability")

    def __init__(self, display_name: str, key: str):
        self.display_name = display_name
        self.key = key


@dataclass
class QualityScore:
    """Quality assessment score."""
    dimension: QualityDimension
    score: int  # 0-2
    notes: str = ""


@dataclass
class CodeIssue:
    """A code issue found during analysis."""
    file: str
    line: int
    issue_type: str
    message: str
    severity: str = "warning"  # error, warning, info
    suggestion: str = ""


@dataclass
class CodeAnalysisResult:
    """Result of analyzing a single file."""
    file_path: str
    content: str
    issues: List[CodeIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    dimension_scores: Dict[str, int] = field(default_factory=dict)


class QualityCheckSkill:
    """
    Slash command skill for quality assessment.

    Usage:
        /quality-check              - General quality check
        /quality-check frontend     - Frontend-specific quality check
        /quality-check backend      - Backend-specific quality check
        /quality-check merge        - Pre-merge quality validation
    """

    def __init__(self):
        self.dimensions = list(QualityDimension)
        self.max_score = len(self.dimensions) * 2
        self.target_percentage = 0.8
        self.target_score = int(self.max_score * self.target_percentage)

        # Regex patterns for code analysis
        self.patterns = {
            'console_log': re.compile(r'console\.(log|warn|error|info|debug)\s*\('),
            'todo_comment': re.compile(r'#\s*TODO|//\s*TODO|/\*\s*TODO'),
            'fixme_comment': re.compile(r'#\s*FIXME|//\s*FIXME|/\*\s*FIXME'),
            'any_type': re.compile(r':\s*any\s*[,;\)]|<any>'),
            'unused_import': re.compile(r'^import\s+.*from'),
            'long_line': re.compile(r'.{121,}'),
            'magic_number': re.compile(r'(?<![\w\.])(\d{2,})(?![\w\.])'),
            'string_concat': re.compile(r'\+\s*["\']|["\']\s*\+'),
            'try_except_pass': re.compile(r'except.*:\s*pass'),
            'bare_except': re.compile(r'except\s*:\s*(pass|$)'),
            'dead_code': re.compile(r'^\s*#\s*(if|elif|else)\s*0'),
            'placeholder_text': re.compile(r'coming soon|placeholder|stub|select two versions to compare', re.IGNORECASE),
            'type_assertion': re.compile(r'\bas\s+[A-Za-z_][\w<>{}\[\]\|&,\s]*'),
            'mojibake': re.compile(r'Ãƒ.|Ã¢.|ï¿½'),
        }

    def read_file(self, file_path: str) -> Optional[str]:
        """Read a file and return its contents."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            return path.read_text(encoding='utf-8')
        except Exception:
            return None

    def analyze_file(self, file_path: str, content: str) -> CodeAnalysisResult:
        """
        Analyze a single file for quality issues.

        Args:
            file_path: Path to the file
            content: File contents

        Returns:
            CodeAnalysisResult with issues and metrics
        """
        result = CodeAnalysisResult(file_path=file_path, content=content)
        lines = content.split('\n')

        # Calculate basic metrics
        result.metrics = {
            'line_count': len(lines),
            'char_count': len(content),
            'max_line_length': max((len(line) for line in lines), default=0),
            'is_typescript': file_path.endswith(('.ts', '.tsx')),
            'is_python': file_path.endswith('.py'),
        }

        # Check for various issues
        self._check_console_logs(result, lines)
        self._check_todo_comments(result, lines)
        self._check_any_types(result, lines)
        self._check_long_lines(result, lines)
        self._check_error_handling(result, lines)
        self._check_magic_numbers(result, lines)
        self._check_function_length(result, lines, file_path)
        self._check_placeholder_text(result, lines)
        self._check_type_assertions(result, lines)
        self._check_encoding_artifacts(result, lines)

        return result

    def _check_console_logs(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for console.log statements."""
        for i, line in enumerate(lines, 1):
            if self.patterns['console_log'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='console_log',
                    message='Console.log found - should be removed in production code',
                    severity='warning',
                    suggestion='Remove console.log or use proper logging framework'
                ))

    def _check_todo_comments(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for TODO and FIXME comments."""
        for i, line in enumerate(lines, 1):
            if self.patterns['todo_comment'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='todo_comment',
                    message='TODO comment found - should be addressed',
                    severity='info'
                ))
            if self.patterns['fixme_comment'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='fixme_comment',
                    message='FIXME comment found - should be addressed',
                    severity='warning'
                ))

    def _check_any_types(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for 'any' type usage in TypeScript."""
        if not result.metrics.get('is_typescript'):
            return
        for i, line in enumerate(lines, 1):
            if self.patterns['any_type'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='any_type',
                    message='Use of "any" type - reduces type safety',
                    severity='warning',
                    suggestion='Use more specific types or unknown'
                ))

    def _check_long_lines(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for lines exceeding 120 characters."""
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='long_line',
                    message=f'Line exceeds 120 characters ({len(line)} chars)',
                    severity='info',
                    suggestion='Break into multiple lines for readability'
                ))

    def _check_error_handling(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for poor error handling patterns."""
        if not result.metrics.get('is_python'):
            return
        for i, line in enumerate(lines, 1):
            if self.patterns['bare_except'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='bare_except',
                    message='Bare except clause - catches all exceptions including SystemExit',
                    severity='error',
                    suggestion='Use specific exception types or at least "except Exception"'
                ))
            if self.patterns['try_except_pass'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='silent_failure',
                    message='Exception caught but silently ignored',
                    severity='warning',
                    suggestion='Log the error or re-raise with context'
                ))

    def _check_magic_numbers(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for magic numbers."""
        if not result.metrics.get('is_python'):
            return
        for i, line in enumerate(lines, 1):
            # Skip comments and string literals
            if line.strip().startswith('#'):
                continue
            matches = self.patterns['magic_number'].findall(line)
            for match in matches:
                num = int(match)
                if num > 100:  # Only flag larger numbers
                    result.issues.append(CodeIssue(
                        file=result.file_path,
                        line=i,
                        issue_type='magic_number',
                        message=f'Magic number {num} found',
                        severity='info',
                        suggestion='Use a named constant for clarity'
                    ))

    def _check_function_length(self, result: CodeAnalysisResult, lines: List[str], file_path: str) -> None:
        """Check for overly long functions."""
        # Simple heuristic - look for def/function declarations
        func_pattern = re.compile(r'^\s*(def|async\s+def|function|const\s+\w+\s*=\s*(async\s+)?\()')
        func_starts = []

        for i, line in enumerate(lines):
            if func_pattern.match(line):
                func_starts.append(i)

        # Calculate function lengths
        for start_idx in func_starts:
            # Find end of function (next function at same indent or end of file)
            start_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
            end_idx = len(lines)

            for j in range(start_idx + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    curr_indent = len(lines[j]) - len(lines[j].lstrip())
                    if curr_indent <= start_indent and func_pattern.match(lines[j]):
                        end_idx = j
                        break

            func_length = end_idx - start_idx
            if func_length > 50:
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=start_idx + 1,
                    issue_type='long_function',
                    message=f'Function is {func_length} lines long (>50)',
                    severity='warning',
                    suggestion='Consider breaking into smaller functions'
                ))

    def _check_placeholder_text(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for placeholder or prototype copy in user-facing code."""
        for i, line in enumerate(lines, 1):
            if self.patterns['placeholder_text'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='placeholder_text',
                    message='Placeholder or prototype text found in code path',
                    severity='warning',
                    suggestion='Replace placeholder text with a real implementation or explicit unsupported-state handling'
                ))

    def _check_type_assertions(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for unsafe-looking TypeScript type assertions."""
        if not result.metrics.get('is_typescript'):
            return
        for i, line in enumerate(lines, 1):
            if self.patterns['type_assertion'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='type_assertion',
                    message='Type assertion found - verify this is not masking an invalid runtime shape',
                    severity='warning',
                    suggestion='Prefer a real type-safe conversion or validated narrowing over `as ...` where possible'
                ))

    def _check_encoding_artifacts(self, result: CodeAnalysisResult, lines: List[str]) -> None:
        """Check for common mojibake artifacts in source text."""
        for i, line in enumerate(lines, 1):
            if self.patterns['mojibake'].search(line):
                result.issues.append(CodeIssue(
                    file=result.file_path,
                    line=i,
                    issue_type='encoding_artifact',
                    message='Possible mojibake or replacement-character artifact found',
                    severity='warning',
                    suggestion='Replace corrupted text with valid UTF-8 or ASCII text before shipping'
                ))

    def analyze_files(self, file_paths: List[str]) -> List[CodeAnalysisResult]:
        """
        Analyze multiple files.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            List of CodeAnalysisResult objects
        """
        results = []
        for file_path in file_paths:
            content = self.read_file(file_path)
            if content is not None:
                result = self.analyze_file(file_path, content)
                results.append(result)
        return results

    def run_quality_check(self, context: str = "general", files_changed: Optional[List[str]] = None) -> str:
        """
        Run the quality check assessment.

        Args:
            context: Context for the quality check (frontend, backend, merge, general)
            files_changed: Optional list of files to analyze

        Returns:
            Formatted quality check report
        """
        report_sections = []

        # Header and files analyzed
        analysis_results = self._build_header_and_analyze_files(report_sections, context, files_changed)

        # Introduction
        self._add_introduction_section(report_sections)

        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(analysis_results, context)

        # Dimension assessment
        self._add_dimension_assessment_section(report_sections, dimension_scores, context)

        # Issues found
        self._add_issues_found_section(report_sections, analysis_results)

        # Automatic failure conditions
        self._add_failure_conditions_section(report_sections, analysis_results, context)

        # Context-specific automated checks
        self._add_automated_checks_section(report_sections, context)

        # Overall score
        self._add_overall_score_section(report_sections, dimension_scores)

        # Final self-check
        self._add_self_check_section(report_sections, context)

        # Adverse review intro
        self._add_adverse_review_intro(report_sections)

        return "\n".join(report_sections)

    def _build_header_and_analyze_files(
        self,
        report_sections: List[str],
        context: str,
        files_changed: Optional[List[str]]
    ) -> List[CodeAnalysisResult]:
        """Build header section and analyze files if provided."""
        report_sections.append("# Quality Check Assessment")
        report_sections.append("")
        report_sections.append(f"**Context:** {context}")
        report_sections.append("")

        analysis_results = []
        if files_changed:
            report_sections.append("## Files Analyzed")
            report_sections.append("")
            for f in files_changed:
                report_sections.append(f"- `{f}`")
            report_sections.append("")
            analysis_results = self.analyze_files(files_changed)

        return analysis_results

    def _add_introduction_section(self, report_sections: List[str]) -> None:
        """Add the introduction section."""
        report_sections.append("## Introduction")
        report_sections.append("")
        report_sections.append("This quality check evaluates your work against 10 universal quality dimensions.")
        report_sections.append("Each dimension is scored 0-2, with a target of 80% (16/20).")
        report_sections.append("")
        report_sections.append("**Scoring Guide:**")
        report_sections.append("- `0`: Broken or missing")
        report_sections.append("- `1`: Partial or inconsistent")
        report_sections.append("- `2`: Complete and consistent")
        report_sections.append("")

    def _add_dimension_assessment_section(
        self,
        report_sections: List[str],
        dimension_scores: Dict[str, Any],
        context: str
    ) -> None:
        """Add the dimension assessment section."""
        report_sections.append("## Dimension Assessment")
        report_sections.append("")

        for dimension in self.dimensions:
            self._add_dimension_subsection(report_sections, dimension, dimension_scores, context)

    def _add_dimension_subsection(
        self,
        report_sections: List[str],
        dimension: QualityDimension,
        dimension_scores: Dict[str, Any],
        context: str
    ) -> None:
        """Add a single dimension subsection."""
        report_sections.append(f"### {dimension.display_name}")
        report_sections.append("")

        checklist = self._get_dimension_checklist(dimension, context)
        score = dimension_scores.get(dimension.key, 1)
        score_notes = dimension_scores.get(f"{dimension.key}_notes", "")

        checked = "[x]" if score == 2 else "[ ]"
        for item in checklist:
            report_sections.append(f"{checked} {item}")

        report_sections.append("")
        report_sections.append(f"**Score (0-2):** `{score}`")
        if score_notes:
            report_sections.append(f"**Notes:** {score_notes}")
        report_sections.append("")

    def _add_issues_found_section(
        self,
        report_sections: List[str],
        analysis_results: List[CodeAnalysisResult]
    ) -> None:
        """Add the issues found section."""
        if not analysis_results:
            return

        report_sections.append("## Issues Found")
        report_sections.append("")

        all_issues = self._collect_all_issues(analysis_results)

        if all_issues:
            self._add_issues_by_severity(report_sections, all_issues)
        else:
            report_sections.append("No issues found during automated analysis.")
            report_sections.append("")

    def _collect_all_issues(self, analysis_results: List[CodeAnalysisResult]) -> List[CodeIssue]:
        """Collect all issues from analysis results."""
        all_issues = []
        for result in analysis_results:
            all_issues.extend(result.issues)
        return all_issues

    def _add_issues_by_severity(
        self,
        report_sections: List[str],
        all_issues: List[CodeIssue]
    ) -> None:
        """Add issues grouped by severity."""
        errors = [i for i in all_issues if i.severity == 'error']
        warnings = [i for i in all_issues if i.severity == 'warning']
        infos = [i for i in all_issues if i.severity == 'info']

        if errors:
            self._add_issue_subsection(report_sections, "### Errors", errors, include_suggestion=False)

        if warnings:
            self._add_issue_subsection(report_sections, "### Warnings", warnings, include_suggestion=True)

        if infos:
            self._add_issue_subsection(report_sections, "### Info", infos, include_suggestion=False)

    def _add_issue_subsection(
        self,
        report_sections: List[str],
        header: str,
        issues: List[CodeIssue],
        include_suggestion: bool
    ) -> None:
        """Add a subsection for issues of a specific severity."""
        report_sections.append(header)
        report_sections.append("")

        for issue in issues:
            report_sections.append(f"- **{issue.file}:{issue.line}** - {issue.message}")
            if include_suggestion and issue.suggestion:
                report_sections.append(f"  -> {issue.suggestion}")
        report_sections.append("")

    def _add_failure_conditions_section(
        self,
        report_sections: List[str],
        analysis_results: List[CodeAnalysisResult],
        context: str
    ) -> None:
        """Add the automatic failure conditions section."""
        report_sections.append("## Automatic Failure Conditions")
        report_sections.append("")
        report_sections.append("Work is NOT high quality if ANY of these are true:")
        report_sections.append("")

        failure_conditions = self._get_failure_conditions(context)
        for condition in failure_conditions:
            violated = self._check_failure_condition(condition, analysis_results)
            marker = "[!]" if violated else "[ ]"
            report_sections.append(f"{marker} {condition}")
        report_sections.append("")

    def _add_automated_checks_section(
        self,
        report_sections: List[str],
        context: str
    ) -> None:
        """Add context-specific automated checks section."""
        if context == "frontend":
            self._add_frontend_checks_section(report_sections)
        elif context == "backend":
            self._add_backend_checks_section(report_sections)
        elif context == "merge":
            self._add_merge_checks_section(report_sections)

    def _add_frontend_checks_section(self, report_sections: List[str]) -> None:
        """Add frontend automated checks."""
        report_sections.append("## Frontend Automated Checks")
        report_sections.append("")
        report_sections.append("Run these commands and ensure they pass:")
        report_sections.append("")
        report_sections.append("```bash")
        report_sections.append("cd frontend")
        report_sections.append("npm run lint")
        report_sections.append("npm run typecheck")
        report_sections.append("npm run build")
        report_sections.append("```")
        report_sections.append("")

    def _add_backend_checks_section(self, report_sections: List[str]) -> None:
        """Add backend automated checks."""
        report_sections.append("## Backend Automated Checks")
        report_sections.append("")
        report_sections.append("Run these commands and ensure they pass:")
        report_sections.append("")
        report_sections.append("```bash")
        report_sections.append("python -m pytest -q -p no:cacheprovider")
        report_sections.append("```")
        report_sections.append("")

    def _add_merge_checks_section(self, report_sections: List[str]) -> None:
        """Add merge readiness checks."""
        report_sections.append("## Merge Readiness Checks")
        report_sections.append("")
        report_sections.append("Run ALL of these commands and ensure they pass:")
        report_sections.append("")
        report_sections.append("```bash")
        report_sections.append("# Backend")
        report_sections.append("python -m pytest -q -p no:cacheprovider")
        report_sections.append("")
        report_sections.append("# Frontend")
        report_sections.append("cd frontend && npm run lint")
        report_sections.append("cd frontend && npm run typecheck")
        report_sections.append("cd frontend && npm run build")
        report_sections.append("```")
        report_sections.append("")

    def _add_overall_score_section(
        self,
        report_sections: List[str],
        dimension_scores: Dict[str, Any]
    ) -> None:
        """Add the overall score section."""
        total_score = sum(dimension_scores.get(d.key, 0) for d in self.dimensions)
        percentage = (total_score / self.max_score) * 100
        passed = total_score >= self.target_score

        report_sections.append("## Overall Score")
        report_sections.append("")
        status = "[PASS]" if passed else "[FAIL]"
        report_sections.append(f"**Total:** {total_score}/{self.max_score} ({percentage:.0f}%) {status}")
        report_sections.append("")

    def _add_self_check_section(
        self,
        report_sections: List[str],
        context: str
    ) -> None:
        """Add the final self-check section."""
        report_sections.append("## Final Self-Check")
        report_sections.append("")
        report_sections.append("Before declaring work complete, answer these with 'yes':")
        report_sections.append("")

        self_check_questions = self._get_self_check_questions(context)
        for question in self_check_questions:
            report_sections.append(f"- [ ] {question}")
        report_sections.append("")
        report_sections.append("**If any answer is 'no,' the work is not complete.**")
        report_sections.append("")

    def _add_adverse_review_intro(self, report_sections: List[str]) -> None:
        """Add the adverse review introduction."""
        report_sections.append("---")
        report_sections.append("")
        report_sections.append("*The following is the final step - an adverse review of your work.*")
        report_sections.append("")

    def run_quality_check_with_adverse_review(self, context: str = "general",
                                              files_changed: Optional[List[str]] = None) -> str:
        """
        Run the complete quality check including adverse review.

        Args:
            context: Context for the quality check
            files_changed: List of files that were modified

        Returns:
            Complete quality check report with adverse review
        """
        # Run the base quality check
        base_report = self.run_quality_check(context, files_changed)

        # Add the adverse review
        adverse_report = self.run_adverse_review(files_changed, context)

        return base_report + adverse_report

    def _calculate_dimension_scores(self, analysis_results: List[CodeAnalysisResult], context: str) -> Dict[str, Any]:
        """
        Calculate scores for each quality dimension based on code analysis.

        Args:
            analysis_results: List of analysis results from files
            context: Context for scoring

        Returns:
            Dictionary mapping dimension keys to scores (0-2) and notes
        """
        scores = {}

        # Initialize all dimensions to score of 2 (perfect)
        for dimension in self.dimensions:
            scores[dimension.key] = 2
            scores[f"{dimension.key}_notes"] = ""

        if not analysis_results:
            return scores

        # Count issues by type
        issue_counts = {}
        total_issues = 0
        for result in analysis_results:
            for issue in result.issues:
                issue_type = issue.issue_type
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                total_issues += 1

        # Production Readiness - check for console logs, TODOs
        console_logs = issue_counts.get('console_log', 0)
        todos = issue_counts.get('todo_comment', 0)
        placeholders = issue_counts.get('placeholder_text', 0)
        if console_logs > 0:
            scores[QualityDimension.PRODUCTION_READINESS.key] = 1
            scores[f"{QualityDimension.PRODUCTION_READINESS.key}_notes"] = f"Found {console_logs} console.log statement(s)"
        if todos > 0:
            scores[QualityDimension.PRODUCTION_READINESS.key] = min(
                scores[QualityDimension.PRODUCTION_READINESS.key], 1
            )
            notes = scores.get(f"{QualityDimension.PRODUCTION_READINESS.key}_notes", "")
            scores[f"{QualityDimension.PRODUCTION_READINESS.key}_notes"] = notes + f" {todos} TODO(s)" if notes else f"{todos} TODO(s)"
        if placeholders > 0:
            scores[QualityDimension.PRODUCTION_READINESS.key] = min(
                scores[QualityDimension.PRODUCTION_READINESS.key], 1
            )
            notes = scores.get(f"{QualityDimension.PRODUCTION_READINESS.key}_notes", "")
            addition = f"{placeholders} placeholder/prototype text instance(s)"
            scores[f"{QualityDimension.PRODUCTION_READINESS.key}_notes"] = notes + f" {addition}" if notes else addition

        # Error Resilience - check for bare except, silent failures
        bare_excepts = issue_counts.get('bare_except', 0)
        silent_failures = issue_counts.get('silent_failure', 0)
        if bare_excepts > 0:
            scores[QualityDimension.ERROR_RESILIENCE.key] = 0
            scores[f"{QualityDimension.ERROR_RESILIENCE.key}_notes"] = f"Found {bare_excepts} bare except clause(s)"
        elif silent_failures > 0:
            scores[QualityDimension.ERROR_RESILIENCE.key] = 1
            scores[f"{QualityDimension.ERROR_RESILIENCE.key}_notes"] = f"Found {silent_failures} silent failure(s)"

        # Type Safety - check for 'any' types
        any_types = issue_counts.get('any_type', 0)
        type_assertions = issue_counts.get('type_assertion', 0)
        if any_types > 0:
            scores[QualityDimension.TYPE_SAFETY.key] = 1
            scores[f"{QualityDimension.TYPE_SAFETY.key}_notes"] = f"Found {any_types} use(s) of 'any' type"
        if type_assertions > 0:
            scores[QualityDimension.TYPE_SAFETY.key] = min(
                scores[QualityDimension.TYPE_SAFETY.key], 1
            )
            notes = scores.get(f"{QualityDimension.TYPE_SAFETY.key}_notes", "")
            addition = f"{type_assertions} type assertion(s)"
            scores[f"{QualityDimension.TYPE_SAFETY.key}_notes"] = notes + f" {addition}" if notes else addition

        # Maintainability - check for long functions, magic numbers
        long_functions = issue_counts.get('long_function', 0)
        magic_numbers = issue_counts.get('magic_number', 0)
        if long_functions > 0:
            scores[QualityDimension.MAINTAINABILITY.key] = 1
            scores[f"{QualityDimension.MAINTAINABILITY.key}_notes"] = f"Found {long_functions} long function(s) (>50 lines)"
        if magic_numbers > 2:
            scores[QualityDimension.MAINTAINABILITY.key] = min(
                scores[QualityDimension.MAINTAINABILITY.key], 1
            )

        # UX Polish - check for long lines (readability)
        long_lines = issue_counts.get('long_line', 0)
        encoding_artifacts = issue_counts.get('encoding_artifact', 0)
        if long_lines > 5:
            scores[QualityDimension.UX_POLISH.key] = 1
            scores[f"{QualityDimension.UX_POLISH.key}_notes"] = f"Found {long_lines} long line(s) affecting readability"
        if encoding_artifacts > 0:
            scores[QualityDimension.UX_POLISH.key] = min(
                scores[QualityDimension.UX_POLISH.key], 1
            )
            notes = scores.get(f"{QualityDimension.UX_POLISH.key}_notes", "")
            addition = f"{encoding_artifacts} encoding artifact(s)"
            scores[f"{QualityDimension.UX_POLISH.key}_notes"] = notes + f" {addition}" if notes else addition

        # Static Analyzability - check for string concatenation (dynamic patterns)
        string_concats = issue_counts.get('string_concat', 0)
        if string_concats > 3:
            scores[QualityDimension.STATIC_ANALYZABILITY.key] = 1
            scores[f"{QualityDimension.STATIC_ANALYZABILITY.key}_notes"] = "Excessive string concatenation detected"

        # Boundary Discipline - check for FIXME comments (indicates known issues)
        fixmes = issue_counts.get('fixme_comment', 0)
        if fixmes > 0:
            scores[QualityDimension.BOUNDARY_DISCIPLINE.key] = 1
            scores[f"{QualityDimension.BOUNDARY_DISCIPLINE.key}_notes"] = f"Found {fixmes} FIXME comment(s)"

        return scores

    def _check_failure_condition(self, condition: str, analysis_results: List[CodeAnalysisResult]) -> bool:
        """
        Check if a failure condition is violated.

        Args:
            condition: The condition text to check
            analysis_results: Analysis results to examine

        Returns:
            True if condition is violated (failure), False otherwise
        """
        if not analysis_results:
            return False

        # Count issues
        has_console_logs = any(
            i.issue_type == 'console_log'
            for r in analysis_results
            for i in r.issues
        )
        has_todos = any(
            i.issue_type == 'todo_comment'
            for r in analysis_results
            for i in r.issues
        )
        has_fixmes = any(
            i.issue_type == 'fixme_comment'
            for r in analysis_results
            for i in r.issues
        )

        condition_lower = condition.lower()

        if 'console' in condition_lower or 'prototype' in condition_lower:
            return has_console_logs
        if 'placeholder' in condition_lower or 'todo' in condition_lower:
            return has_todos or has_fixmes

        return False

    def _get_dimension_checklist(self, dimension: QualityDimension, context: str) -> List[str]:
        """Get checklist items for a specific dimension."""
        checklists = {
            QualityDimension.CONTRACT_ADHERENCE: [
                "Use exact interfaces/endpoints defined by the system",
                "Do not invent workarounds for uncertain contracts",
                "Preserve naming conventions at appropriate boundaries",
                "Do not rename fields just for convenience"
            ],
            QualityDimension.ARCHITECTURAL_CONSISTENCY: [
                "Use shared utilities and clients instead of duplicating configuration",
                "Maintain consistency in error handling, state management, and data flow",
                "Do not reinvent patterns that already exist",
                "Extend existing abstractions rather than creating parallel ones"
            ],
            QualityDimension.STATE_CORRECTNESS: [
                "Source of truth is explicit and singular",
                "State survives edge cases (deep links, refreshes, restarts)",
                "Avoid fragile parsing or brittle assumptions",
                "Route/state remain synchronized across navigation methods"
            ],
            QualityDimension.PRODUCTION_READINESS: [
                "No console logs in user-facing code paths",
                "No dead buttons or non-functional CTAs",
                "No placeholder data or 'for now' assumptions",
                "Every user-facing action has a real implementation"
            ],
            QualityDimension.ERROR_RESILIENCE: [
                "Loading states are explicit",
                "Empty states are explicit and suggest next steps",
                "Error states are recoverable where possible",
                "Meaningful error categories are distinguished",
                "Service layer handles technical details; presentation layer handles display"
            ],
            QualityDimension.UX_POLISH: [
                "Labels and messages are readable and intentional",
                "Disabled states prevent invalid actions proactively",
                "No encoding artifacts or awkward interactions",
                "Buttons do what they claim",
                "State transitions feel deliberate"
            ],
            QualityDimension.TYPE_SAFETY: [
                "Avoid excessive type casting",
                "Do not collapse rich shapes into lossy substitutes without reason",
                "Functions return established types whenever possible",
                "Component interfaces are explicit and narrow"
            ],
            QualityDimension.STATIC_ANALYZABILITY: [
                "Avoid dynamic patterns that defeat optimization or detection",
                "Use explicit conditional branches over dynamic string interpolation where tools matter",
                "Keep styling and configuration aligned with tool expectations"
            ],
            QualityDimension.BOUNDARY_DISCIPLINE: [
                "Mock/test mode is explicit and contained",
                "Mock data matches real types",
                "Live mode does not keep mock-only artifacts",
                "Boundaries are explicit, not leaky"
            ],
            QualityDimension.MAINTAINABILITY: [
                "Changes reduce duplication, not increase it",
                "Intent is obvious without reverse-engineering",
                "Future extensions are easier after the change",
                "Logic is centralized when it appears in multiple places"
            ]
        }

        return checklists.get(dimension, [])

    def _get_failure_conditions(self, context: str) -> List[str]:
        """Get automatic failure conditions."""
        base_conditions = [
            "Automated checks fail",
            "Prototype artifacts remain in user-visible paths",
            "Dead or non-functional UI elements exist",
            "Configuration duplication exists where sharing is possible",
            "Placeholder assumptions remain in merged flows",
            "Visible artifacts (encoding, mojibake) remain",
            "Mock behavior leaks into live flows unnecessarily"
        ]

        return base_conditions

    def _get_self_check_questions(self, context: str) -> List[str]:
        """Get final self-check questions."""
        return [
            "Does every action have a real implementation?",
            "Does every interface match the contract?",
            "Did I remove all prototype artifacts?",
            "Did I avoid duplicating existing utilities?",
            "Can the flow survive edge cases?",
            "Are all states (loading, empty, error) explicit?",
            "Is the surface free of artifacts and brittle patterns?",
            "Did all automated checks pass?"
        ]

    def run_adverse_review(self, files_changed: Optional[List[str]] = None,
                          context: str = "general") -> str:
        """
        Run an adverse code review - a critical examination of the completed code.

        This is the final step that looks for potential issues, weaknesses, and
        areas of concern from a skeptical perspective.

        Args:
            files_changed: List of files that were modified (optional)
            context: Context for the review (frontend, backend, merge, general)

        Returns:
            Formatted adverse review report
        """
        report = []
        analysis_results = self.analyze_files(files_changed) if files_changed else []

        # Header
        report.append("## [ADVERSE CODE REVIEW]")
        report.append("")
        report.append("*This is a critical examination designed to find potential issues.*")
        report.append("")

        # Review questions by category
        review_categories = self._get_adverse_review_categories(context)

        for category, questions in review_categories.items():
            report.append(f"### {category}")
            report.append("")
            for question in questions:
                report.append(f"- [ ] {question}")
            report.append("")

        # Red flags checklist
        report.append("### Red Flags to Watch For")
        report.append("")
        red_flags = self._get_red_flags(context)
        for flag in red_flags:
            report.append(f"- [ ] {flag}")
        report.append("")

        # File-specific review (if files provided)
        if files_changed:
            report.append("### Files Changed")
            report.append("")
            for file_path in files_changed:
                report.append(f"- `{file_path}`")
            report.append("")
            self._add_adverse_findings_section(report, analysis_results)
            report.append("")

        # Adverse review summary
        report.append("### Adverse Review Summary")
        report.append("")
        report.append("**If any of the above checkboxes are checked, investigate further.**")
        report.append("")
        report.append("**Remember:**")
        report.append("- The first implementation is rarely the best")
        report.append("- Simplicity is the ultimate sophistication")
        report.append("- If it feels wrong, it probably is")
        report.append("- Future maintainers will thank you for extra care now")
        report.append("")

        return "\n".join(report)

    def _add_adverse_findings_section(
        self,
        report_sections: List[str],
        analysis_results: List[CodeAnalysisResult],
    ) -> None:
        """Add concrete file-aware findings for the adverse review."""
        report_sections.append("### Concrete Findings")
        report_sections.append("")

        all_issues = self._collect_all_issues(analysis_results)
        if not all_issues:
            report_sections.append("- No concrete adverse findings were detected by automated file analysis.")
            report_sections.append("- Remaining review is limited to the generic checklist below.")
            return

        prioritized_issues = sorted(
            all_issues,
            key=lambda issue: (
                0 if issue.severity == 'error' else 1 if issue.severity == 'warning' else 2,
                issue.file,
                issue.line,
            )
        )

        for issue in prioritized_issues[:20]:
            report_sections.append(
                f"- `{issue.file}:{issue.line}` [{issue.severity}] {issue.message}"
            )
            if issue.suggestion:
                report_sections.append(f"  -> {issue.suggestion}")

    def _get_adverse_review_categories(self, context: str) -> Dict[str, List[str]]:
        """Get adverse review categories and questions."""
        base_categories = {
            "Design Decisions": [
                "Are there any design decisions that seem arbitrary or unexamined?",
                "Could this be simpler?",
                "Is there unnecessary abstraction or complexity?",
                "Are there hidden assumptions that could break?",
                "Is the separation of concerns clear?"
            ],
            "Error Handling": [
                "Are errors handled gracefully or just logged and ignored?",
                "Could error states lead to data corruption?",
                "Are there silent failures that could occur?",
                "Is error messaging helpful to users and developers?",
                "Are exceptions caught at the right level?"
            ],
            "Security Concerns": [
                "Are there any potential injection vulnerabilities?",
                "Is user input properly validated and sanitized?",
                "Are sensitive data properly protected?",
                "Are there any hardcoded secrets or credentials?",
                "Is authentication/authorization properly enforced?"
            ],
            "Performance Issues": [
                "Are there any obvious performance anti-patterns?",
                "Could large datasets cause memory issues?",
                "Are there unnecessary computations or iterations?",
                "Is caching used appropriately?",
                "Are there potential N+1 query problems?"
            ],
            "Maintainability": [
                "Will this code be easy to understand in 6 months?",
                "Are there any 'magic numbers' or hardcoded values?",
                "Is the code properly documented where needed?",
                "Are there any TODOs or FIXMEs that should be addressed?",
                "Could refactoring make this significantly cleaner?"
            ],
            "Testing Gaps": [
                "Are edge cases properly tested?",
                "Are error paths covered by tests?",
                "Is there adequate test isolation?",
                "Are there any untestable parts of the code?",
                "Do tests actually verify the intended behavior?"
            ]
        }

        # Context-specific additions
        if context == "frontend":
            base_categories["Frontend Concerns"] = [
                "Are there any memory leaks from event listeners or subscriptions?",
                "Is re-rendering optimized appropriately?",
                "Are there any accessibility issues?",
                "Is the code responsive to different screen sizes?",
                "Are there any browser compatibility concerns?"
            ]
        elif context == "backend":
            base_categories["Backend Concerns"] = [
                "Are database transactions properly managed?",
                "Is there proper rate limiting where needed?",
                "Are API responses properly paginated for large datasets?",
                "Is there proper logging for debugging production issues?",
                "Are there any race conditions in concurrent operations?"
            ]

        return base_categories

    def _get_red_flags(self, context: str) -> List[str]:
        """Get red flags to watch for."""
        base_flags = [
            "Code that says 'I don't know what I'm doing' (excessive comments explaining basics)",
            "Copy-pasted code without proper abstraction",
            "Type assertions or 'any' types used to avoid proper typing",
            "Dead code that isn't commented out or removed",
            "Functions/methods that are too long (>50 lines)",
            "Deep nesting (>3 levels) that suggests complexity issues",
            "Magic strings or numbers scattered throughout",
            "Catch-all exception handlers that swallow errors",
            "Direct database queries instead of using repositories",
            "Business logic in controllers/views instead of services"
        ]

        if context == "frontend":
            base_flags.extend([
                "Inline styles instead of proper styling",
                "Direct DOM manipulation instead of React patterns",
                "State duplication between component and store",
                "API calls in render methods instead of effects/hooks"
            ])
        elif context == "backend":
            base_flags.extend([
                "N+1 query patterns",
                "Missing database indexes on queried fields",
                "Synchronous operations that should be async",
                "Missing input validation at the API boundary"
            ])

        return base_flags

    def calculate_score(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate the quality score.

        Args:
            scores: Dictionary mapping dimension keys to scores (0-2)

        Returns:
            Dictionary with total, max, percentage, target, and passed status
        """
        total = sum(scores.values())
        percentage = (total / self.max_score) * 100
        passed = total >= self.target_score

        return {
            "total": total,
            "max": self.max_score,
            "percentage": percentage,
            "target": self.target_score,
            "passed": passed
        }

    def generate_report(self, scores: Dict[str, int], context: str = "general") -> str:
        """
        Generate a quality assessment report.

        Args:
            scores: Dictionary mapping dimension keys to scores (0-2)
            context: Context for the quality check

        Returns:
            Formatted quality assessment report
        """
        result = self.calculate_score(scores)

        report = []
        report.append("# Quality Assessment Report")
        report.append("")
        report.append(f"**Context:** {context}")
        report.append("")

        # Overall result
        status = "âœ“ PASS" if result["passed"] else "âœ— FAIL"
        report.append(f"## Overall: {result['total']}/{result['max']} ({result['percentage']:.0f}%) {status}")
        report.append("")

        # Dimension scores
        report.append("## Dimension Scores")
        report.append("")
        report.append("| Dimension | Score | Status |")
        report.append("|-----------|-------|--------|")

        for dimension in self.dimensions:
            score = scores.get(dimension.key, 0)
            if score == 2:
                status = "âœ“"
            elif score == 1:
                status = "âš "
            else:
                status = "âœ—"
            report.append(f"| {dimension.display_name} | {score}/2 | {status} |")

        report.append("")

        # Gaps
        gaps = [d for d in self.dimensions if scores.get(d.key, 0) < 2]
        if gaps:
            report.append("## Gaps Identified")
            report.append("")
            for gap in gaps:
                score = scores.get(gap.key, 0)
                report.append(f"- **{gap.display_name}**: Score {score}/2")
            report.append("")

        # Recommendations
        report.append("## Recommendations")
        report.append("")
        report.append("1. Address all gaps before merging")
        report.append("2. Run automated checks to verify fixes")
        report.append("3. Re-run quality check after fixes")
        report.append("")

        return "\n".join(report)


# Auto-trigger integration
class AutoQualityCheckIntegration:
    """Integration for automatic quality check after coding tasks."""

    def __init__(self):
        self.skill = QualityCheckSkill()
        self.enabled = True
        self.delay_ms = 1000

    def on_task_complete(self, task_info: Dict[str, Any]) -> str:
        """
        Called when a coding task is completed.

        Args:
            task_info: Dictionary containing task information

        Returns:
            Quality check report
        """
        if not self.enabled:
            return ""

        context = task_info.get("context", "general")
        files_changed = task_info.get("files_changed", [])

        return f"""\n## [QUALITY CHECK TRIGGERED]

Your coding task has been completed. Running automatic quality assessment...

{self.skill.run_quality_check_with_adverse_review(context, files_changed)}

---

**Note:** Please review the quality check above and address any gaps before considering the task complete.
"""

    def toggle(self) -> bool:
        """Toggle auto quality check on/off."""
        self.enabled = not self.enabled
        return self.enabled


# Factory function
def create_quality_check_skill() -> QualityCheckSkill:
    """Factory function to create a quality check skill instance."""
    return QualityCheckSkill()


# Example usage
if __name__ == "__main__":
    skill = create_quality_check_skill()

    # Run a quality check
    report = skill.run_quality_check("frontend")
    print(report)
