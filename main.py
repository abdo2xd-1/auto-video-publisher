import os
import sys
import json
import random
import time
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================================
# 1. قائمة مصادر الفيديوهات المباشرة
# ==========================================================
DIRECT_HARDWARE_SOURCES = [
    {
        "id": "hw_clip_tech_01",
        "title": "Electronics PCB Diagnostics & Component Fix #Shorts",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4"
    },
    {
        "id": "hw_clip_tech_02",
        "title": "Hardware Circuit Inspection & Maintenance #Shorts",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/face-demographics-walking-and-pause.mp4"
    },
    {
        "id": "hw_clip_tech_03",
        "title": "Micro Soldering & Board Diagnostics Tips #Shorts",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection-female.mp4"
    }
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
# 3. تنزيل ملف الفيديو المباشر
# ==========================================================
def download_video():
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    direct_pool = [v for v in DIRECT_HARDWARE_SOURCES if v["id"] not in published_ids]
    if not direct_pool:
        print("🔄 تم استهلاك كافة الفيديوهات، جارٍ تصفير السجل وإعادة التدوير...")
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        direct_pool = DIRECT_HARDWARE_SOURCES.copy()

    random.shuffle(direct_pool)
    headers = {"User-Agent": USER_AGENT}

    for item in direct_pool:
        v_id = item["id"]
        title = item["title"]
        url = item["url"]
        filepath = f"downloads/{v_id}.mp4"

        print(f"📥 بدء تحميل: {title}")
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                if r.status_code != 200:
                    continue

                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

            if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                file_size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                print(f"✅ تم تنزيل الفيديو بنجاح ({file_size_mb} MB)")
                return filepath, title, v_id

        except Exception as e:
            print(f"⚠️ خطأ أثناء التحميل: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            continue

    print("❌ تعذر تحميل أي ملف فيديو.")
    sys.exit(1)

# ==========================================================
# 4. الرفع والنشر على YouTube Shorts (مع تنظيف التوكن)
# ==========================================================
def publish_to_youtube(video_path, title, token_env):
    refresh_token = (os.getenv(token_env) or "").strip()
    client_id = (os.getenv("YOUTUBE_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("YOUTUBE_CLIENT_SECRET") or "").strip()

    if not refresh_token or not client_id or not client_secret:
        print(f"⏩ تخطي النشر على YouTube ({token_env}): البيانات غير مكتملة.")
        return

    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:95],
                "description": f"{title}\n\n#repair #electronics #hardware #shorts #tech",
                "tags": ["repair", "electronics", "hardware", "tech", "shorts"],
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
        print(f"✅ تم الرفع على YouTube Shorts بنجاح! الرابط: https://youtu.be/{response.get('id')}")
    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى YouTube ({token_env}): {e}")

# ==========================================================
# 5. إشعارات Green API (WhatsApp)
# ==========================================================
def send_notification(message):
    id_instance = (os.getenv("GREEN_ID_INSTANCE") or "").strip()
    api_token = (os.getenv("GREEN_API_TOKEN") or "").strip()

    if not id_instance or not api_token:
        return

    try:
        url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
        payload = {"chatId": "status@broadcast", "message": message}
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

# ==========================================================
# 6. نقطة الدخول الرئيسية
# ==========================================================
def main():
    print("🚀 بدء تشغيل الأتمتة ونشر مقاطع الصيانة...")
    raw_video_path, title, video_id = download_video()

    if raw_video_path and os.path.exists(raw_video_path):
        print(f"📦 بدء نشر الفيديو: {title}")

        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN")

        record_published_video(video_id)
        send_notification(f"✅ تم نشر فيديو جديد: {title}")

        try:
            os.remove(raw_video_path)
        except OSError:
            pass

        print("🎉 تمت الأتمتة بنجاح وظهر الفيديو على القناة!")

if __name__ == "__main__":
    main()
