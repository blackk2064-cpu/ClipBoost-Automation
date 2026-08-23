"""
Analytics & Profit Tracker
===========================
يسجّل كل منشور، ويحدّث المشاهدات لاحقًا (عبر استدعاء منفصل يقرأ من APIs
كل منصة - insights/analytics endpoints)، ويحسب الأرباح المتوقعة.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

LOG_FILE = Path(__file__).resolve().parents[2] / "data" / "posts_log.json"


def _load_log() -> list:
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_log(log: list) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def record_post(campaign: dict, platform: str, post_id: str, video_path: str) -> None:
    log = _load_log()
    log.append(
        {
            "campaign_id": campaign.get("id"),
            "campaign_name": campaign.get("name"),
            "rpm": campaign.get("rpm", 0),
            "platform": platform,
            "post_id": post_id,
            "video_path": video_path,
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "views": 0,
            "estimated_earnings": 0.0,
        }
    )
    _save_log(log)


def update_views(post_id: str, views: int) -> None:
    log = _load_log()
    for entry in log:
        if entry["post_id"] == post_id:
            entry["views"] = views
            entry["estimated_earnings"] = round((views / 1000) * entry.get("rpm", 0), 4)
            break
    _save_log(log)


def get_campaign_performance_summary() -> dict:
    """يرجّع أداء كل حملة (مجموع المشاهدات والأرباح) لدعم إعادة توزيع الإنتاج."""
    log = _load_log()
    summary = {}
    for entry in log:
        cid = entry["campaign_id"]
        if cid not in summary:
            summary[cid] = {"campaign_name": entry["campaign_name"], "total_views": 0, "total_earnings": 0.0, "posts": 0}
        summary[cid]["total_views"] += entry.get("views", 0)
        summary[cid]["total_earnings"] += entry.get("estimated_earnings", 0.0)
        summary[cid]["posts"] += 1
    return summary
