import os
import sys
import json
import random
import time
import requests
import yt_dlp
from instagrapi import Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 1. قائمة مصادر المحتوى (هاردوير وصيانة أجهزة)
# ==========================================
DEFAULT_TARGET_CHANNELS = [
    # بحث يوتيوب الذكي لضمان جلب فيديوهات جديدة دائماً بدون حظر
    "ytsearch15:pc hardware repair shorts",
    "ytsearch15:gpu motherboard repair shorts",
    "ytsearch15:microsoldering repair shorts",
    "ytsearch15:appliance repair technician shorts",
    "ytsearch15:washing machine fix shorts",
    "ytsearch15:hvac cooling repair shorts",
    "ytsearch15:electronics teardown and fix shorts",
    "ytsearch15:laptop motherboard repair shorts",
    "ytsearch15:smd soldering electronics shorts",
    "ytsearch15:home appliance electrical fix shorts"
]

HISTORY_FILE = "published_history.txt"

# ==========================================
# 2. إدارة سجل الفيديوهات المنشورة لمنع التكرار
# ==========================================
def get_published_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def record_published_video(video_id):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{video_id}\n")

# ==========================================
# 3. دالة تحميل الفيديو عبر yt-dlp مع محاكاة الموبايل
# ==========================================
def download_video(custom_video_url=None):
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    # إعدادات yt-dlp لتجاوز حظر يوتيوب عبر محاكاة عميل Android
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }

    sources = [custom_video_url] if custom_video_url else DEFAULT_TARGET_CHANNELS.copy()
    random.shuffle(sources)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for source in sources:
            if not source:
                continue
            try:
                print(f"🔍 جارٍ فحص المصدر: {source}")
                result = ydl.extract_info(source, download=False)
                if not result:
                    continue

                entries = result.get('entries', [result]) if 'entries' in result else [result]
                for entry in entries:
                    if not entry:
                        continue
                    v_id = entry.get('id')
                    duration = entry.get('duration', 0)

                    # التأكد من أنه فيديو قصير (أقل من 90 ثانية) وغير مكرر
                    if v_id and v_id not in published_ids and (duration is None or duration <= 90):
                        print(f"📥 تم العثور على فيديو جديد: {entry.get('title')}")
                        info = ydl.extract_info(f"https://www.youtube.com/watch?v={v_id}", download=True)
                        filepath = ydl.prepare_filename(info)
                        
                        # التأكد من الامتداد بعد الدمج
                        if not os.path.exists(filepath):
                            base, _ = os.path.splitext(filepath)
                            filepath = f"{base}.mp4"

                        return filepath, entry.get('title', 'Hardware Repair Tips'), v_id
            except Exception as err:
                print(f"⚠️ خطأ أثناء الفحص: {err}")
                continue

    # الخروج الآمن دون إيقاف الـ Workflow بخطأ أحمر
    print("ℹ️ لم يتم العثور على أي فيديو جديد غير مكرر حالياً. إنهاء المهمة بنجاح.")
    sys.exit(0)

# ==========================================
# 4. النشر على YouTube Shorts
# ==========================================
def publish_to_youtube(video_path, title, token_env):
    refresh_token = os.getenv(token_env)
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")

    if not all([refresh_token, client_id, client_secret]):
        print(f"⏩ تخطي النشر على YouTube ({token_env}): البيانات غير مكتملة.")
        return

    try:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:90] + " #Shorts",
                "description": f"{title}\n\n#repair #electronics #hardware #shorts",
                "tags": ["repair", "electronics", "hardware", "soldering", "howto"],
                "categoryId": "28"  # Science & Technology
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        print(f"✅ تم النشر على YouTube بنجاح: https://youtu.be/{response.get('id')}")
    except Exception as e:
        print(f"❌ خطأ أثناء النشر على YouTube: {e}")

# ==========================================
# 5. النشر على Instagram Reels
# ==========================================
def publish_to_instagram(video_path, title):
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        print("⏩ تخطي النشر على Instagram: بيانات تسجيل الدخول غير متوفرة.")
        return

    try:
        cl = Client()
        cl.login(username, password)
        caption = f"{title}\n.\n#repair #hardware #tech #electronics #soldering #fix"
        media = cl.clip_upload(video_path, caption=caption)
        print(f"✅ تم النشر على Instagram Reels بنجاح: {media.pk}")
    except Exception as e:
        print(f"❌ خطأ أثناء النشر على Instagram: {e}")

# ==========================================
# 6. إشعارات Green API (WhatsApp)
# ==========================================
def send_notification(message):
    id_instance = os.getenv("GREEN_ID_INSTANCE")
    api_token = os.getenv("GREEN_API_TOKEN")

    if not id_instance or not api_token:
        return

    try:
        url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
        payload = {"chatId": "status@broadcast", "message": message}
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

# ==========================================
# 7. نقطة الدخول الرئيسية (Main)
# ==========================================
def main():
    direct_video_url = os.getenv("CUSTOM_VIDEO_URL", None)
    
    print("🚀 بدء تشغيل أتمتة جلب ونشر الفيديوهات...")
    raw_video_path, title, video_id = download_video(custom_video_url=direct_video_url)

    if raw_video_path and os.path.exists(raw_video_path):
        print(f"📦 جاري النشر للفيديو: {title}")

        # النشر على القنوات المحددة
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN")
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN_2")
        publish_to_instagram(raw_video_path, title)

        # حفظ المعرف لمنع تكراره مستقبلاً
        record_published_video(video_id)
        send_notification(f"✅ تم نشر فيديو جديد بنجاح: {title}")

        # تنظيف الملفات المؤقتة
        try:
            os.remove(raw_video_path)
        except OSError:
            pass

        print("🎉 تمت جميع المهام بنجاح!")

if __name__ == "__main__":
    main()
