"""Report and Finding dataclasses for custodian operations."""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Finding:
    severity: Severity
    category: str  # links, decay, frontmatter, relationships, orphans
    message: str
    file_path: Optional[Path] = None
    fixed: bool = False


@dataclass
class Report:
    operation: str
    dry_run: bool = False
    findings: List[Finding] = field(default_factory=list)

    def add(
        self, severity: Severity, category: str, message: str, file_path: Optional[Path] = None, fixed: bool = False
    ) -> None:
        self.findings.append(Finding(severity, category, message, file_path, fixed))

    def error(self, category: str, message: str, **kw) -> None:
        self.add(Severity.ERROR, category, message, **kw)

    def warning(self, category: str, message: str, **kw) -> None:
        self.add(Severity.WARNING, category, message, **kw)

    def info(self, category: str, message: str, **kw) -> None:
        self.add(Severity.INFO, category, message, **kw)

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == Severity.WARNING]

    @property
    def fixed_count(self) -> int:
        return sum(1 for f in self.findings if f.fixed)

    def summary(self) -> Dict[str, Any]:
        by_category: Dict[str, int] = {}
        for f in self.findings:
            by_category[f.category] = by_category.get(f.category, 0) + 1
        return {
            "total_findings": len(self.findings),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "fixed": self.fixed_count,
            "by_category": by_category,
        }

    def render_markdown(self) -> str:
        s = self.summary()
        lines = [
            f"# Custodian Report: {self.operation}",
            f"**Dry run**: {self.dry_run}",
            "",
            "## Summary",
            f"- Findings: {s['total_findings']}",
            f"- Errors: {s['errors']}",
            f"- Warnings: {s['warnings']}",
            f"- Fixed: {s['fixed']}",
        ]
        if self.errors:
            lines += ["", "## Errors"]
            for f in self.errors:
                path_str = f"  `{f.file_path}`" if f.file_path else ""
                fixed_str = " (FIXED)" if f.fixed else ""
                lines.append(f"- [{f.category}]{path_str}: {f.message}{fixed_str}")
        if self.warnings:
            lines += ["", "## Warnings"]
            for f in self.warnings:
                path_str = f"  `{f.file_path}`" if f.file_path else ""
                lines.append(f"- [{f.category}]{path_str}: {f.message}")
        return "\n".join(lines)

    def render_json(self) -> str:
        return json.dumps(
            {
                "operation": self.operation,
                "dry_run": self.dry_run,
                "summary": self.summary(),
                "findings": [
                    {
                        "severity": f.severity.value,
                        "category": f.category,
                        "message": f.message,
                        "file_path": str(f.file_path) if f.file_path else None,
                        "fixed": f.fixed,
                    }
                    for f in self.findings
                ],
            },
            indent=2,
        )
