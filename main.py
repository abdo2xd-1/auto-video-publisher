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
# 1. قائمة الـ 100 قناة
# ==========================================================
CHANNELS = [
    # القنوات المحددة
    "https://www.youtube.com/@Engineer-M-Z/shorts",
    "https://www.youtube.com/@drmakerr/shorts",
    "https://www.youtube.com/@ahmedamrembabi97/shorts",
    "https://www.youtube.com/@Saba7oKorah/shorts",
    "https://www.youtube.com/@erza3ma3serry/shorts",
    "https://www.youtube.com/@santarama3gharib/shorts",
    "https://www.youtube.com/@KoraStation/shorts",

    # قنوات صيانة الهواتف والمايكروسولدرينغ
    "https://www.youtube.com/@PhoneRepairGuru/shorts",
    "https://www.youtube.com/@HughJeffreys/shorts",
    "https://www.youtube.com/@iPadRehab/shorts",
    "https://www.youtube.com/@JerryRigEverything/shorts",
    "https://www.youtube.com/@StrangeParts/shorts",
    "https://www.youtube.com/@TheArtofRepair/shorts",
    "https://www.youtube.com/@STSTelecom/shorts",
    "https://www.youtube.com/@VCCBoardRepair/shorts",
    "https://www.youtube.com/@RewaTechnology/shorts",
    "https://www.youtube.com/@QianLiToolPlus/shorts",
    "https://www.youtube.com/@iFixitYourself/shorts",
    "https://www.youtube.com/@JesseCruzRepair/shorts",
    "https://www.youtube.com/@MobileRepairingOnline/shorts",
    "https://www.youtube.com/@FixitFixitFixit/shorts",
    "https://www.youtube.com/@ThePhoneLab/shorts",
    "https://www.youtube.com/@MonkeyCapital/shorts",
    "https://www.youtube.com/@MicrosolderingFR/shorts",
    "https://www.youtube.com/@PhoneBoardSolutions/shorts",
    "https://www.youtube.com/@CellPhoneRepairCPR/shorts",

    # قنوات صيانة اللابتوب وكروت الشاشة والكمبيوتر
    "https://www.youtube.com/@NorthridgeFix/shorts",
    "https://www.youtube.com/@Tronicsfix/shorts",
    "https://www.youtube.com/@KrisFixGermany/shorts",
    "https://www.youtube.com/@NorthwestRepair/shorts",
    "https://www.youtube.com/@rossmanngroup/shorts",
    "https://www.youtube.com/@ElectronicsRepairSchool/shorts",
    "https://www.youtube.com/@SalemTechsperts/shorts",
    "https://www.youtube.com/@GregSalazar/shorts",
    "https://www.youtube.com/@ActuallyHardcoreOverclocking/shorts",
    "https://www.youtube.com/@MyMateVINCE/shorts",
    "https://www.youtube.com/@MendItMark/shorts",
    "https://www.youtube.com/@AdamantIT/shorts",
    "https://www.youtube.com/@The8BitGuy/shorts",
    "https://www.youtube.com/@TechYESCity/shorts",
    "https://www.youtube.com/@AlexLaptopRepair/shorts",
    "https://www.youtube.com/@BoardRepairLab/shorts",
    "https://www.youtube.com/@GPURepairHub/shorts",
    "https://www.youtube.com/@RetroDogFix/shorts",
    "https://www.youtube.com/@PCRepairSquad/shorts",
    "https://www.youtube.com/@MotherboardDiagnostics/shorts",
    "https://www.youtube.com/@ComputerRepairZone/shorts",
    "https://www.youtube.com/@ModdingCafe/shorts",

    # قنوات صيانة الأجهزة المنزلية والإلكترونيات والباور
    "https://www.youtube.com/@LearnElectronicsRepair/shorts",
    "https://www.youtube.com/@BigCliveDotCom/shorts",
    "https://www.youtube.com/@EEVblog/shorts",
    "https://www.youtube.com/@greatscottlab/shorts",
    "https://www.youtube.com/@RepairClinic/shorts",
    "https://www.youtube.com/@AppliancePartsPros/shorts",
    "https://www.youtube.com/@SamuraiApplianceRepair/shorts",
    "https://www.youtube.com/@TechnologyConnections/shorts",
    "https://www.youtube.com/@ElectroBOOM/shorts",
    "https://www.youtube.com/@SDGElectronics/shorts",
    "https://www.youtube.com/@MrCarlsonsLab/shorts",
    "https://www.youtube.com/@12voltvids/shorts",
    "https://www.youtube.com/@norcal715/shorts",
    "https://www.youtube.com/@JohnWardElectric/shorts",
    "https://www.youtube.com/@ElectronicClinic/shorts",
    "https://www.youtube.com/@DavesTVElectronics/shorts",
    "https://www.youtube.com/@MikesElectricStuff/shorts",
    "https://www.youtube.com/@TheSignalPath/shorts",
    "https://www.youtube.com/@AllAboutCircuits/shorts",
    "https://www.youtube.com/@PowerSupplyRepair/shorts",
    "https://www.youtube.com/@InverterBoardRepair/shorts",
    "https://www.youtube.com/@MicrowaveFixer/shorts",
    "https://www.youtube.com/@CircuitLabFix/shorts",

    # قنوات عربية متخصصة في الصيانة
    "https://www.youtube.com/@AhmedTahseen/shorts",
    "https://www.youtube.com/@AliSaberLaptop/shorts",
    "https://www.youtube.com/@WalidIssaElectronics/shorts",
    "https://www.youtube.com/@ElectronicsForEveryone/shorts",
    "https://www.youtube.com/@SmouhaAcademy/shorts",
    "https://www.youtube.com/@MobileProRepair/shorts",
    "https://www.youtube.com/@EgyptBoardRepair/shorts",
    "https://www.youtube.com/@WorldOfElectronicsRepair/shorts",
    "https://www.youtube.com/@TechHardwareAr/shorts",
    "https://www.youtube.com/@DoctorHardware/shorts",
    "https://www.youtube.com/@ElectronicsWorkshop/shorts",
    "https://www.youtube.com/@HardwareCastle/shorts",
    "https://www.youtube.com/@SamehLaptopRepair/shorts",
    "https://www.youtube.com/@ArabElectronics/shorts",
    "https://www.youtube.com/@TVMaintenanceAr/shorts",
    "https://www.youtube.com/@ACBoardRepair/shorts",
    "https://www.youtube.com/@HardwareCafe/shorts",
    "https://www.youtube.com/@InnovatorElectronics/shorts",
    "https://www.youtube.com/@ArabHardware/shorts",
    "https://www.youtube.com/@EasyMobileRepair/shorts",
    "https://www.youtube.com/@BoardFixArabic/shorts",
    "https://www.youtube.com/@HomeApplianceEng/shorts",
    "https://www.youtube.com/@LaptopRepairSecrets/shorts",
    "https://www.youtube.com/@ElectronicsMasteryWay/shorts",
    "https://www.youtube.com/@MaintenanceExcellenceCenter/shorts",
    "https://www.youtube.com/@MicroTechAr/shorts",
    "https://www.youtube.com/@BoardDoctor/shorts"
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
# 3. استخراج Access Token
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
        data = res.json()
        return data.get("access_token")
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
            print("⚠️ تم استهلاك حصة الرفع اليومية المتاحة للـ API.")
            quota_exceeded_flag = True
        else:
            print(f"❌ خطأ أثناء الرفع ({title}): {e}")
        return False

# ==========================================================
# 5. معالجة القناة وسحب 7 فيديوهات
# ==========================================================
def process_channel(channel_url, access_token, published_ids):
    global quota_exceeded_flag
    if quota_exceeded_flag:
        return

    os.makedirs("downloads", exist_ok=True)
    channel_name = channel_url.split('/')[3]

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'playlist_items': '1-7',  # سحب أول 7 فيديوهات من القناة
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
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
                v_title = entry.get('title', 'Hardware & Repair Shorts')
                v_url = entry.get('webpage_url') or f"https://www.youtube.com/watch?v={v_id}"

                # تخطي الفيديو إذا تم نشره مسبقاً
                if not v_id or v_id in published_ids:
                    continue

                print(f"📥 [تحميل] ({channel_name}) : {v_title[:45]}...")
                try:
                    ydl.download([v_url])
                except Exception as dl_err:
                    print(f"⚠️ فشل تنزيل المقطع: {dl_err}")
                    continue

                # البحث عن الملف المحمّل
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
        print(f"⚠️ تنبيه في قناة {channel_url}: {e}")

# ==========================================================
# 6. نقطة الدخول والتشغيل المتوازي
# ==========================================================
def main():
    print("🚀 بدء فحص الـ 100 قناة ومعالجة 7 مقاطع من كل قناة...")
    access_token = get_access_token()
    if not access_token:
        print("❌ لم يتم العثور على Access Token صالح.")
        sys.exit(1)

    published_ids = get_published_history()
    print(f"📊 إجمالي المقاطع المسجلة سابقاً: {len(published_ids)}")

    # معالجة 5 قنوات بالتوازي في نفس اللحظة
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_channel, ch, access_token, published_ids) for ch in CHANNELS]
        for future in as_completed(futures):
            if quota_exceeded_flag:
                break

    print("🎉 انتهت دورة العمل لهذه الفترة.")

if __name__ == "__main__":
    main()
