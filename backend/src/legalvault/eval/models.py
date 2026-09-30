from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    query: str
    expect_query_mode: str | None = None
    min_citations: int | None = None
    max_citations: int | None = None
    required_section_numbers: tuple[int, ...] = ()
    required_ipc_section_numbers: tuple[int, ...] = ()
    min_confidence: str | None = None
    source: str = "handwritten"


@dataclass(frozen=True)
class EvalCaseResult:
    question_id: str
    query: str
    passed: bool
    failure_reason: str | None
    metrics: dict[str, Any]
    query_mode: str | None = None


@dataclass
class EvalReport:
    results: list[EvalCaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for result in self.results if result.passed)

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    def pass_rate_for_mode(self, query_mode: str) -> float | None:
        mode_results = [
            result
            for result in self.results
            if result.query_mode == query_mode
        ]
        if not mode_results:
            return None
        passed = sum(1 for result in mode_results if result.passed)
        return passed / len(mode_results)

    def check_invite_gate(self, thresholds: EvalThresholds) -> InviteGateResult:
        failures = invite_gate_failures(self, thresholds)
        return InviteGateResult(
            passed=len(failures) == 0,
            overall_pass_rate=self.pass_rate,
            failures=failures,
        )


@dataclass(frozen=True)
class EvalThresholds:
    min_overall_pass_rate: float
    section_lookup_min_pass_rate: float
    ipc_mapping_min_pass_rate: float
    fact_pattern_min_pass_rate: float


@dataclass(frozen=True)
class InviteGateResult:
    passed: bool
    overall_pass_rate: float
    failures: tuple[str, ...]


def invite_gate_failures(
    report: EvalReport, thresholds: EvalThresholds
) -> tuple[str, ...]:
    failures: list[str] = []
    if report.pass_rate < thresholds.min_overall_pass_rate:
        failures.append(
            f"overall pass rate {report.pass_rate:.2%} "
            f"< {thresholds.min_overall_pass_rate:.2%}"
        )
    mode_checks = (
        ("section_lookup", thresholds.section_lookup_min_pass_rate),
        ("ipc_to_bns_mapping", thresholds.ipc_mapping_min_pass_rate),
        ("fact_pattern_analysis", thresholds.fact_pattern_min_pass_rate),
    )
    for mode, minimum in mode_checks:
        rate = report.pass_rate_for_mode(mode)
        if rate is None:
            continue
        if rate < minimum:
            failures.append(
                f"{mode} pass rate {rate:.2%} < {minimum:.2%}"
            )
    return tuple(failures)
