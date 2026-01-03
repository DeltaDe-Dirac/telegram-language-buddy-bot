import os
import pytest

from src.models.free_translator import FreeTranslator

# Simple mock response for OpenAI API
class MockOpenAIResponse:
    def __init__(self, content: str):
        self._content = content

    def raise_for_status(self):
        # Simulate successful HTTP status
        pass

    def json(self):
        # Return structure matching OpenAI chat completion response
        return {
            "choices": [
                {"message": {"content": self._content}}
            ]
        }


@pytest.mark.integration
@pytest.mark.skipif(os.getenv('RUN_INTEGRATION') != '1', reason='integration tests disabled')
def test_translation_fallback_to_openai(monkeypatch):
    """Integration test: ensure FreeTranslator falls back to OpenAI when Google Translate fails.

    The test monkey-patches the internal Google Translate call to return ``None``
    and mocks ``requests.post`` to simulate a successful OpenAI response.
    """

    # Ensure an OpenAI key is present (dummy value is fine for the mock)
    # Use monkeypatch to set env var so it's automatically restored after test
    monkeypatch.setenv('OPENAI_API_KEY', 'dummy-key')

    # Force the Google Translate path to fail by returning None
    def fake_google_translate(*args, **kwargs):
        return None
    monkeypatch.setattr(FreeTranslator, "_translate_googletrans", staticmethod(fake_google_translate))

    # Mock the OpenAI HTTP request
    expected_translation = "Hello world"
    def fake_post(*args, **kwargs):
        return MockOpenAIResponse(expected_translation)
    monkeypatch.setattr('requests.post', fake_post)

    translator = FreeTranslator()
    result = translator.translate_text("some text", target_lang="en", source_lang="auto")

    assert result == expected_translation, "Fallback to OpenAI did not produce expected translation"
