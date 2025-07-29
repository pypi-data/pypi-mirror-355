from collections.abc import Iterable
from datetime import timedelta
from typing import Literal, cast

from moviepy import Effect
from moviepy.audio.AudioClip import AudioClip
from moviepy.video.fx.AccelDecel import AccelDecel
from moviepy.video.fx.Loop import Loop
from moviepy.video.fx.MakeLoopable import MakeLoopable
from moviepy.video.VideoClip import VideoClip


def match_audio_duration(
    video_clip: VideoClip,
    audio_clip: AudioClip | float | Iterable[AudioClip | float],
    *,
    padding: timedelta = timedelta(seconds=0.25),
    mode: Literal["scale", "loop"] = "scale",
    loop_fadein: timedelta | None = timedelta(seconds=1),
) -> VideoClip:
    audio_clips: Iterable[AudioClip | float] = (
        audio_clip if isinstance(audio_clip, Iterable)
        else [audio_clip]
    )

    audio_duration: float = sum(
        (
            (
                audio_clip.duration if isinstance(audio_clip, AudioClip)
                else audio_clip
            ) + padding.seconds
            for audio_clip in audio_clips
        ),
        start=padding.seconds,
    )

    effects: list[Effect] = []

    match mode:
        case "scale":
            effects.append(
                AccelDecel(audio_duration),
            )
        case "loop":
            if loop_fadein:
                effects.append(
                    MakeLoopable(overlap_duration=loop_fadein.seconds),
                )

            effects.append(
                Loop(duration=audio_duration),
            )
        case _:
            raise ValueError

    return cast(
        "VideoClip",
        video_clip.with_effects(effects),
    )
