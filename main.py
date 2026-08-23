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
# 1. قائمة القنوات المختارة والمحققة
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
    "https://www.youtube.com/@iFixitYourself",
    "https://www.youtube.com/@ThePhoneLab",
    "https://www.youtube.com/@MonkeyCapital",
    "https://www.youtube.com/@JesseCruz",

    # قنوات صيانة اللابتوب، الكمبيوتر، وكروت الشاشة
    "https://www.youtube.com/@NorthridgeFix",
    "https://www.youtube.com/@Tronicsfix",
    "https://www.youtube.com/@KrisFix-Germany",
    "https://www.youtube.com/@NorthwestRepair",
    "https://www.youtube.com/@rossmanngroup",
    "https://www.youtube.com/@ElectronicsRepairSchool",
    "https://www.youtube.com/@SalemTechsperts",
    "https://www.youtube.com/@GregSalazar",
    "https://www.youtube.com/@ActuallyHardcoreOverclocking",
    "https://www.youtube.com/@MyMateVINCE",
    "https://www.youtube.com/@MendItMark",
    "https://www.youtube.com/@AdamantIT",
    "https://www.youtube.com/@The8BitGuy",
    "https://www.youtube.com/@TechYESCity",
    "https://www.youtube.com/@AlexLaptopRepair",

    # قنوات صيانة الأجهزة المنزلية والباور سبلاي
    "https://www.youtube.com/@LearnElectronicsRepair",
    "https://www.youtube.com/@BigCliveDotCom",
    "https://www.youtube.com/@EEVblog",
    "https://www.youtube.com/@greatscottlab",
    "https://www.youtube.com/@RepairClinic",
    "https://www.youtube.com/@AppliancePartsPros",
    "https://www.youtube.com/@TechnologyConnections",
    "https://www.youtube.com/@ElectroBOOM",
    "https://www.youtube.com/@SDGElectronics",
    "https://www.youtube.com/@MrCarlsonsLab",
    "https://www.youtube.com/@12voltvids",
    "https://www.youtube.com/@norcal715",
    "https://www.youtube.com/@JohnWardElectric",
    "https://www.youtube.com/@MikeElectricStuff",
    "https://www.youtube.com/@TheSignalPath",
    "https://www.youtube.com/@AllAboutCircuits"
]

HISTORY_FILE = "published_history.txt"
history_lock = threading.Lock()
quota_exceeded_flag = False

# ==========================================================
# 2. إدارة السجل ومنع التكرار
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
                "description": f"{title}\n\n#Shorts #Tech #Repair #Hardware #Electronics",
                "tags": ["Shorts", "Tech", "Repair", "Hardware", "Electronics"],
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
            print("⚠️ تم استهلاك حصة الرفع اليومية المتاحة للـ API.")
            quota_exceeded_flag = True
        else:
            print(f"❌ خطأ أثناء الرفع ({title}): {e}")
        return False

# ==========================================================
# 5. معالجة القناة وتخطي حماية YouTube Datacenter Block
# ==========================================================
def process_channel(channel_url, access_token, published_ids):
    global quota_exceeded_flag
    if quota_exceeded_flag:
        return

    os.makedirs("downloads", exist_ok=True)
    channel_name = channel_url.split('/')[-1]

    # إعدادات متقدمة لمحاكاة هواتف Android وتجاوز كشف البوتات
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'playlist_items': '1-7',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
    }

    try:
        # البحث في صفحة الفيديوهات القصيرة أو العامة للقناة
        target_url = f"{channel_url}/shorts"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            if not info or not info.get('entries'):
                info = ydl.extract_info(f"{channel_url}/videos", download=False)

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
                v_title = entry.get('title', 'Hardware Shorts')
                v_url = entry.get('webpage_url') or f"https://www.youtube.com/watch?v={v_id}"

                if not v_id or v_id in published_ids:
                    continue

                print(f"📥 [تنزيل] ({channel_name}) : {v_title[:45]}...")
                try:
                    ydl.download([v_url])
                except Exception as dl_err:
                    print(f"⚠️ تخطي الفيديو بسبب قيود التحميل: {dl_err}")
                    continue

                downloaded_file = None
                for ext in ['mp4', 'webm', 'mkv']:
                    candidate = f"downloads/{v_id}.{ext}"
                    if os.path.exists(candidate):
                        downloaded_file = candidate
                        break

                if downloaded_file and os.path.exists(downloaded_file):
                    success = upload_to_youtube(downloaded_file, v_title, access_token)
                    if success:
                        record_published_video(v_id)
                        published_ids.add(v_id)

                    try:
                        os.remove(downloaded_file)
                    except OSError:
                        pass

    except Exception as e:
        print(f"⚠️ تنبيه أثناء فحص {channel_name}: {e}")

# ==========================================================
# 6. التشغيل المتوازي
# ==========================================================
def main():
    print("🚀 بدء الفحص الذكي وتنزيل ونشر 7 مقاطع بالتوازي...")
    access_token = get_access_token()
    if not access_token:
        print("❌ تعذر متابعة النشر بسبب عدم توفر التوكن.")
        sys.exit(1)

    published_ids = get_published_history()
    print(f"📊 إجمالي المقاطع المسجلة سابقاً: {len(published_ids)}")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_channel, ch, access_token, published_ids) for ch in CHANNELS]
        for future in as_completed(futures):
            if quota_exceeded_flag:
                break

    print("🎉 انتهت دورة النشر بنجاح!")

if __name__ == "__main__":
    main()
