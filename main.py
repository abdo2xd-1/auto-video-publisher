import os
import sys
import json
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================================
# 1. قائمة الـ 20 حساباً (مع المعرفات البديلة لضمان الجلب)
# ==========================================================
TARGET_ACCOUNTS = [
    # الحسابات الـ 7 الأساسية
    {"name": "Engineer M Z", "handles": ["engineermz", "engineer_m_z", "engineer.m.z"]},
    {"name": "Dr Maker", "handles": ["drmakerr", "dr.maker", "drmaker"]},
    {"name": "Ahmed Amr Embabi", "handles": ["ahmedamrembabi97", "ahmedamrembabi"]},
    {"name": "Saba7o Korah", "handles": ["amr.nasoohy", "saba7okorah", "nasoohy"]},
    {"name": "Erza3 Ma3 Serry", "handles": ["marwanserry", "erza3ma3serry"]},
    {"name": "Santaramaghareeb", "handles": ["santaramaghareeb", "santarama_ghareeb"]},
    {"name": "Kora Station", "handles": ["korastation", "kora_station"]},

    # أفضل 13 حساباً في صيانة الهاردوير والإلكترونيات
    {"name": "Phone Repair Guru", "handles": ["phonerepairguru"]},
    {"name": "JerryRigEverything", "handles": ["jerryrigeverything"]},
    {"name": "Hugh Jeffreys", "handles": ["hughjeffreys"]},
    {"name": "Strange Parts", "handles": ["strangeparts"]},
    {"name": "The Art of Repair", "handles": ["theartofrepair"]},
    {"name": "The Phone Lab", "handles": ["thephonelab", "thephonelabnl"]},
    {"name": "NorthridgeFix", "handles": ["northridgefix"]},
    {"name": "TronicsFix", "handles": ["tronicsfix"]},
    {"name": "Northwest Repair", "handles": ["northwestrepair"]},
    {"name": "Louis Rossmann", "handles": ["rossmanngroup", "louisrossmann"]},
    {"name": "Salem Techsperts", "handles": ["salemtechsperts"]},
    {"name": "Big Clive", "handles": ["bigclivedotcom", "bigclive"]},
    {"name": "ElectroBOOM", "handles": ["electroboom", "electroboomok"]}
]

HISTORY_FILE = "published_history.txt"
history_lock = threading.Lock()
quota_exceeded_flag = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

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
# 3. توليد Access Token من Google
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

        clean_title = (title[:85] + " #Shorts") if "#Shorts" not in title else title[:95]
        body = {
            "snippet": {
                "title": clean_title,
                "description": f"{title}\n\n#Shorts #Viral #Trending #Reels #Tech #Hardware",
                "tags": ["Shorts", "Viral", "Trending", "Reels", "Tech", "Hardware"],
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
            print("⚠️ تم استهلاك حصة الرفع اليومية للـ API.")
            quota_exceeded_flag = True
        else:
            print(f"❌ خطأ أثناء الرفع ({title}): {e}")
        return False

# ==========================================================
# 5. جلب الفيديوهات عبر TikWM API السحابي
# ==========================================================
def fetch_account_videos(handles, count=7):
    for handle in handles:
        try:
            api_url = f"https://www.tikwm.com/api/user/posts?unique_id={handle}&count={count}"
            res = requests.get(api_url, headers=HEADERS, timeout=12)
            if res.status_code == 200:
                data = res.json()
                if data.get("code") == 0:
                    videos = data.get("data", {}).get("videos", [])
                    if videos:
                        return handle, videos[:count]
        except Exception:
            continue
    return None, []

# ==========================================================
# 6. تحميل الفيديو عبر رابطه المباشر
# ==========================================================
def download_stream_file(download_url, output_path):
    try:
        with requests.get(download_url, headers=HEADERS, stream=True, timeout=30) as r:
            if r.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                    return True
    except Exception:
        pass
    return False

# ==========================================================
# 7. معالجة الحساب الواحد
# ==========================================================
def process_account(account, access_token, published_ids):
    global quota_exceeded_flag
    if quota_exceeded_flag:
        return

    acc_name = account["name"]
    handles = account["handles"]
    os.makedirs("downloads", exist_ok=True)

    matched_handle, videos = fetch_account_videos(handles, count=7)
    if not videos:
        print(f"⚠️ [تخطي] لم يتم العثور على مقاطع لحساب {acc_name}")
        return

    print(f"🔍 [فحص الحساب بنجاح] {acc_name} (@{matched_handle}) - عُثر على {len(videos)} مقاطع.")

    for vid_data in videos:
        if quota_exceeded_flag:
            break

        v_id = vid_data.get("video_id")
        if not v_id or v_id in published_ids:
            continue

        v_title = vid_data.get("title") or f"{acc_name} Tech Video"
        v_title = v_title.replace("#", "").strip()[:80]
        play_url = vid_data.get("play") or vid_data.get("wmplay")

        if not play_url:
            continue

        print(f"📥 [تحميل فيديو] ({acc_name}) : ID {v_id}...")
        filepath = f"downloads/{v_id}.mp4"

        if download_stream_file(play_url, filepath):
            uploaded = upload_to_youtube(filepath, v_title, access_token)
            if uploaded:
                record_published_video(v_id)
                published_ids.add(v_id)

            try:
                os.remove(filepath)
            except OSError:
                pass
        else:
            print(f"❌ تعذر تنزيل ملف الفيديو {v_id}")

# ==========================================================
# 8. نقطة الدخول والتشغيل المتوازي
# ==========================================================
def main():
    print("🚀 بدء الفحص الشامل وتنزيل ونشر مقاطع الـ 20 حساباً على YouTube Shorts...")
    access_token = get_access_token()
    if not access_token:
        print("❌ لم يتم العثور على Access Token صالح.")
        sys.exit(1)

    published_ids = get_published_history()
    print(f"📊 إجمالي المقاطع المنشورة سابقاً في السجل: {len(published_ids)}")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_account, acc, access_token, published_ids) for acc in TARGET_ACCOUNTS]
        for future in as_completed(futures):
            if quota_exceeded_flag:
                break

    print("🎉 اكتملت الدورة بنجاح تام!")

if __name__ == "__main__":
    main()
