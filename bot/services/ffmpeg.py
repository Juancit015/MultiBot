import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def video_has_audio(video_path: Path) -> bool:
    probe = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries',
         'stream=codec_type', '-of', 'default=noprint_wrappers=1', str(video_path)],
        capture_output=True, timeout=10
    )
    return bool(probe.stdout.strip())


def merge_audio_into_video(video_path: Path, audio_path: Path) -> Path | None:
    """Fusiona audio MP3 en video MP4 usando FFmpeg."""
    output_path = video_path.parent / f"merged_{video_path.name}"
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0 and output_path.exists():
            logger.info(f"Audio incrustado en {output_path.name}")
            return output_path
        else:
            logger.warning(f"FFmpeg merge falló: {result.stderr.decode()[:200]}")
            return None
    except Exception as e:
        logger.warning(f"merge_audio_into_video error: {e}")
        return None


def extract_audio_from_video(video_path: Path) -> Path | None:
    """Extrae audio MP3 de un video usando FFmpeg directamente."""
    audio_path = video_path.with_suffix('.mp3')
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-vn',
            '-acodec', 'mp3',
            '-q:a', '2',
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0 and audio_path.exists() and audio_path.stat().st_size > 0:
            logger.info(f"Audio extraído: {audio_path.name}")
            return audio_path
        return None
    except Exception as e:
        logger.warning(f"extract_audio_from_video error: {e}")
        return None