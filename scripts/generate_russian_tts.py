"""Generate a synthetic Russian voice OGG file for integration testing.

Uses gTTS to synthesize speech, then converts the MP3 to OGG using the bundled ffmpeg
binary from ``imageio-ffmpeg``. The resulting file is placed in ``tests/fixtures`` as
``russian_voice.ogg``.
"""

import os
from pathlib import Path

def main():
    try:
        from gtts import gTTS
        import imageio_ffmpeg as ffmpeg
        import subprocess
    except Exception as e:
        print("Missing dependencies – install with: pip install gTTS imageio-ffmpeg")
        raise

    fixtures = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)

    # Simple Russian sentence for testing
    russian_text = "Привет, это тестовое сообщение для проверки транскрипции и перевода."

    tts = gTTS(text=russian_text, lang="ru")
    mp3_path = fixtures / "russian_voice.mp3"
    ogg_path = fixtures / "russian_voice.ogg"
    tts.save(str(mp3_path))
    print(f"Saved MP3 to {mp3_path}")

    ffmpeg_exe = ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-y", "-i", str(mp3_path), "-c:a", "libopus", str(ogg_path)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        # fallback to libvorbis if opus not available
        cmd = [ffmpeg_exe, "-y", "-i", str(mp3_path), "-c:a", "libvorbis", str(ogg_path)]
        subprocess.run(cmd, check=True)

    print(f"Exported OGG to {ogg_path}")

if __name__ == "__main__":
    main()
