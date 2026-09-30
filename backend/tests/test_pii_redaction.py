"""Unit tests for pattern-based PII redaction before persist (ADR-0012)."""

from legalvault.privacy.redaction import redact_message


def test_redacts_email_addresses() -> None:
    text = "Contact me at alice@example.com about the case."
    assert redact_message(text) == "Contact me at [REDACTED_EMAIL] about the case."


def test_redacts_phone_numbers() -> None:
    text = "My number is +91 98765 43210 for follow-up."
    assert "[REDACTED_PHONE]" in redact_message(text)
    assert "98765" not in redact_message(text)


def test_leaves_legal_queries_without_pii_unchanged() -> None:
    text = "What is BNS section 101?"
    assert redact_message(text) == text
