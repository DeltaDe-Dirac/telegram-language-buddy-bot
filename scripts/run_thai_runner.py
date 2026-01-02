import os
import logging
import sys

# Ensure project root is on sys.path so `src` package is importable
sys.path.insert(0, os.getcwd())

# Load .env values similar to tests
try:
    from dotenv import dotenv_values
    env = dotenv_values(os.path.join(os.getcwd(), '.env'))
    for k, v in env.items():
        if v is not None and k not in os.environ:
            os.environ[k] = v
except Exception:
    pass

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

from src.models.voice_transcriber import VoiceTranscriber

fixture = os.path.join('tests', 'fixtures', 'thai_voice.ogg')
if not os.path.exists(fixture):
    print('THAI FIXTURE MISSING:', fixture)
    raise SystemExit(2)

with open(fixture, 'rb') as f:
    audio_bytes = f.read()

vt = VoiceTranscriber()

# Monkeypatch the download method to return local bytes
vt._download_voice_file = lambda file_id: audio_bytes

print('Calling transcribe_voice_message_with_confidence...')
result = vt.transcribe_voice_message_with_confidence('TEST_FILE_ID', confidence_threshold=0.65)
print('DONE. result is', type(result))
if result:
    print('TEXT:', result.text)
    print('CONFIDENCE:', result.confidence)
    try:
        print('RAW_RESPONSE:', result.raw_response)
    except Exception:
        pass
else:
    print('No result returned')
