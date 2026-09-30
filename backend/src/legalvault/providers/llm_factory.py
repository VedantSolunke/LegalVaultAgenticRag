from legalvault.config import get_settings
from legalvault.providers.stubs import StubLLMProvider


def get_llm_provider() -> StubLLMProvider:
    settings = get_settings()
    if settings.gemini_api_key:
        from legalvault.providers.gemini import GeminiLLMProvider

        return GeminiLLMProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            fallback=StubLLMProvider(),
        )
    return StubLLMProvider()
