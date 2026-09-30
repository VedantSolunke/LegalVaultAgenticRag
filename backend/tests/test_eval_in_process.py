"""In-process eval uses the shared research graph (fixture corpus), not HTTP auth."""

from pathlib import Path

from legalvault.eval.load_questions import load_questions_json
from legalvault.eval.runner import run_eval_in_process


def test_eval_question_set_passes_on_fixture_corpus() -> None:
    questions_path = Path(__file__).resolve().parents[1] / "eval" / "questions.json"
    questions = load_questions_json(questions_path)
    report = run_eval_in_process(questions)
    assert report.passed == report.total
    assert report.pass_rate == 1.0
