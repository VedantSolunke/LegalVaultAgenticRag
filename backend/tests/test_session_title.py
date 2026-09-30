from legalvault.sessions.title import SESSION_TITLE_MAX_LENGTH, session_title_from_first_prompt


def test_session_title_collapses_whitespace() -> None:
    assert session_title_from_first_prompt("  What is   BNS 101?  ") == "What is BNS 101?"


def test_session_title_truncates_long_prompts() -> None:
    long_query = "a" * 80
    title = session_title_from_first_prompt(long_query)
    assert len(title) == SESSION_TITLE_MAX_LENGTH
    assert title.endswith("…")


def test_session_title_redacts_pii() -> None:
    title = session_title_from_first_prompt("Email witness@example.com about section 101")
    assert "[REDACTED_EMAIL]" in title
    assert "witness@example.com" not in title
