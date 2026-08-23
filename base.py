"""Base Publisher: كل منصة ترث من هذا الكلاس وتطبّق publish()."""
import os
from abc import ABC, abstractmethod


class BasePublisher(ABC):
    platform_name: str = "base"

    def __init__(self):
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    @abstractmethod
    def publish(self, video_path: str, metadata: dict) -> dict:
        """
        ينشر الفيديو ويرجّع dict فيه على الأقل:
        {"success": bool, "post_id": str | None, "error": str | None}
        """
        raise NotImplementedError

    def _dry_run_result(self, video_path: str, metadata: dict) -> dict:
        print(f"[DRY_RUN][{self.platform_name}] كان سينشر: {video_path}")
        print(f"[DRY_RUN][{self.platform_name}] العنوان: {metadata.get('title')}")
        return {"success": True, "post_id": "DRY_RUN_ID", "error": None}
