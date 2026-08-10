"""T15: probe de audio, extraccion y merge con FFmpeg real."""
import pytest

from tests.conftest import skip_if_no_ffmpeg

pytestmark = [skip_if_no_ffmpeg, pytest.mark.ffmpeg]


def test_T15_ffmpeg_probe_extraer_merge(media_fx):
    from bot.services.ffmpeg import (extract_audio_from_video,
                                      merge_audio_into_video, video_has_audio)
    va = media_fx["video_audio"]
    vn = media_fx["video_mute"]

    assert video_has_audio(va) is True, "video con audio detectado sin audio"
    assert video_has_audio(vn) is False, "video mudo detectado con audio"

    ex = extract_audio_from_video(va)
    assert ex and ex.stat().st_size > 0, "extracción de audio falló"

    merged = merge_audio_into_video(vn, ex)
    assert merged and video_has_audio(merged), "merge no produjo video con audio"