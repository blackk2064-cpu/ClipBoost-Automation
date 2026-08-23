"""
Pipeline الرئيسي:
Content Rewards -> Campaign Scanner -> AI Editor -> Quality Check -> Publisher -> Analytics
"""
import os
import yaml
from dotenv import load_dotenv

from src.scanner.campaign_scanner import get_selected_campaigns
from src.editor.video_editor import process_video, generate_metadata
from src.editor.quality_check import check_video
from src.publishers.tiktok import TikTokPublisher
from src.publishers.youtube import YouTubePublisher
from src.publishers.instagram import InstagramPublisher
from src.analytics.tracker import record_post

load_dotenv()

PUBLISHERS = {
    "tiktok": TikTokPublisher(),
    "youtube_shorts": YouTubePublisher(),
    "instagram_reels": InstagramPublisher(),
}


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline():
    config = load_config()
    campaigns = get_selected_campaigns(config)

    if not campaigns:
        print("لا توجد حملات مطابقة للمعايير حاليًا.")
        return

    print(f"تم اختيار {len(campaigns)} حملة/حملات.")

    for campaign in campaigns:
        print(f"\n--- معالجة: {campaign.get('name')} ---")

        source_video = campaign.get("source_video_url")
        if not source_video:
            print("لا يوجد فيديو مصدر لهذه الحملة، تخطي.")
            continue

        output_path = f"output/{campaign['id']}.mp4"
        video_cfg = config.get("video_editing", {})

        try:
            process_video(
                input_path=source_video,
                output_path=output_path,
                hook_text=campaign.get("hook_text", campaign.get("name")),
                max_duration=video_cfg.get("max_clip_duration_seconds", 60),
                hook_duration=video_cfg.get("hook_duration_seconds", 3),
            )
        except Exception as e:
            print(f"فشل تجهيز الفيديو: {e}")
            continue

        passed, errors = check_video(
            output_path, config, had_captions=video_cfg.get("add_captions", False)
        )
        if not passed:
            print(f"فشل فحص الجودة: {errors}")
            continue

        metadata = generate_metadata(campaign)

        for platform in campaign.get("platforms", []):
            publisher = PUBLISHERS.get(platform)
            if not publisher:
                print(f"لا يوجد Publisher لمنصة: {platform}")
                continue

            result = publisher.publish(output_path, metadata)
            if result["success"]:
                print(f"✅ نُشر على {platform}: {result['post_id']}")
                record_post(campaign, platform, result["post_id"], output_path)
            else:
                print(f"❌ فشل النشر على {platform}: {result['error']}")


if __name__ == "__main__":
    run_pipeline()
