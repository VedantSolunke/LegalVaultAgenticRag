"""Offline eval question set runner (ADR-0013)."""

from legalvault.eval.models import EvalQuestion, EvalThresholds
from legalvault.eval.runner import evaluate_response, run_eval_in_process


def test_evaluate_section_lookup_passes_with_expected_citation() -> None:
    question = EvalQuestion(
        id="section-101",
        query="What is BNS section 101?",
        expect_query_mode="section_lookup",
        min_citations=1,
        required_section_numbers=(101,),
    )
    response = {
        "query_mode": "section_lookup",
        "citations": [{"section_number": 101, "act": "BNS"}],
        "confidence": "high",
    }
    result = evaluate_response(question, response)
    assert result.passed
    assert result.metrics["citation_count"] == 1


def test_evaluate_fails_when_query_mode_mismatch() -> None:
    question = EvalQuestion(
        id="ipc-302",
        query="What happened to IPC section 302?",
        expect_query_mode="ipc_to_bns_mapping",
    )
    response = {
        "query_mode": "section_lookup",
        "citations": [],
        "confidence": "low",
    }
    result = evaluate_response(question, response)
    assert not result.passed
    assert "query_mode" in result.failure_reason


def test_run_eval_in_process_against_fixture_corpus() -> None:
    questions = [
        EvalQuestion(
            id="section-101",
            query="What is BNS section 101?",
            expect_query_mode="section_lookup",
            min_citations=1,
            required_section_numbers=(101,),
        ),
        EvalQuestion(
            id="out-of-corpus",
            query="What does BNSS say about bail?",
            expect_query_mode="out_of_corpus",
            max_citations=0,
        ),
    ]
    report = run_eval_in_process(questions)
    assert report.total == 2
    assert report.passed == 2
    assert report.pass_rate == 1.0


def test_report_fails_invite_gate_when_below_threshold() -> None:
    thresholds = EvalThresholds(
        min_overall_pass_rate=1.0,
        section_lookup_min_pass_rate=1.0,
        ipc_mapping_min_pass_rate=1.0,
        fact_pattern_min_pass_rate=1.0,
    )
    questions = [
        EvalQuestion(
            id="section-101",
            query="What is BNS section 101?",
            expect_query_mode="section_lookup",
            min_citations=1,
            required_section_numbers=(101,),
        ),
        EvalQuestion(
            id="bad",
            query="What is BNS section 101?",
            expect_query_mode="ipc_to_bns_mapping",
        ),
    ]
    report = run_eval_in_process(questions)
    gate = report.check_invite_gate(thresholds)
    assert not gate.passed
    assert gate.overall_pass_rate < 1.0
