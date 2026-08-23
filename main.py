import os
import sys
import re
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
# 1. قائمة القنوات المستهدفة
# ==========================================================
CHANNELS = [
    # القنوات المحددة من قبلك
    "https://www.youtube.com/@Engineer-M-Z",
    "https://www.youtube.com/@drmakerr",
    "https://www.youtube.com/@ahmedamrembabi97",
    "https://www.youtube.com/@Saba7oKorah",
    "https://www.youtube.com/@erza3ma3serry",
    "https://www.youtube.com/@santarama3gharib",
    "https://www.youtube.com/@KoraStation",

    # قنوات صيانة الهواتف والمايكروسولدرينغ
    "https://www.youtube.com/@PhoneRepairGuru",
    "https://www.youtube.com/@HughJeffreys",
    "https://www.youtube.com/@JerryRigEverything",
    "https://www.youtube.com/@StrangeParts",
    "https://www.youtube.com/@TheArtofRepair",
    "https://www.youtube.com/@ThePhoneLab",
    "https://www.youtube.com/@MonkeyCapital",

    # قنوات صيانة اللابتوب والكمبيوتر
    "https://www.youtube.com/@NorthridgeFix",
    "https://www.youtube.com/@Tronicsfix",
    "https://www.youtube.com/@NorthwestRepair",
    "https://www.youtube.com/@rossmanngroup",
    "https://www.youtube.com/@SalemTechsperts",
    "https://www.youtube.com/@GregSalazar",
    "https://www.youtube.com/@MyMateVINCE",
    "https://www.youtube.com/@MendItMark",
    "https://www.youtube.com/@The8BitGuy",
    "https://www.youtube.com/@TechYESCity",
    "https://www.youtube.com/@AlexLaptopRepair",

    # قنوات صيانة الأجهزة المنزلية والباور سبلاي
    "https://www.youtube.com/@BigCliveDotCom",
    "https://www.youtube.com/@EEVblog",
    "https://www.youtube.com/@greatscottlab",
    "https://www.youtube.com/@RepairClinic",
    "https://www.youtube.com/@AppliancePartsPros",
    "https://www.youtube.com/@ElectroBOOM",
    "https://www.youtube.com/@SDGElectronics",
    "https://www.youtube.com/@MrCarlsonsLab",
    "https://www.youtube.com/@norcal715"
]

HISTORY_FILE = "published_history.txt"
history_lock = threading.Lock()
quota_exceeded_flag = False

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

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
# 3. توليد Access Token
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
# 4. رفع الفيديو إلى YouTube Shorts
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
                "description": f"{title}\n\n#Shorts #Tech #Repair #Hardware #Electronics #Viral",
                "tags": ["Shorts", "Tech", "Repair", "Hardware", "Electronics", "Viral"],
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
        print(f"✅ [تم النشر بنجاح] {clean_title} -> https://youtu.be/{response.get('id')}")
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
# 5. استخراج معرفات الفيديوهات من صفحات القنوات
# ==========================================================
def get_channel_video_ids(channel_url, max_videos=7):
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    urls_to_try = [f"{channel_url}/shorts", f"{channel_url}/videos"]
    found_ids = []

    for target in urls_to_try:
        try:
            res = requests.get(target, headers=headers, timeout=10)
            if res.status_code == 200:
                html = res.text
                shorts_ids = re.findall(r'/shorts/([a-zA-Z0-9_-]{11})', html)
                video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)

                combined = list(dict.fromkeys(shorts_ids + video_ids))
                for vid in combined:
                    if vid not in found_ids:
                        found_ids.append(vid)

                if len(found_ids) >= max_videos:
                    break
        except Exception:
            continue

    return found_ids[:max_videos]

# ==========================================================
# 6. التنزيل السحابي عبر خوادم البدائل (تجاوز حظر يوتيوب 100%)
# ==========================================================
def download_video_stream(v_id, output_path):
    invidious_nodes = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://invidious.jing.rocks",
        "https://yt.artemislena.eu",
        "https://iv.ggtyler.dev",
        "https://invidious.projectsegfau.lt",
        "https://invidious.private.coffee"
    ]

    for node in invidious_nodes:
        try:
            api_url = f"{node}/api/v1/videos/{v_id}"
            res = requests.get(api_url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                title = data.get("title", f"Short {v_id}")
                formats = data.get("formatStreams", [])
                if formats:
                    stream_url = formats[-1].get("url")
                    if stream_url:
                        with requests.get(stream_url, stream=True, timeout=30) as r:
                            if r.status_code == 200:
                                with open(output_path, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                                        if chunk:
                                            f.write(chunk)
                                if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                                    return True, title
        except Exception:
            continue

    return False, None

# ==========================================================
# 7. معالجة القناة الفردية
# ==========================================================
def process_channel(channel_url, access_token, published_ids):
    global quota_exceeded_flag
    if quota_exceeded_flag:
        return

    os.makedirs("downloads", exist_ok=True)
    channel_name = channel_url.split('/')[-1]

    video_ids = get_channel_video_ids(channel_url, max_videos=7)
    if not video_ids:
        return

    for v_id in video_ids:
        if quota_exceeded_flag:
            break

        if v_id in published_ids:
            continue

        print(f"📥 [تنزيل مقطع] ({channel_name}) : ID {v_id}...")
        filepath = f"downloads/{v_id}.mp4"
        success, v_title = download_video_stream(v_id, filepath)

        if success and os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
            uploaded = upload_to_youtube(filepath, v_title, access_token)
            if uploaded:
                record_published_video(v_id)
                published_ids.add(v_id)

            try:
                os.remove(filepath)
            except OSError:
                pass

# ==========================================================
# 8. نقطة الدخول الرئيسية
# ==========================================================
def main():
    print("🚀 بدء الفحص المتوازي ومعالجة 7 مقاطع من كل قناة عبر السحابة...")
    access_token = get_access_token()
    if not access_token:
        print("❌ لم يتم العثور على Access Token صالح.")
        sys.exit(1)

    published_ids = get_published_history()
    print(f"📊 إجمالي المقاطع المسجلة سابقاً: {len(published_ids)}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_channel, ch, access_token, published_ids) for ch in CHANNELS]
        for future in as_completed(futures):
            if quota_exceeded_flag:
                break

    print("🎉 اكتملت الدورة بنجاح!")

if __name__ == "__main__":
    main()
