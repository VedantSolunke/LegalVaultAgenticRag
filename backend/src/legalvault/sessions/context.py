"""Assemble short session history for the research graph."""


def build_retrieval_query(
    query: str,
    conversation_history: list[tuple[str, str]] | None,
) -> str:
    if not conversation_history:
        return query
    lines = [f"{role}: {body}" for role, body in conversation_history]
    lines.append(f"user: {query}")
    return "\n".join(lines)
