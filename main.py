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
# 1. قائمة مصادر مباشرة ومضمونة لفيديوهات الهاردوير واللحام
# ==========================================================
DIRECT_HARDWARE_SOURCES = [
    {
        "id": "hw_soldering_01",
        "title": "Professional Electronics Soldering & Repair",
        "url": "https://upload.wikimedia.org/wikipedia/commons/transcoded/5/52/Through-hole_soldering.webm/Through-hole_soldering.webm.480p.vp9.webm"
    },
    {
        "id": "hw_pcb_surface_02",
        "title": "SMD Circuit Board Soldering Demonstration",
        "url": "https://upload.wikimedia.org/wikipedia/commons/transcoded/e/e0/Surface-mount_soldering.webm/Surface-mount_soldering.webm.480p.vp9.webm"
    },
    {
        "id": "hw_motherboard_diag_03",
        "title": "Computer Motherboard Diagnostics & Testing",
        "url": "https://upload.wikimedia.org/wikipedia/commons/transcoded/1/13/Desoldering_with_braid.webm/Desoldering_with_braid.webm.480p.vp9.webm"
    },
    {
        "id": "hw_desoldering_04",
        "title": "Electronics Desoldering & Component Replacement",
        "url": "https://upload.wikimedia.org/wikipedia/commons/transcoded/b/b3/Wave_soldering.webm/Wave_soldering.webm.480p.vp9.webm"
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
# 3. دعم Pexels API لجلب مقاطع يومية متجددة
# ==========================================================
def fetch_from_pexels(published_ids):
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return []

    topics = ["soldering electronics", "motherboard repair", "pc repair technician", "circuit board repair"]
    query = random.choice(topics)
    print(f"🔍 البحث في Pexels API عن: '{query}'...")

    headers = {"Authorization": api_key, "User-Agent": USER_AGENT}
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=15"

    results = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            videos = res.json().get("videos", [])
            for v in videos:
                v_id = f"pex_{v.get('id')}"
                if v_id not in published_ids:
                    files = v.get("video_files", [])
                    best_file = next((f for f in files if f.get("quality") == "hd"), files[0] if files else None)
                    if best_file and best_file.get("link"):
                        results.append({
                            "id": v_id,
                            "title": f"Hardware & Electronics Repair - {query.title()}",
                            "url": best_file.get("link")
                        })
    except Exception as e:
        print(f"⚠️ تنبيه Pexels: {e}")

    return results

# ==========================================================
# 4. تنزيل الفيديو الذكي مع التخطي التلقائي للأخطاء
# ==========================================================
def download_video():
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    # تجميع الروابط المتاحة
    candidates = fetch_from_pexels(published_ids)

    direct_available = [v for v in DIRECT_HARDWARE_SOURCES if v["id"] not in published_ids]
    if not direct_available and not candidates:
        print("🔄 تم استهلاك كافة الفيديوهات، جارٍ تصفير السجل وإعادة التدوير...")
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        direct_available = DIRECT_HARDWARE_SOURCES.copy()

    random.shuffle(direct_available)
    candidates.extend(direct_available)

    headers = {"User-Agent": USER_AGENT}

    for item in candidates:
        v_id = item["id"]
        title = item["title"]
        url = item["url"]
        
        ext = "webm" if ".webm" in url else "mp4"
        filepath = f"downloads/{v_id}.{ext}"

        print(f"📥 محاولة تحميل: {title}")
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                if r.status_code != 200:
                    print(f"⚠️ تخطي الرابط بسبب كود الحالة: {r.status_code}")
                    continue

                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

            if os.path.exists(filepath) and os.path.getsize(filepath) > 50000:
                file_size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                print(f"✅ تم تحميل الفيديو بنجاح ({file_size_mb} MB)")
                return filepath, title, v_id

        except Exception as e:
            print(f"⚠️ خطأ أثناء التحميل: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            continue

    print("❌ تعذر تحميل أي فيديو صالح حالياً.")
    sys.exit(1)

# ==========================================================
# 5. الرفع على YouTube Shorts
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
                "description": f"{title}\n\n#repair #electronics #hardware #shorts #soldering #tech",
                "tags": ["repair", "electronics", "hardware", "soldering", "tech", "shorts"],
                "categoryId": "28"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        print(f"✅ تم نشر الفيديو على YouTube Shorts بنجاح! الرابط: https://youtu.be/{response.get('id')}")
    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى YouTube ({token_env}): {e}")

# ==========================================================
# 6. الرفع على Instagram Reels
# ==========================================================
def publish_to_instagram(video_path, title):
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        print("⏩ تخطي Instagram: بيانات الحساب غير متوفرة.")
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
# 7. إشعارات Green API (WhatsApp)
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
# 8. نقطة الدخول الرئيسية
# ==========================================================
def main():
    print("🚀 بدء تشغيل الأتمتة وجلب فيديوهات الهاردوير والصيانة...")
    raw_video_path, title, video_id = download_video()

    if raw_video_path and os.path.exists(raw_video_path):
        print(f"📦 بدء عملية النشر للفيديو: {title}")

        # النشر الفوري
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN")
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN_2")
        publish_to_instagram(raw_video_path, title)

        # تسجيل المعرف وإرسال الإشعار
        record_published_video(video_id)
        send_notification(f"✅ تم نشر فيديو جديد: {title}")

        # تنظيف الملف
        try:
            os.remove(raw_video_path)
        except OSError:
            pass

        print("🎉 تمت المهمة بالكامل ونُشر الفيديو بنجاح!")

if __name__ == "__main__":
    main()
