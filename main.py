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
SEARCH_TOPICS = [
    "soldering electronics",
    "motherboard repair",
    "circuit board",
    "pc repair technician",
    "computer hardware",
    "micro soldering",
    "electronics diagnostic",
    "cpu socket motherboard"
]

HISTORY_FILE = "published_history.txt"
USER_AGENT = "HardwareBot/2.0 (Automated Educational Publisher; contact@example.com)"

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
# 3. المصدر 1: Pexels API (مقاطع Shorts عمودية فائقة الجودة)
# ==========================================================
def fetch_from_pexels(published_ids):
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return None

    topic = random.choice(SEARCH_TOPICS)
    print(f"🔍 البحث في Pexels API عن: '{topic}'...")
    url = f"https://api.pexels.com/videos/search?query={topic}&orientation=portrait&per_page=20"
    headers = {"Authorization": api_key, "User-Agent": USER_AGENT}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            videos = res.json().get("videos", [])
            random.shuffle(videos)
            for v in videos:
                v_id = f"pex_{v.get('id')}"
                duration = v.get("duration", 0)
                if v_id not in published_ids and (duration <= 90):
                    files = v.get("video_files", [])
                    # اختيار جودة HD أو SD مناسبة
                    target_file = next((f for f in files if f.get("quality") == "hd" and f.get("width", 0) < f.get("height", 0)), None)
                    if not target_file and files:
                        target_file = files[0]

                    if target_file and target_file.get("link"):
                        return {
                            "id": v_id,
                            "title": f"Professional Hardware Repair - {topic.title()}",
                            "url": target_file.get("link"),
                            "headers": {}
                        }
    except Exception as e:
        print(f"⚠️ خطأ أثناء طلب Pexels: {e}")
    return None

# ==========================================================
# 4. المصدر 2: Internet Archive API (مفتوح بالكامل وبدون حظر)
# ==========================================================
def fetch_from_archive_org(published_ids):
    topic = random.choice(["soldering", "electronics repair", "circuit board", "computer repair", "motherboard"])
    print(f"🔍 البحث في Internet Archive عن: '{topic}'...")

    search_url = "https://archive.org/advancedsearch.php"
    params = {
        "q": f"mediatype:(movies) AND ({topic})",
        "fl[]": "identifier,title",
        "sort[]": "downloads desc",
        "rows": 30,
        "output": "json"
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(search_url, params=params, headers=headers, timeout=15)
        if res.status_code == 200:
            docs = res.json().get("response", {}).get("docs", [])
            random.shuffle(docs)

            for doc in docs:
                item_id = doc.get("identifier")
                if not item_id or item_id in published_ids:
                    continue

                # جلب ملفات العنصر
                meta_url = f"https://archive.org/metadata/{item_id}"
                meta_res = requests.get(meta_url, headers=headers, timeout=10)
                if meta_res.status_code != 200:
                    continue

                files = meta_res.json().get("files", [])
                for f in files:
                    fname = f.get("name", "")
                    fmt = f.get("format", "")
                    size = int(f.get("size", 0) or 0)

                    # اختيار ملف MP4 بحجم مناسب لأجهزة الموبايل (أقل من 40 ميجابايت)
                    if fname.endswith(".mp4") and (0 < size < 40 * 1024 * 1024):
                        download_url = f"https://archive.org/download/{item_id}/{fname}"
                        clean_title = doc.get("title", f"Hardware & Electronics Guide - {topic.title()}")
                        return {
                            "id": f"ia_{item_id}",
                            "title": clean_title,
                            "url": download_url,
                            "headers": headers
                        }
    except Exception as e:
        print(f"⚠️ خطأ أثناء طلب Internet Archive: {e}")
    return None

# ==========================================================
# 5. تنزيل ملف الفيديو المباشر وحفظه محلياً
# ==========================================================
def download_video():
    os.makedirs("downloads", exist_ok=True)
    published_ids = get_published_history()

    # المحاولة من Pexels ثم Internet Archive
    video_item = fetch_from_pexels(published_ids)
    if not video_item:
        video_item = fetch_from_archive_org(published_ids)

    if not video_item:
        print("ℹ️ تم فحص كافة المصادر ولم يتم العثور على فيديوهات جديدة غير مكررة.")
        sys.exit(0)

    v_id = video_item["id"]
    title = video_item["title"]
    download_url = video_item["url"]
    req_headers = video_item.get("headers", {"User-Agent": USER_AGENT})

    filepath = f"downloads/{v_id}.mp4"
    print(f"📥 تم اختيار الفيديو: {title}")
    print(f"⏳ جارٍ التحميل المباشر من المصدر...")

    try:
        with requests.get(download_url, headers=req_headers, stream=True, timeout=45) as r:
            if r.status_code != 200:
                print(f"❌ فشل التحميل بكود الحالة: {r.status_code}")
                sys.exit(1)

            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 50000:
            file_size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
            print(f"✅ تم تحميل الفيديو بنجاح ({file_size_mb} MB)")
            return filepath, title, v_id
    except Exception as err:
        print(f"❌ خطأ أثناء التنزيل: {err}")
        if os.path.exists(filepath):
            os.remove(filepath)
        sys.exit(1)

    print("❌ تعذر حفظ ملف الفيديو.")
    sys.exit(1)

# ==========================================================
# 6. النشر على YouTube Shorts
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

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        print(f"✅ تم الرفع على YouTube بنجاح! الرابط: https://youtu.be/{response.get('id')}")
    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى YouTube ({token_env}): {e}")

# ==========================================================
# 7. النشر على Instagram Reels
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
# 8. إشعارات Green API (WhatsApp)
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
# 9. نقطة الدخول الرئيسية
# ==========================================================
def main():
    print("🚀 بدء تشغيل الأتمتة وجلب فيديوهات الهاردوير والصيانة...")
    raw_video_path, title, video_id = download_video()

    if raw_video_path and os.path.exists(raw_video_path):
        print(f"📦 بدء عملية النشر للفيديو: {title}")

        # الرفع والنشر
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

        print("🎉 تمت جميع المهام بنجاح ونُشر الفيديو على قناتك!")

if __name__ == "__main__":
    main()
