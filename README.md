# Content Rewards Bot

نظام شبه آلي (semi-automated) لإدارة حملات Content Rewards عبر ثلاث منصات:
TikTok, YouTube Shorts, Instagram Reels — باستخدام الـ APIs الرسمية فقط.

⚠️ **مهم جدًا قبل الاستخدام:**
- هذا المشروع يستخدم فقط واجهات API الرسمية لكل منصة (لا Selenium/Playwright، لا تجاوز CAPTCHA، لا محاكاة تسجيل دخول).
- يجب أن تقرأ وتلتزم بشروط استخدام كل منصة (Platform Terms) وشروط كل حملة Content Rewards بشكل يدوي قبل تفعيل النشر التلقائي.
- بعض المنصات (خصوصًا TikTok وInstagram) تتطلب مراجعة تطبيقك (App Review) قبل السماح لك بالنشر الفعلي على حسابات غير حسابك الخاص في وضع الاختبار.
- YouTube يفرض حصة يومية (quota) على رفع الفيديوهات — راقبها.
- ابدأ دائمًا بوضع `DRY_RUN=true` للتأكد أن الأنابيب (pipeline) تعمل بشكل صحيح قبل النشر الفعلي.

## البنية

```
content-rewards-bot/
├── config.yaml              # إعدادات الحملات والحدود (سعر 1000 مشاهدة، الحد الأقصى للدفع...)
├── .env.example              # نموذج لمتغيرات البيئة (API keys)
├── requirements.txt
├── src/
│   ├── scanner/               # اكتشاف واختيار الحملات
│   ├── editor/                # تجهيز الفيديو (قص، captions، 9:16، hook)
│   ├── publishers/             # نشر عبر TikTok / YouTube / Instagram
│   ├── analytics/               # متابعة الأداء وحساب الأرباح
│   └── pipeline.py              # الأنبوب الكامل الذي يربط كل شيء
├── data/campaigns.json          # مثال لبيانات حملة
└── .github/workflows/           # تشغيل مجدول عبر GitHub Actions
```

## خطوات التشغيل

1. انسخ `.env.example` إلى `.env` واملأ مفاتيحك:
   ```bash
   cp .env.example .env
   ```
2. ثبّت المتطلبات:
   ```bash
   pip install -r requirements.txt
   ```
3. عدّل `config.yaml` حسب شروط الحملات التي تستهدفها.
4. شغّل بوضع تجريبي أولاً:
   ```bash
   DRY_RUN=true python -m src.pipeline
   ```
5. بعد التأكد أن كل شيء يعمل صح، شغّل بدون DRY_RUN.

## ملاحظة عن "Content Rewards"

الـ Scanner في هذا المشروع مبني بشكل عام (generic) لأن "Content Rewards" قد يشير لأكثر من منصة/برنامج
(مثل برامج مكافآت المحتوى الخاصة بمنصات معينة). عدّل `src/scanner/campaign_scanner.py`
ليتصل بمصدر بيانات الحملات الفعلي الذي تستخدمه (API أو ملف بيانات يدوي).

## رفعه على GitHub

```bash
cd content-rewards-bot
git init
git add .
git commit -m "Initial commit: content rewards automation pipeline"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO_NAME.git
git push -u origin main
```

**تأكد أن ملف `.env` مضاف إلى `.gitignore` ولا يُرفع أبدًا إلى GitHub** (موجود بالفعل في `.gitignore`).
