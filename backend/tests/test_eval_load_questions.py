def test_load_questions_jsonl_uses_question_field(tmp_path) -> None:
    from legalvault.eval.load_questions import load_questions_jsonl

    path = tmp_path / "sample.jsonl"
    path.write_text(
        '{"question": "What is BNS section 101?"}\n',
        encoding="utf-8",
    )
    questions = load_questions_jsonl(path)
    assert len(questions) == 1
    assert questions[0].query == "What is BNS section 101?"
    assert questions[0].source == "qa_jsonl"
