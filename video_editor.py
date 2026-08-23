"""
Video Editor
============
يجهّز الفيديو النهائي: تحويل المقاس إلى 9:16، إضافة hook بالبداية،
وإضافة كابشنز. يعتمد على moviepy (ويتطلب ffmpeg مثبتًا على النظام).

ملاحظة: توليد الكابشنز التلقائي (transcription) يحتاج محرك تحويل كلام
لنص (مثل Whisper). هذه الوحدة تفترض أنك تمرر ملف srt/نص جاهز، أو تربطها
بخدمة transcription خاصة بك عبر generate_captions().
"""
import os
from pathlib import Path
from typing import Optional

from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)


def resize_to_9x16(clip: VideoFileClip) -> VideoFileClip:
    """يحوّل الفيديو لمقاس عمودي 9:16 عبر crop مركزي."""
    target_ratio = 9 / 16
    w, h = clip.size
    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 0.01:
        return clip

    if current_ratio > target_ratio:
        # الفيديو أعرض من اللازم -> نقص من الجوانب
        new_w = int(h * target_ratio)
        x_center = w / 2
        clip = clip.crop(x_center=x_center, width=new_w)
    else:
        # الفيديو أطول من اللازم عموديًا بالفعل بشكل غير متوقع -> نقص من الأعلى/الأسفل
        new_h = int(w / target_ratio)
        y_center = h / 2
        clip = clip.crop(y_center=y_center, height=new_h)

    return clip


def add_hook_text(clip: VideoFileClip, hook_text: str, duration: float = 3) -> VideoFileClip:
    """يضيف نص hook في أول ثوانٍ من الفيديو لجذب الانتباه."""
    txt_clip = (
        TextClip(hook_text, fontsize=70, color="white", font="Arial-Bold", stroke_color="black", stroke_width=2)
        .set_position(("center", "top"))
        .set_duration(min(duration, clip.duration))
    )
    return CompositeVideoClip([clip, txt_clip])


def add_captions(clip: VideoFileClip, captions: list) -> VideoFileClip:
    """
    يضيف كابشنز بسيطة فوق الفيديو.
    captions: قائمة من dict مثل {"text": "...", "start": 0.0, "end": 2.5}
    """
    overlays = [clip]
    for c in captions:
        txt = (
            TextClip(c["text"], fontsize=48, color="white", font="Arial-Bold", stroke_color="black", stroke_width=1.5)
            .set_position(("center", "bottom"))
            .set_start(c["start"])
            .set_duration(c["end"] - c["start"])
        )
        overlays.append(txt)
    return CompositeVideoClip(overlays)


def trim_clip(clip: VideoFileClip, max_duration: float) -> VideoFileClip:
    if clip.duration > max_duration:
        return clip.subclip(0, max_duration)
    return clip


def process_video(
    input_path: str,
    output_path: str,
    hook_text: Optional[str] = None,
    captions: Optional[list] = None,
    max_duration: float = 60,
    hook_duration: float = 3,
) -> str:
    """يشغّل خط المعالجة الكامل على فيديو واحد ويحفظ الناتج."""
    clip = VideoFileClip(input_path)
    clip = trim_clip(clip, max_duration)
    clip = resize_to_9x16(clip)

    if captions:
        clip = add_captions(clip, captions)

    if hook_text:
        clip = add_hook_text(clip, hook_text, hook_duration)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    return output_path


def generate_metadata(campaign: dict) -> dict:
    """يولّد عنوان/وصف/هاشتاغات أساسية بناءً على بيانات الحملة."""
    hashtags = campaign.get("required_hashtags", [])
    disclosure = campaign.get("required_disclosure", "")
    title = campaign.get("name", "New Video")
    description = f"{title} {disclosure}".strip()
    if hashtags:
        description += " " + " ".join(hashtags)
    return {"title": title, "description": description, "hashtags": hashtags}
