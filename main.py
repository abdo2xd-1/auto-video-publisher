import os
import sys
import json
import random
import time
import requests
from instagrapi import Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================================
# 1. الكلمات المفتاحية للبحث عن محتوى الصيانة والهاردوير
# ==========================================================
SEARCH_KEYWORDS = [
    "pc hardware repair",
    "motherboard soldering repair",
    "gpu repair electronics",
    "microsoldering fix",
    "laptop motherboard repair",
    "appliance repair technician",
    "electronics circuit repair",
    "washing machine repair tips",
    "smd soldering tech"
]

HISTORY_FILE = "published_history.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# ==========================================================
# 2. إدارة السجل لمنع التكرار
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
# 3. جلب وتحميل الفيديو بدون علامة مائية وبدون حظر
# ==========================================================
def download_video():
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    keywords = SEARCH_KEYWORDS.copy()
    random.shuffle(keywords)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    for kw in keywords:
        print(f"🔍 جارٍ البحث عن فيديوهات لكلمة: '{kw}'...")
        try:
            # استخدام سيرفر TikWM للبحث وسحب روابط MP4 المباشرة
            api_url = "https://www.tikwm.com/api/feed/search"
            payload = {"keywords": kw, "count": 12, "cursor": 0, "web": 1}
            
            res = requests.post(api_url, data=payload, headers=headers, timeout=20)
            if res.status_code != 200:
                print(f"⚠️ استجابة غير صالحة من السيرفر ({res.status_code})")
                continue

            data = res.json()
            videos = data.get("data", {}).get("videos", [])

            for item in videos:
                v_id = str(item.get("video_id") or item.get("id"))
                duration = item.get("duration", 0)
                download_url = item.get("play") # رابط الفيديو بدون علامة مائية
                title = item.get("title", "Hardware Repair & Tech Tips")

                # التحقق من أن الفيديو لم يُنشر مسبقاً ومدته مناسبة للـ Shorts
                if v_id and v_id not in published_ids and download_url and (duration <= 90):
                    print(f"📥 تم العثور على فيديو غير مكرر: {title}")
                    
                    filepath = f"downloads/{v_id}.mp4"
                    print(f"⏳ جارٍ تنزيل ملف الفيديو المباشر...")
                    
                    with requests.get(download_url, headers=headers, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        with open(filepath, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    f.write(chunk)

                    if os.path.exists(filepath) and os.path.getsize(filepath) > 100000:
                        print(f"✅ تم تحميل الفيديو بنجاح ({round(os.path.getsize(filepath)/(1024*1024), 2)} MB)")
                        return filepath, title, v_id

        except Exception as e:
            print(f"⚠️ خطأ أثناء البحث عن '{kw}': {e}")
            continue

    print("ℹ️ تم فحص كافة المصادر ولم يتم العثور على فيديوهات جديدة.")
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

        # تنظيف العنوان وإضافة الهاشتاج
        clean_title = (title[:80] + " #Shorts") if len(title) > 80 else (title + " #Shorts")
        
        body = {
            "snippet": {
                "title": clean_title,
                "description": f"{title}\n\n#repair #electronics #hardware #shorts #tech #soldering",
                "tags": ["repair", "electronics", "hardware", "soldering", "tech", "shorts"],
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
        print(f"✅ تم الرفع على YouTube بنجاح! الرابط: https://youtu.be/{response.get('id')}")
    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى YouTube ({token_env}): {e}")

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
    print("🚀 بدء تشغيل الأتمتة لجلب ونشر فيديوهات الهاردوير والصيانة...")
    raw_video_path, title, video_id = download_video()

    if raw_video_path and os.path.exists(raw_video_path):
        print(f"📦 بدء نشر الفيديو: {title}")

        # الرفع على القنوات
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN")
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN_2")
        publish_to_instagram(raw_video_path, title)

        # تسجيل المعرف وإرسال الإشعار
        record_published_video(video_id)
        send_notification(f"✅ تم نشر فيديو جديد: {title}")

        # تنظيف الملفات المؤقتة
        try:
            os.remove(raw_video_path)
        except OSError:
            pass

        print("🎉 اكتملت المهمة ونُشر الفيديو بنجاح!")

if __name__ == "__main__":
    main()
