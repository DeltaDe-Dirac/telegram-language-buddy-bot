import os
import pytest
import difflib

from unittest.mock import patch

# Load .env values when running tests so services (Google/AssemblyAI/OpenAI) are available
try:
    from dotenv import dotenv_values
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env = dotenv_values(env_path)
    for k, v in env.items():
        if v is not None and k not in os.environ:
            os.environ[k] = v
except Exception:
    # best-effort; continue if dotenv not installed or .env missing
    pass

from src.models.voice_transcriber import VoiceTranscriber
from src.models.free_translator import FreeTranslator


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


@pytest.mark.integration
@pytest.mark.skipif(os.getenv('RUN_INTEGRATION') != '1', reason='integration tests disabled')
def test_thai_voice_transcription_and_translation():
    """Integration: transcribe a local Thai voice file and translate to English.

    Place a Thai voice OGG file at `tests/fixtures/thai_voice.ogg` before running.
    If `OPENAI_API_KEY` is set and FreeTranslator output is low-quality, the test will
    optionally try OpenAI text translation as a fallback.
    """
    fixture_path = os.path.join('tests', 'fixtures', 'thai_voice.ogg')
    if not os.path.exists(fixture_path):
        pytest.skip(f"Voice fixture not found: {fixture_path}")

    # Read audio bytes
    with open(fixture_path, 'rb') as f:
        audio_bytes = f.read()

        vt = VoiceTranscriber()

    # Patch the _download_voice_file method to return our local bytes
    with patch.object(VoiceTranscriber, '_download_voice_file', return_value=audio_bytes):
        result = vt.transcribe_voice_message_with_confidence('FAKE_FILE_ID_FOR_TEST', confidence_threshold=0.65)

    assert result is not None, "Transcription failed for fixture"

    transcription_text = result.text
    assert transcription_text.strip(), "Empty transcription"

    # Translate transcription to English using FreeTranslator
    translator = FreeTranslator()
    translated = translator.translate_text(transcription_text, 'en', 'auto')

    # Basic quality check: translation should not be an error message
    assert translated and not translated.startswith('❌'), f"Translation failed or low quality: {translated}"

    # Optional: if similarity to an expected phrase is very low, user can provide expected text
    expected_env = os.getenv('EXPECTED_THAI_ENGLISH')
    if expected_env:
        sim = _similarity(expected_env, translated)
        if sim < 0.6:
            # Try OpenAI fallback if available
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                import requests
                system = "You are a precise translator. Translate to English without added commentary."
                user = f"Translate the following text to English:\n\n{transcription_text}"
                resp = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {openai_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'gpt-3.5-turbo',
                        'messages': [
                            {'role': 'system', 'content': system},
                            {'role': 'user', 'content': user}
                        ],
                        'temperature': 0.0
                    },
                    timeout=30
                )
                resp.raise_for_status()
                openai_out = resp.json()['choices'][0]['message']['content'].strip()
                sim2 = _similarity(expected_env, openai_out)
                assert sim2 >= 0.75, f"OpenAI fallback still low quality (sim={sim2:.2f}): {openai_out}"
            else:
                pytest.fail("Low-quality translation and no OPENAI_API_KEY for fallback")
