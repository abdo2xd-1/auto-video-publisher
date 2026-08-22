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
# 1. المجتمعات المستهدفة (صيانة هاردوير وإلكترونيات ولحام)
# ==========================================================
SUBREDDITS = [
    "soldering",
    "ElectronicsRepair",
    "techsupportgore",
    "pcmasterrace",
    "diyelectronics",
    "specializedtools"
]

HISTORY_FILE = "published_history.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# ==========================================================
# 2. إدارة سجل الفيديوهات المنشورة لمنع التكرار
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
# 3. جلب وتنزيل الفيديوهات عبر Reddit API مباشرة
# ==========================================================
def download_video(custom_video_url=None):
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    # في حال تمرير رابط مباشر
    if custom_video_url:
        return download_direct_url(custom_video_url)

    random_subs = SUBREDDITS.copy()
    random.shuffle(random_subs)

    headers = {"User-Agent": USER_AGENT}

    for sub in random_subs:
        api_url = f"https://www.reddit.com/r/{sub}/hot.json?limit=30"
        print(f"🔍 جارٍ فحص مجتمع: r/{sub}")
        
        try:
            res = requests.get(api_url, headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"⚠️ فشل الاتصال بـ r/{sub} (Status: {res.status_code})")
                continue

            data = res.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                p_data = post.get("data", {})
                post_id = p_data.get("id")
                is_video = p_data.get("is_video", False)
                title = p_data.get("title", "Hardware Repair & Tech Tips")
                permalink = p_data.get("permalink")

                # التحقق من أن المنشور يحتوي على فيديو ولم يتم نشره مسبقاً
                if is_video and post_id not in published_ids and permalink:
                    media_data = p_data.get("media", {}).get("reddit_video", {})
                    duration = media_data.get("duration", 0)

                    # شروط الفيديو القصير (أقل من 90 ثانية)
                    if duration and duration > 90:
                        continue

                    full_post_url = f"https://www.reddit.com{permalink}"
                    print(f"📥 تم العثور على فيديو جديد: {title}")

                    # تنزيل الفيديو المدمج بالصوت عبر yt-dlp برأس متصفح حقيقي
                    ydl_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': f'downloads/{post_id}.%(ext)s',
                        'quiet': True,
                        'no_warnings': True,
                        'http_headers': {'User-Agent': USER_AGENT}
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([full_post_url])

                    # التحقق من وجود الملف المحمل
                    for ext in ["mp4", "mkv", "webm"]:
                        candidate = f"downloads/{post_id}.{ext}"
                        if os.path.exists(candidate):
                            print(f"✅ تم تنزيل الفيديو بنجاح: {candidate}")
                            return candidate, title, post_id

        except Exception as e:
            print(f"⚠️ خطأ أثناء قراءة r/{sub}: {e}")
            continue

    print("ℹ️ تم فحص كافة المصادر ولم يتم العثور على فيديوهات جديدة غير مكررة.")
    sys.exit(0)

def download_direct_url(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {'User-Agent': USER_AGENT}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        return filepath, info.get('title', 'Repair Tips'), info.get('id')

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

        clean_title = (title[:85] + " #Shorts") if len(title) > 85 else (title + " #Shorts")
        body = {
            "snippet": {
                "title": clean_title,
                "description": f"{title}\n\n#repair #electronics #hardware #shorts #soldering",
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
        print(f"✅ تم الرفع والنشر على YouTube Shorts بنجاح! الرابط: https://youtu.be/{response.get('id')}")
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
# ==========================================================
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

        print("🎉 تمت كل العمليات ونُشر الفيديو بنجاح على قناتك!")

if __name__ == "__main__":
    main()
