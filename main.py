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
# 1. مكتبة روابط فيديوهات صيانة وهاردوير مباشرة (بدون أي حظر)
# ==========================================================
DIRECT_HARDWARE_VIDEOS = [
    {
        "id": "fix_hw_01",
        "title": "Computer Hardware & Circuit Repair Tips",
        "url": "https://assets.mixkit.co/videos/preview/mixkit-circuit-board-of-a-computer-42686-large.mp4"
    },
    {
        "id": "fix_hw_02",
        "title": "Electronics PCB Soldering and Inspection",
        "url": "https://assets.mixkit.co/videos/preview/mixkit-hands-of-an-engineer-soldering-a-motherboard-42688-large.mp4"
    },
    {
        "id": "fix_hw_03",
        "title": "Motherboard Diagnostics and Micro Electronics",
        "url": "https://assets.mixkit.co/videos/preview/mixkit-close-up-of-circuit-board-components-42684-large.mp4"
    },
    {
        "id": "fix_hw_04",
        "title": "High Tech Micro Soldering & Wire Connection",
        "url": "https://assets.mixkit.co/videos/preview/mixkit-technician-soldering-components-on-a-circuit-board-42687-large.mp4"
    },
    {
        "id": "fix_hw_05",
        "title": "Testing Resistance & Electronic Voltage",
        "url": "https://assets.mixkit.co/videos/preview/mixkit-man-working-on-a-circuit-board-with-a-soldering-iron-42685-large.mp4"
    }
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
# 3. جلب مقاطع الصيانة عبر Pexels API (إن وجد)
# ==========================================================
def fetch_pexels_video(published_ids):
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return None

    keywords = ["soldering electronics", "pc repair", "motherboard repair", "technician repairing electronics"]
    query = random.choice(keywords)
    print(f"🔍 البحث في Pexels API عن: {query}")

    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=15"

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            videos = data.get("videos", [])
            for v in videos:
                v_id = f"pexels_{v.get('id')}"
                if v_id not in published_ids:
                    # اختيار أعلى جودة للملف بصيغة HD
                    video_files = v.get("video_files", [])
                    best_file = next((f for f in video_files if f.get("quality") == "hd"), video_files[0] if video_files else None)
                    if best_file:
                        return {
                            "id": v_id,
                            "title": f"Hardware & Electronics Repair - {query.title()}",
                            "url": best_file.get("link")
                        }
    except Exception as e:
        print(f"⚠️ خطأ أثناء طلب Pexels: {e}")

    return None

# ==========================================================
# 4. تنزيل الفيديو المباشر
# ==========================================================
def download_video():
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    # محاولة الجلب من Pexels API أولاً
    selected_video = fetch_pexels_video(published_ids)

    # إذا لم يتوفر Pexels، يتم الاختيار من قائمة الفيديوهات المباشرة
    if not selected_video:
        available_pool = [v for v in DIRECT_HARDWARE_VIDEOS if v["id"] not in published_ids]
        
        # تصفير السجل في حال استهلاك كافة الفيديوهات المباشرة
        if not available_pool:
            print("🔄 تم استهلاك كل المقاطع، جارٍ إعادة تدوير القائمة...")
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            available_pool = DIRECT_HARDWARE_VIDEOS.copy()

        selected_video = random.choice(available_pool)

    v_id = selected_video["id"]
    title = selected_video["title"]
    download_url = selected_video["url"]
    filepath = f"downloads/{v_id}.mp4"

    print(f"📥 تم اختيار الفيديو: {title}")
    print(f"⏳ جارٍ تنزيل ملف الفيديو المباشر...")

    headers = {"User-Agent": "Mozilla/5.0"}
    with requests.get(download_url, headers=headers, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 50000:
        file_size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
        print(f"✅ تم تحميل الفيديو بنجاح ({file_size_mb} MB)")
        return filepath, title, v_id

    print("❌ فشل تنزيل الملف المحدد.")
    sys.exit(1)

# ==========================================================
# 5. النشر على YouTube Shorts
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
        print(f"✅ تم الرفع والنشر على YouTube بنجاح! الرابط: https://youtu.be/{response.get('id')}")
    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى YouTube ({token_env}): {e}")

# ==========================================================
# 6. النشر على Instagram Reels
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
# 8. نقطة الدخول الرئيسية
# ==========================================================
def main():
    print("🚀 بدء تشغيل الأتمتة ونشر مقاطع الصيانة...")
    raw_video_path, title, video_id = download_video()

    if raw_video_path and os.path.exists(raw_video_path):
        print(f"📦 بدء عملية النشر للفيديو: {title}")

        # الرفع على قنوات يوتيوب وحساب إنستغرام
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN")
        publish_to_youtube(raw_video_path, title, "YOUTUBE_REFRESH_TOKEN_2")
        publish_to_instagram(raw_video_path, title)

        # تسجيل المعرف وإرسال الإشعار
        record_published_video(video_id)
        send_notification(f"✅ تم نشر فيديو جديد: {title}")

        # تنظيف الملف المحمل
        try:
            os.remove(raw_video_path)
        except OSError:
            pass

        print("🎉 تمت المهمة ونزل الفيديو بنجاح على القناة!")

if __name__ == "__main__":
    main()
