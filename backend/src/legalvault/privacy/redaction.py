"""Pattern-based PII redaction for persisted messages (ADR-0012)."""

import re

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
)
_PHONE_RE = re.compile(
    r"""
    (?<!\d)
    (?:\+?\d{1,3}[\s.-]?)?
    (?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{3,5}
    (?!\d)
    """,
    re.VERBOSE,
)


def redact_message(text: str) -> str:
    """Return a copy of text with obvious email and phone patterns replaced."""
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = _PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    return redacted
