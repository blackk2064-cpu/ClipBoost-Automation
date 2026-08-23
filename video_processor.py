"""
Video Processor
================
نسخة مبسّطة من معالجة الفيديو خاصة ببوت تلغرام:
قص المدة + تحويل 9:16 + إضافة نص hook بالبداية.
"""
from pathlib import Path
from typing import Optional

from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip


def resize_to_9x16(clip: VideoFileClip) -> VideoFileClip:
    target_ratio = 9 / 16
    w, h = clip.size
    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 0.01:
        return clip

    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        clip = clip.crop(x_center=w / 2, width=new_w)
    else:
        new_h = int(w / target_ratio)
        clip = clip.crop(y_center=h / 2, height=new_h)

    return clip


def add_hook_text(clip: VideoFileClip, hook_text: str, duration: float = 3) -> VideoFileClip:
    txt_clip = (
        TextClip(
            hook_text,
            fontsize=60,
            color="white",
            font="Arial-Bold",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(clip.w * 0.9, None),
        )
        .set_position(("center", "top"))
        .set_duration(min(duration, clip.duration))
    )
    return CompositeVideoClip([clip, txt_clip])


def process_video(
    input_path: str,
    output_path: str,
    hook_text: Optional[str] = None,
    max_duration: float = 60,
    hook_duration: float = 3,
) -> str:
    clip = VideoFileClip(input_path)

    if clip.duration > max_duration:
        clip = clip.subclip(0, max_duration)

    clip = resize_to_9x16(clip)

    if hook_text:
        clip = add_hook_text(clip, hook_text, hook_duration)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return output_path
