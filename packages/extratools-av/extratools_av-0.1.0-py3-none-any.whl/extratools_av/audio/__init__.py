from typing import cast

import numpy as np
from moviepy.audio.AudioClip import AudioClip
from moviepy.audio.fx import AudioNormalize
from moviepy.audio.io.AudioFileClip import AudioFileClip


def get_max_volume(clip: AudioClip | str) -> float:
    if isinstance(clip, str):
        clip = AudioFileClip(clip)

    return float(cast("np.float64", clip.max_volume()))


def scale_volume(clip: AudioClip | str, *, target_volume: float = 0.5) -> AudioClip:
    if isinstance(clip, str):
        clip = AudioFileClip(clip)

    max_volume: float = get_max_volume(clip)

    return cast("AudioClip", clip.with_volume_scaled(target_volume / max_volume))


def normalize(clip: AudioClip | str) -> AudioClip:
    if isinstance(clip, str):
        clip = AudioFileClip(clip)

    return cast("AudioClip", clip.with_effects([AudioNormalize()]))
