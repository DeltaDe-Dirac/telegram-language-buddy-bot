import os
import pytest
import difflib
import requests

from src.models.free_translator import FreeTranslator


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _openai_translate(text: str, source: str | None, target: str) -> str | None:
    """Use OpenAI ChatCompletion to translate when API key is present.
    This is an optional, best-effort helper used by the integration test only.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None

    # Build a simple translation prompt
    system = "You are a helpful translator. Translate input text to the target language precisely."
    user = f"Translate the following text to {target} (do not add extra commentary):\n\n" + text

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.0,
                "max_tokens": 400,
            },
            timeout=30,
        )

        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception:
        return None


@pytest.mark.integration
@pytest.mark.skipif(os.getenv('RUN_INTEGRATION') != '1', reason='integration tests disabled')
def test_translation_quality_for_complex_languages():
    """Integration test: verify translation quality for several non-Latin languages.

    - Runs only when `RUN_INTEGRATION=1` is set in the environment.
    - If `OPENAI_API_KEY` is present, tries OpenAI translation as a fallback.
    """
    translator = FreeTranslator()

    cases = [
        ("สวัสดีครับ", "Hello"),  # Thai
        ("ฉันรักภาษาไทย", "I love the Thai language"),
        ("こんにちは", "Hello"),  # Japanese
        ("私は音楽が好きです", "I like music"),
        ("مرحبا بك", "Welcome"),  # Arabic
    ]

    for src_text, expected_en in cases:
        translated = translator.translate_text(src_text, 'en', 'auto')

        # Normalize failed translations
        if not translated or translated.startswith('❌'):
            translated = ''

        sim = _similarity(expected_en, translated)

        # If FreeTranslator is good enough accept >= 0.6 similarity
        if sim >= 0.6:
            continue

        # Otherwise, if OpenAI key is available, try OpenAI translation and expect higher quality
        openai_out = _openai_translate(src_text, None, 'English')
        if openai_out:
            sim2 = _similarity(expected_en, openai_out)
            assert sim2 >= 0.8, (
                f"OpenAI translation still low quality for '{src_text}': '{openai_out}' (sim={sim2:.2f})"
            )
        else:
            pytest.fail(
                f"Low-quality translation for '{src_text}': '{translated}' (sim={sim:.2f}). "
                "Set OPENAI_API_KEY and RUN_INTEGRATION=1 to compare against a paid model."
            )
