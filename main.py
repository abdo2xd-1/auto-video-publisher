import os
import sys
import json
import time
import threading
import requests
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================================
# 1. قائمة الـ 20 حساباً المستهدفة على TikTok
# ==========================================================
TARGET_ACCOUNTS = [
    # الحسابات الـ 7 المطلوبة من قبلك
    {"name": "Engineer M Z", "url": "https://www.tiktok.com/@engineermz"},
    {"name": "Dr Maker", "url": "https://www.tiktok.com/@drmakerr"},
    {"name": "Ahmed Amr Embabi", "url": "https://www.tiktok.com/@ahmedamrembabi"},
    {"name": "Saba7o Korah", "url": "https://www.tiktok.com/@amr.nasoohy"},
    {"name": "Erza3 Ma3 Serry", "url": "https://www.tiktok.com/@marwanserry"},
    {"name": "Santaramaghareeb", "url": "https://www.tiktok.com/@santaramaghareeb"},
    {"name": "Kora Station", "url": "https://www.tiktok.com/@korastation"},

    # أفضل 13 حساباً في صيانة الهاردوير والهواتف والكمبيوتر
    {"name": "Phone Repair Guru", "url": "https://www.tiktok.com/@phonerepairguru"},
    {"name": "JerryRigEverything", "url": "https://www.tiktok.com/@jerryrigeverything"},
    {"name": "Hugh Jeffreys", "url": "https://www.tiktok.com/@hughjeffreys"},
    {"name": "Strange Parts", "url": "https://www.tiktok.com/@strangeparts"},
    {"name": "The Art of Repair", "url": "https://www.tiktok.com/@theartofrepair"},
    {"name": "The Phone Lab", "url": "https://www.tiktok.com/@thephonelab"},
    {"name": "NorthridgeFix", "url": "https://www.tiktok.com/@northridgefix"},
    {"name": "TronicsFix", "url": "https://www.tiktok.com/@tronicsfix"},
    {"name": "Northwest Repair", "url": "https://www.tiktok.com/@northwestrepair"},
    {"name": "Louis Rossmann", "url": "https://www.tiktok.com/@louisrossmann"},
    {"name": "Salem Techsperts", "url": "https://www.tiktok.com/@salemtechsperts"},
    {"name": "Big Clive", "url": "https://www.tiktok.com/@bigclivedotcom"},
    {"name": "ElectroBOOM", "url": "https://www.tiktok.com/@electroboom"}
]

HISTORY_FILE = "published_history.txt"
history_lock = threading.Lock()
quota_exceeded_flag = False

# ==========================================================
# 2. إدارة السجل لمنع التكرار
# ==========================================================
def get_published_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def record_published_video(video_id):
    with history_lock:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"{video_id}\n")

# ==========================================================
# 3. استخراج Access Token من Google OAuth
# ==========================================================
def get_access_token():
    refresh_token = (os.getenv("YOUTUBE_REFRESH_TOKEN") or "").strip()
    client_id = (os.getenv("YOUTUBE_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("YOUTUBE_CLIENT_SECRET") or "").strip()

    if not all([refresh_token, client_id, client_secret]):
        print("❌ نقص في بيانات اعتماد YouTube Secrets.")
        return None

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    try:
        res = requests.post(token_url, data=payload, timeout=15)
        return res.json().get("access_token")
    except Exception as e:
        print(f"❌ تعذر الاتصال بـ Google OAuth: {e}")
        return None

# ==========================================================
# 4. الرفع على YouTube Shorts
# ==========================================================
def upload_to_youtube(video_path, title, access_token):
    global quota_exceeded_flag
    if quota_exceeded_flag:
        return False

    try:
        creds = Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=creds)

        # تجهيز عنوان ووصف متوافق مع Shorts
        clean_title = (title[:85] + " #Shorts") if "#Shorts" not in title else title[:95]
        body = {
            "snippet": {
                "title": clean_title,
                "description": f"{title}\n\n#Shorts #Viral #Trending #Reels #Tech",
                "tags": ["Shorts", "Viral", "Trending", "Reels", "Tech"],
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
        print(f"✅ [تم النشر بنجاح على قناتك] {clean_title} -> https://youtu.be/{response.get('id')}")
        return True

    except Exception as e:
        err_msg = str(e)
        if "quotaExceeded" in err_msg:
            print("⚠️ تم استهلاك حصة الرفع اليومية للـ API المتاحة لحسابك اليوم.")
            quota_exceeded_flag = True
        else:
            print(f"❌ خطأ أثناء الرفع ({title}): {e}")
        return False

# ==========================================================
# 5. تنزيل ومعالجة مقاطع الحساب (7 مقاطع لكل حساب)
# ==========================================================
def process_account(account, access_token, published_ids):
    global quota_exceeded_flag
    if quota_exceeded_flag:
        return

    acc_name = account["name"]
    acc_url = account["url"]
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'playlist_items': '1-7',  # سحب أحدث 7 مقاطع
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"🔍 [فحص الحساب] {acc_name} ({acc_url})...")
            info = ydl.extract_info(acc_url, download=False)
            if not info:
                return

            entries = info.get('entries', [])
            if not entries and isinstance(info, dict):
                entries = [info]

            for entry in entries:
                if quota_exceeded_flag:
                    break

                if not entry:
                    continue

                v_id = entry.get('id')
                v_title = entry.get('title', f"{acc_name} Video")
                v_url = entry.get('webpage_url') or entry.get('url') or f"{acc_url}/video/{v_id}"

                if not v_id or v_id in published_ids:
                    continue

                print(f"📥 [تحميل فيديو جديد] ({acc_name}) : {v_title[:45]}...")
                try:
                    ydl.download([v_url])
                except Exception as dl_err:
                    print(f"⚠️ تعذر تنزيل المقطع {v_id}: {dl_err}")
                    continue

                # العثور على الملف المحمل
                downloaded_file = None
                for ext in ['mp4', 'webm', 'mkv', 'mov']:
                    candidate = f"downloads/{v_id}.{ext}"
                    if os.path.exists(candidate):
                        downloaded_file = candidate
                        break

                if downloaded_file and os.path.exists(downloaded_file) and os.path.getsize(downloaded_file) > 10000:
                    uploaded = upload_to_youtube(downloaded_file, v_title, access_token)
                    if uploaded:
                        record_published_video(v_id)
                        published_ids.add(v_id)

                    try:
                        os.remove(downloaded_file)
                    except OSError:
                        pass

    except Exception as e:
        print(f"⚠️ تنبيه أثناء معالجة حساب {acc_name}: {e}")

# ==========================================================
# 6. نقطة الدخول والتشغيل المتوازي
# ==========================================================
def main():
    print("🚀 بدء الفحص الشامل وتنزيل المقاطع من الـ 20 حساباً ونشرها على YouTube Shorts...")
    access_token = get_access_token()
    if not access_token:
        print("❌ لم يتم العثور على Access Token صالح.")
        sys.exit(1)

    published_ids = get_published_history()
    print(f"📊 إجمالي المقاطع المنشورة سابقاً في السجل: {len(published_ids)}")

    # معالجة 4 حسابات بالتوازي في نفس اللحظة
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_account, acc, access_token, published_ids) for acc in TARGET_ACCOUNTS]
        for future in as_completed(futures):
            if quota_exceeded_flag:
                break

    print("🎉 اكتملت الدورة بنجاح!")

if __name__ == "__main__":
    main()
