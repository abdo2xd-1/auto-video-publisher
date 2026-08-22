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

# ==========================================================
# 1. مصادر Reddit لصيانة الهاردوير والأجهزة (بدون حظر 100%)
# ==========================================================
DEFAULT_TARGET_SOURCES = [
    "https://www.reddit.com/r/soldering/hot/",
    "https://www.reddit.com/r/ElectronicsRepair/hot/",
    "https://www.reddit.com/r/techsupportgore/hot/",
    "https://www.reddit.com/r/pcmasterrace/hot/",
    "https://www.reddit.com/r/diyelectronics/hot/"
]

HISTORY_FILE = "published_history.txt"

# ==========================================================
# 2. إدارة السجل لمنع تكرار الفيديوهات
# ==========================================================
def get_published_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def record_published_video(video_id):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{video_id}\n")

# ==========================================================
# 3. دالة التحميل المباشر
# ==========================================================
def download_video(custom_video_url=None):
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': False,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': False
    }

    sources = [custom_video_url] if custom_video_url else DEFAULT_TARGET_SOURCES.copy()
    random.shuffle(sources)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for source in sources:
            if not source:
                continue
            try:
                print(f"🔍 جارٍ جلب الفيديوهات من: {source}")
                result = ydl.extract_info(source, download=False)
                if not result:
                    continue

                entries = result.get('entries', [result]) if 'entries' in result else [result]
                for entry in entries:
                    if not entry:
                        continue
                    v_id = str(entry.get('id', ''))
                    duration = entry.get('duration', 0)
                    webpage_url = entry.get('webpage_url') or entry.get('url')

                    # التحقق من أن الفيديو مدته أقل من 90 ثانية وغير مكرر
                    if v_id and v_id not in published_ids and (duration is None or duration <= 90):
                        title = entry.get('title', 'Hardware Repair & Electronics Tips')
                        print(f"📥 تم العثور على فيديو جديد: {title}")
                        
                        target_url = webpage_url if webpage_url else f"https://www.reddit.com/r/{v_id}"
                        info = ydl.extract_info(target_url, download=True)
                        filepath = ydl.prepare_filename(info)
                        
                        if not os.path.exists(filepath):
                            base, _ = os.path.splitext(filepath)
                            filepath = f"{base}.mp4"

                        if os.path.exists(filepath):
                            print(f"✅ تم تنزيل الفيديو بنجاح إلى: {filepath}")
                            return filepath, title, v_id
            except Exception as err:
                print(f"⚠️ خطأ أثناء المعالجة: {err}")
                continue

    print("ℹ️ لم يتم العثور على فيديوهات جديدة غير مكررة حالياً.")
    sys.exit(0)

# ==========================================================
# 4. النشر على YouTube Shorts
# ==========================================================
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

        clean_title = (title[:80] + " #Shorts") if len(title) > 80 else (title + " #Shorts")
        body = {
            "snippet": {
                "title": clean_title,
                "description": f"{title}\n\n#repair #electronics #hardware #shorts #tech",
                "tags": ["repair", "electronics", "hardware", "soldering", "tech"],
                "categoryId": "28"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        print(f"✅ تم النشر على YouTube Shorts بنجاح! الرابط: https://youtu.be/{response.get('id')}")
    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى YouTube: {e}")

# ==========================================================
# 5. النشر على Instagram Reels
# ==========================================================
def publish_to_instagram(video_path, title):
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        print("⏩ تخطي Instagram: بيانات الحساب غير موجودة.")
        return

    try:
        cl = Client()
        cl.login(username, password)
        caption = f"{title}\n.\n#repair #hardware #tech #electronics #soldering #fix"
        media = cl.clip_upload(video_path, caption=caption)
        print(f"✅ تم النشر على Instagram Reels بنجاح: {media.pk}")
    except Exception as e:
        print(f"❌ خطأ أثناء النشر على Instagram: {e}")

# ==========================================================
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

# ==========================================================
# 7. نقطة الدخول الرئيسية
# ==========================================================
def main():
    direct_video_url = os.getenv("CUSTOM_VIDEO_URL", None)
    
    print("🚀 بدء تشغيل السكريبت لجلب ونشر الفيديو...")
    raw_video_path, title, video_id = download_video(custom_video_url=direct_video_url)

    if raw_video_path and os.path.exists(raw_video_path):
        print(f"📦 بدء نشر الفيديو: {title}")

        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN")
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN_2")
        publish_to_instagram(raw_video_path, title)

        record_published_video(video_id)
        send_notification(f"✅ تم نشر فيديو جديد: {title}")

        try:
            os.remove(raw_video_path)
        except OSError:
            pass

        print("🎉 اكتملت المهمة ونُشر الفيديو بنجاح!")

if __name__ == "__main__":
    main()
