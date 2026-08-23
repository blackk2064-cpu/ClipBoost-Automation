"""Quality Check: يتأكد أن الفيديو يستوفي شروط الحملة قبل النشر."""
from moviepy.editor import VideoFileClip


def check_video(path: str, config: dict, had_captions: bool) -> tuple[bool, list]:
    """يرجّع (passed, errors)."""
    errors = []
    qc = config.get("quality_check", {})

    clip = VideoFileClip(path)
    duration = clip.duration
    w, h = clip.size
    clip.close()

    if duration < qc.get("min_duration_seconds", 5):
        errors.append(f"مدة الفيديو قصيرة جدًا: {duration:.1f}s")

    if qc.get("require_captions") and not had_captions:
        errors.append("الفيديو يتطلب كابشنز ولم تُضَف")

    target_ratio = 9 / 16
    actual_ratio = w / h
    if abs(actual_ratio - target_ratio) > 0.02:
        errors.append(f"نسبة الأبعاد غير صحيحة: {w}x{h}")

    return (len(errors) == 0, errors)
