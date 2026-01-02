from pathlib import Path
import sys

def main():
    try:
        from gtts import gTTS
        import imageio_ffmpeg as ffmpeg
        import subprocess
    except Exception as e:
        print("Missing dependencies:", e)
        print("Run: python -m pip install gTTS imageio-ffmpeg")
        sys.exit(2)

    fixtures = Path(__file__).resolve().parents[1] / 'tests' / 'fixtures'
    fixtures.mkdir(parents=True, exist_ok=True)

    thai_text = 'สวัสดีครับ นี่คือการทดสอบการสังเคราะห์เสียงภาษาไทยสำหรับการแปล' 

    # Create MP3 via gTTS
    tts = gTTS(text=thai_text, lang='th')
    mp3_path = fixtures / 'thai_voice.mp3'
    ogg_path = fixtures / 'thai_voice.ogg'
    tts.save(str(mp3_path))
    print(f"Saved MP3 to {mp3_path}")

    # Use imageio-ffmpeg binary to convert mp3 -> ogg
    ffmpeg_exe = ffmpeg.get_ffmpeg_exe()
    print(f"Using ffmpeg at: {ffmpeg_exe}")

    # Prefer libopus if available, otherwise libvorbis
    cmd = [ffmpeg_exe, '-y', '-i', str(mp3_path), '-c:a', 'libopus', str(ogg_path)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        # fallback to libvorbis
        cmd = [ffmpeg_exe, '-y', '-i', str(mp3_path), '-c:a', 'libvorbis', str(ogg_path)]
        subprocess.run(cmd, check=True)

    print(f"Exported OGG to {ogg_path}")

if __name__ == '__main__':
    main()
