"""
ClipBoost Telegram Bot
=======================
بوت تلغرام يستقبل فيديو (ملف أو رابط) مع شروط الحملة، يجهّزه
(قص + تحويل 9:16 + hook + وصف + هاشتاغات)، ويرسله جاهزًا بنفس المحادثة/القناة.

طريقة الاستخدام داخل تلغرام:
أرسل فيديو (أو رابط) مع كابشن/رسالة بهذا الشكل:

رابط: https://... (اختياري لو رفعت فيديو مباشرة)
هوك: النص اللي يطلع أول الفيديو
وصف: وصف الفيديو
هاشتاغ: #tag1 #tag2 #tag3
مدة: 30 (اختياري، بالثواني، افتراضي 60)
"""
import os
import re
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

from video_processor import process_video

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ضع_التوكن_هنا")


def parse_campaign_text(text: str) -> dict:
    """يستخرج رابط/هوك/وصف/هاشتاغ/مدة من نص الرسالة."""
    result = {
        "url": None,
        "hook": None,
        "description": "",
        "hashtags": [],
        "max_duration": 60,
    }
    if not text:
        return result

    url_match = re.search(r"رابط\s*:\s*(\S+)", text)
    if url_match:
        result["url"] = url_match.group(1)

    hook_match = re.search(r"هوك\s*:\s*(.+)", text)
    if hook_match:
        result["hook"] = hook_match.group(1).split("\n")[0].strip()

    desc_match = re.search(r"وصف\s*:\s*(.+)", text)
    if desc_match:
        result["description"] = desc_match.group(1).split("\n")[0].strip()

    hashtag_match = re.search(r"هاشتاغ\s*:\s*(.+)", text)
    if hashtag_match:
        tags_line = hashtag_match.group(1).split("\n")[0]
        result["hashtags"] = re.findall(r"#\S+", tags_line)

    duration_match = re.search(r"مدة\s*:\s*(\d+)", text)
    if duration_match:
        result["max_duration"] = int(duration_match.group(1))

    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا 👋\n\n"
        "أرسل فيديو مباشرة، أو رابط، مع رسالة بهذا الشكل:\n\n"
        "رابط: https://...\n"
        "هوك: النص اللي يطلع أول الفيديو\n"
        "وصف: وصف الفيديو\n"
        "هاشتاغ: #tag1 #tag2\n"
        "مدة: 30\n\n"
        "وراح أرجع لك الفيديو جاهز للنشر 🎬"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.caption or message.text or ""
    campaign = parse_campaign_text(text)

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, "input.mp4")
        output_path = os.path.join(tmp_dir, "output.mp4")

        status = await message.reply_text("⏳ جاري تجهيز الفيديو...")

        try:
            if message.video:
                file = await message.video.get_file()
                await file.download_to_drive(input_path)
            elif message.document and message.document.mime_type == "video/mp4":
                file = await message.document.get_file()
                await file.download_to_drive(input_path)
            elif campaign["url"]:
                await status.edit_text("⏳ جاري تحميل الفيديو من الرابط...")
                download_video_from_url(campaign["url"], input_path)
            else:
                await status.edit_text(
                    "❌ ما فيه فيديو ولا رابط. أرسل فيديو مباشرة أو حط سطر 'رابط: ...'"
                )
                return

            await status.edit_text("⏳ جاري القص والتحرير...")
            process_video(
                input_path=input_path,
                output_path=output_path,
                hook_text=campaign["hook"],
                max_duration=campaign["max_duration"],
            )

            caption_parts = []
            if campaign["description"]:
                caption_parts.append(campaign["description"])
            if campaign["hashtags"]:
                caption_parts.append(" ".join(campaign["hashtags"]))
            final_caption = "\n\n".join(caption_parts) or "الفيديو جاهز ✅"

            await status.delete()
            with open(output_path, "rb") as video_file:
                await message.reply_video(video_file, caption=final_caption)

        except Exception as e:
            await status.edit_text(f"❌ صار خطأ: {e}")


def download_video_from_url(url: str, output_path: str) -> None:
    """يحمّل فيديو من رابط عام (يوتيوب/تيكتوك/إلخ) عبر yt-dlp."""
    import yt_dlp

    ydl_opts = {
        "outtmpl": output_path,
        "format": "mp4/best",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main():
    if "ضع_" in BOT_TOKEN:
        raise SystemExit(
            "❌ لازم تحط التوكن حق البوت أولاً في متغير البيئة TELEGRAM_BOT_TOKEN "
            "أو مباشرة بأعلى الملف."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            (filters.VIDEO | filters.Document.VIDEO | filters.TEXT) & ~filters.COMMAND,
            handle_message,
        )
    )

    print("✅ البوت شغّال... اتركه يشتغل ولا تسكر البرنامج.")
    app.run_polling()


if __name__ == "__main__":
    main()
