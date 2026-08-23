"""
YouTube Shorts Publisher
========================
يستخدم YouTube Data API v3 الرسمي.
التوثيق: https://developers.google.com/youtube/v3/guides/uploading_a_video

يتطلب:
- مشروع في Google Cloud Console مع YouTube Data API v3 مفعّلة
- OAuth 2.0 credentials (Client ID/Secret) + Refresh Token لحسابك
- الفيديو العمودي القصير (<= 60s) يُصنَّف تلقائيًا كـ Short من يوتيوب

ملاحظة: هناك حصة يومية (quota) على الرفع — راقب استهلاكك في Cloud Console.
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .base import BasePublisher


class YouTubePublisher(BasePublisher):
    platform_name = "youtube_shorts"

    def __init__(self):
        super().__init__()
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    def _get_service(self):
        creds = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )
        return build("youtube", "v3", credentials=creds)

    def publish(self, video_path: str, metadata: dict) -> dict:
        if self.dry_run:
            return self._dry_run_result(video_path, metadata)

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            return {"success": False, "post_id": None, "error": "بيانات YouTube OAuth ناقصة"}

        try:
            youtube = self._get_service()

            # أضف #Shorts في العنوان/الوصف لزيادة فرص التصنيف كـ Short
            title = metadata.get("title", "")[:100]
            description = metadata.get("description", "")
            if "#shorts" not in description.lower():
                description += "\n#Shorts"

            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": metadata.get("hashtags", []),
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "private",  # غيّرها إلى public بعد التأكد
                    "selfDeclaredMadeForKids": False,
                },
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = request.execute()

            return {"success": True, "post_id": response.get("id"), "error": None}

        except Exception as e:
            return {"success": False, "post_id": None, "error": str(e)}
