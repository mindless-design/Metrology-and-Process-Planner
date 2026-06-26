"""Structured validation and health-check result models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(str, Enum):
    """Supported diagnostic severities for project validation."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationIssue:
    """One structured validation diagnostic with repair guidance."""

    severity: ValidationSeverity
    category: str
    location: str
    message: str
    repair_suggestion: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize the issue to JSON-compatible structured data."""

        return {
            "severity": self.severity.value,
            "category": self.category,
            "location": self.location,
            "message": self.message,
            "repair_suggestion": self.repair_suggestion,
        }


@dataclass(frozen=True)
class ValidationReport:
    """A named collection of structured validation issues."""

    subject: str
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def ok(self) -> bool:
        """Return whether the report has no error-level issues."""

        return not any(issue.severity is ValidationSeverity.ERROR for issue in self.issues)

    def extend(self, other: ValidationReport) -> ValidationReport:
        """Return a report containing issues from this report and another."""

        return ValidationReport(self.subject, self.issues + other.issues)

    def to_dict(self) -> dict[str, object]:
        """Serialize the report to JSON-compatible structured data."""

        return {
            "subject": self.subject,
            "ok": self.ok,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class HealthCheckItem:
    """One line item in the project health check."""

    name: str
    passed: bool
    issue_count: int = 0

    def to_dict(self) -> dict[str, object]:
        """Serialize the item to JSON-compatible data."""

        return {
            "name": self.name,
            "passed": self.passed,
            "issue_count": self.issue_count,
        }


@dataclass(frozen=True)
class HealthCheckReport:
    """Aggregated project health result for merge readiness."""

    items: tuple[HealthCheckItem, ...]
    reports: tuple[ValidationReport, ...]

    @property
    def score(self) -> int:
        """Return an integer health score from zero to one hundred."""

        if not self.items:
            return 100
        passed = sum(1 for item in self.items if item.passed)
        return round(100 * passed / len(self.items))

    def to_dict(self) -> dict[str, object]:
        """Serialize the health report to JSON-compatible structured data."""

        return {
            "score": self.score,
            "items": [item.to_dict() for item in self.items],
            "reports": [report.to_dict() for report in self.reports],
        }


def issue(
    severity: ValidationSeverity,
    category: str,
    location: str,
    message: str,
    repair_suggestion: str,
) -> ValidationIssue:
    """Build a validation issue with a consistent field order."""

    return ValidationIssue(severity, category, location, message, repair_suggestion)
