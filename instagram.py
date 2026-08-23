"""
Instagram Reels Publisher
=========================
يستخدم Instagram Graph API (Content Publishing).
التوثيق: https://developers.facebook.com/docs/instagram-platform/content-publishing

يتطلب:
- حساب Instagram Business أو Creator مرتبط بصفحة Facebook
- Access Token بصلاحية instagram_content_publish
- الفيديو يجب أن يكون على رابط عام (public URL) يقدر Instagram يقرأه —
  يعني تحتاج ترفع الفيديو أولاً إلى تخزين سحابي (S3, Cloud Storage...) قبل هذه الخطوة.
"""
import os
import time
import requests

from .base import BasePublisher

GRAPH_BASE = "https://graph.facebook.com/v19.0"


class InstagramPublisher(BasePublisher):
    platform_name = "instagram_reels"

    def __init__(self):
        super().__init__()
        self.access_token = os.getenv("IG_ACCESS_TOKEN")
        self.ig_account_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")

    def publish(self, video_public_url: str, metadata: dict) -> dict:
        """
        ملاحظة: هنا video_public_url يجب أن يكون رابط عام للفيديو
        (بعد رفعه لتخزين سحابي)، وليس مسار ملف محلي.
        """
        if self.dry_run:
            return self._dry_run_result(video_public_url, metadata)

        if not all([self.access_token, self.ig_account_id]):
            return {"success": False, "post_id": None, "error": "بيانات Instagram ناقصة"}

        try:
            caption = metadata.get("description", "")

            # 1) إنشاء container
            create_resp = requests.post(
                f"{GRAPH_BASE}/{self.ig_account_id}/media",
                data={
                    "media_type": "REELS",
                    "video_url": video_public_url,
                    "caption": caption,
                    "access_token": self.access_token,
                },
                timeout=60,
            )
            create_resp.raise_for_status()
            container_id = create_resp.json()["id"]

            # 2) انتظار معالجة الفيديو
            status = "IN_PROGRESS"
            for _ in range(30):
                status_resp = requests.get(
                    f"{GRAPH_BASE}/{container_id}",
                    params={"fields": "status_code", "access_token": self.access_token},
                    timeout=30,
                )
                status = status_resp.json().get("status_code")
                if status == "FINISHED":
                    break
                if status == "ERROR":
                    return {"success": False, "post_id": None, "error": "فشلت معالجة الفيديو في Instagram"}
                time.sleep(10)

            if status != "FINISHED":
                return {"success": False, "post_id": None, "error": "انتهى الوقت قبل اكتمال المعالجة"}

            # 3) نشر container
            publish_resp = requests.post(
                f"{GRAPH_BASE}/{self.ig_account_id}/media_publish",
                data={"creation_id": container_id, "access_token": self.access_token},
                timeout=30,
            )
            publish_resp.raise_for_status()
            post_id = publish_resp.json()["id"]

            return {"success": True, "post_id": post_id, "error": None}

        except requests.RequestException as e:
            return {"success": False, "post_id": None, "error": str(e)}
