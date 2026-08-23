"""
TikTok Publisher
================
يستخدم TikTok Content Posting API الرسمي (v2).
التوثيق: https://developers.tiktok.com/doc/content-posting-api-get-started

يتطلب:
- تطبيق مسجّل ومعتمد في TikTok Developer Portal
- Access Token صالح بصلاحية video.publish
- في وضع Unaudited، النشر يذهب كـ "Private" فقط حتى تجتاز App Review

⚠️ هذا كود يوضّح تدفق الاستدعاءات؛ راجع التوثيق الرسمي دوريًا لأن الحقول قد تتغيّر.
"""
import os
import requests

from .base import BasePublisher

INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


class TikTokPublisher(BasePublisher):
    platform_name = "tiktok"

    def __init__(self):
        super().__init__()
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")

    def publish(self, video_path: str, metadata: dict) -> dict:
        if self.dry_run:
            return self._dry_run_result(video_path, metadata)

        if not self.access_token:
            return {"success": False, "post_id": None, "error": "TIKTOK_ACCESS_TOKEN غير موجود"}

        file_size = os.path.getsize(video_path)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }
        body = {
            "post_info": {
                "title": metadata.get("title", "")[:150],
                "privacy_level": "SELF_ONLY",  # غيّرها بعد اجتياز App Review
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1,
            },
        }

        try:
            init_resp = requests.post(INIT_URL, headers=headers, json=body, timeout=30)
            init_resp.raise_for_status()
            init_data = init_resp.json()

            upload_url = init_data["data"]["upload_url"]
            publish_id = init_data["data"]["publish_id"]

            with open(video_path, "rb") as f:
                video_bytes = f.read()

            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            }
            upload_resp = requests.put(upload_url, headers=upload_headers, data=video_bytes, timeout=120)
            upload_resp.raise_for_status()

            return {"success": True, "post_id": publish_id, "error": None}

        except requests.RequestException as e:
            return {"success": False, "post_id": None, "error": str(e)}
