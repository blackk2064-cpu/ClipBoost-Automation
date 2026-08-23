"""
Campaign Scanner
=================
مسؤول عن جلب قائمة الحملات المتاحة وتصفيتها حسب المعايير في config.yaml.

⚠️ ملاحظة: لا توجد واجهة API عامة موحّدة اسمها "Content Rewards" — هذا
الاسم قد يشير لأكثر من برنامج/منصة. لذلك هذه الوحدة مبنية بشكل عام:
- إذا كان لديك مصدر بيانات (API) فعلي، عدّل fetch_campaigns() ليتصل به.
- إذا لم يوجد API، يمكنك تعبئة الحملات يدويًا في data/campaigns.json
  وسيقرأها الكود تلقائيًا كخيار احتياطي.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import requests

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "campaigns.json"


def fetch_campaigns() -> List[Dict[str, Any]]:
    """يجلب الحملات من API خارجي إن كان متاحًا، وإلا من ملف محلي."""
    source_url = os.getenv("CAMPAIGNS_SOURCE_URL")
    api_key = os.getenv("CAMPAIGNS_API_KEY")

    if source_url:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        resp = requests.get(source_url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # fallback: ملف بيانات محلي (تعبئة يدوية)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return []


def filter_campaigns(
    campaigns: List[Dict[str, Any]], filters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """يطبق معايير الاختيار: rpm, payout cap, content type, platforms."""
    min_rpm = filters.get("min_rpm", 0)
    max_payout_cap = filters.get("max_payout_cap", 0)
    allowed_types = set(filters.get("allowed_content_types", []))
    allowed_platforms = set(filters.get("allowed_platforms", []))

    selected = []
    for c in campaigns:
        if c.get("rpm", 0) < min_rpm:
            continue
        if max_payout_cap and c.get("payout_cap", 0) < max_payout_cap:
            continue
        if allowed_types and c.get("content_type") not in allowed_types:
            continue
        if allowed_platforms and not (
            set(c.get("platforms", [])) & allowed_platforms
        ):
            continue
        selected.append(c)

    # الأفضل أداءً (rpm) أولاً
    selected.sort(key=lambda c: c.get("rpm", 0), reverse=True)
    return selected


def get_selected_campaigns(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    campaigns = fetch_campaigns()
    return filter_campaigns(campaigns, config.get("campaign_filters", {}))
