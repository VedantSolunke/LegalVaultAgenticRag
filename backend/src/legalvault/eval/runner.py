from __future__ import annotations

from typing import Any, Protocol

import httpx
from fastapi.testclient import TestClient

from legalvault.eval.models import EvalCaseResult, EvalQuestion, EvalReport
from legalvault.main import create_app

_CONFIDENCE_ORDER = ("low", "medium", "high")


class ResearchClient(Protocol):
    def post_research(self, query: str) -> dict[str, Any]: ...


class InProcessResearchClient:
    def __init__(self, token: str = "test-user-token") -> None:
        self._client = TestClient(create_app())
        self._headers = {"Authorization": f"Bearer {token}"}

    def post_research(self, query: str) -> dict[str, Any]:
        response = self._client.post(
            "/research",
            json={"query": query},
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()


class HttpResearchClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}

    def post_research(self, query: str) -> dict[str, Any]:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self._base_url}/research",
                json={"query": query},
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()


def _confidence_at_least(actual: str, minimum: str) -> bool:
    try:
        return _CONFIDENCE_ORDER.index(actual) >= _CONFIDENCE_ORDER.index(minimum)
    except ValueError:
        return False


def evaluate_response(
    question: EvalQuestion, response: dict[str, Any]
) -> EvalCaseResult:
    citations = response.get("citations") or []
    query_mode = response.get("query_mode")
    confidence = response.get("confidence", "low")
    cited_sections = {
        int(c["section_number"])
        for c in citations
        if c.get("section_number") is not None
    }
    cited_ipc = {
        int(c["ipc_section_number"])
        for c in citations
        if c.get("ipc_section_number") is not None
    }
    metrics: dict[str, Any] = {
        "query_mode": query_mode,
        "citation_count": len(citations),
        "cited_section_numbers": sorted(cited_sections),
        "confidence": confidence,
    }

    if question.expect_query_mode and query_mode != question.expect_query_mode:
        return EvalCaseResult(
            question_id=question.id,
            query=question.query,
            passed=False,
            failure_reason=(
                f"expected query_mode {question.expect_query_mode}, got {query_mode}"
            ),
            metrics=metrics,
            query_mode=query_mode,
        )

    if question.min_citations is not None and len(citations) < question.min_citations:
        return EvalCaseResult(
            question_id=question.id,
            query=question.query,
            passed=False,
            failure_reason=(
                f"expected at least {question.min_citations} citations, "
                f"got {len(citations)}"
            ),
            metrics=metrics,
            query_mode=query_mode,
        )

    if question.max_citations is not None and len(citations) > question.max_citations:
        return EvalCaseResult(
            question_id=question.id,
            query=question.query,
            passed=False,
            failure_reason=(
                f"expected at most {question.max_citations} citations, "
                f"got {len(citations)}"
            ),
            metrics=metrics,
            query_mode=query_mode,
        )

    missing_sections = set(question.required_section_numbers) - cited_sections
    if missing_sections:
        return EvalCaseResult(
            question_id=question.id,
            query=question.query,
            passed=False,
            failure_reason=f"missing cited sections {sorted(missing_sections)}",
            metrics=metrics,
            query_mode=query_mode,
        )

    missing_ipc = set(question.required_ipc_section_numbers) - cited_ipc
    if missing_ipc:
        return EvalCaseResult(
            question_id=question.id,
            query=question.query,
            passed=False,
            failure_reason=f"missing IPC mapping for {sorted(missing_ipc)}",
            metrics=metrics,
            query_mode=query_mode,
        )

    if question.min_confidence and not _confidence_at_least(
        str(confidence), question.min_confidence
    ):
        return EvalCaseResult(
            question_id=question.id,
            query=question.query,
            passed=False,
            failure_reason=(
                f"expected confidence >= {question.min_confidence}, got {confidence}"
            ),
            metrics=metrics,
            query_mode=query_mode,
        )

    return EvalCaseResult(
        question_id=question.id,
        query=question.query,
        passed=True,
        failure_reason=None,
        metrics=metrics,
        query_mode=query_mode,
    )


def run_eval(client: ResearchClient, questions: list[EvalQuestion]) -> EvalReport:
    report = EvalReport()
    for question in questions:
        response = client.post_research(question.query)
        report.results.append(evaluate_response(question, response))
    return report


def run_eval_in_process(
    questions: list[EvalQuestion], *, token: str = "test-user-token"
) -> EvalReport:
    return run_eval(InProcessResearchClient(token=token), questions)

