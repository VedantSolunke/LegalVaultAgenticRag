"""Derive short session titles from the user's first prompt."""

from legalvault.privacy.redaction import redact_message

SESSION_TITLE_MAX_LENGTH = 48


def session_title_from_first_prompt(query: str) -> str:
    text = redact_message(query.strip())
    text = " ".join(text.split())
    if not text:
        return "New chat"
    if len(text) <= SESSION_TITLE_MAX_LENGTH:
        return text
    trimmed = text[: SESSION_TITLE_MAX_LENGTH - 1].rstrip()
    return f"{trimmed}…"
