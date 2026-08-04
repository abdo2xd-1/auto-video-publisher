import os
import glob
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ===================================================
# 📌 قائمة الحسابات المستهدفة
# ===================================================
TARGET_CHANNELS = [
    "https://www.tiktok.com/@yasser_aldosari",
    "https://www.tiktok.com/@islamsobhiofficial",
    "https://www.tiktok.com/@alafasy",
    "https://www.tiktok.com/@maher_almuaiqly",
    "https://www.tiktok.com/@mansour_alsalmi",
    "https://www.tiktok.com/@hazza_alblushi",
    "https://www.tiktok.com/@sherif_mostafa",
    "https://www.tiktok.com/@ahmed_alnufais",
    "https://www.tiktok.com/@abdulbasit_quran",
    "https://www.tiktok.com/@alminshawi_archive",
    "https://www.tiktok.com/@quran_kareem",
    "https://www.tiktok.com/@tilawat_qurania",
    "https://www.tiktok.com/@ayat_qurania_ar",
    "https://www.tiktok.com/@tadabbor_quran",
    "https://www.tiktok.com/@quran_heart",
    "https://www.tiktok.com/@quran_verses_ar",
]

# مجلد حفظ الفيديو النهائي المطابق لإعدادات GitHub Workflow
OUTPUT_DIR = "final_videos"

def ensure_directories():
    """إنشاء مجلد الحفظ إذا لم يكن موجوداً"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def download_latest_video(channel_url):
    """تنزيل أحدث فيديو من حساب تيك توك"""
    print(f"🔍 جاري فحص الحساب: {channel_url}")
    
    ydl_opts = {
        'outtmpl': f'{OUTPUT_DIR}/%(id)s.%(ext)s',
        'playlistend': 1,
        'format': 'mp4/bestvideo+bestaudio/best',
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                video_info = info['entries'][0]
            else:
                video_info = info
                
            title = video_info.get('title', 'فيديو جديد')
            video_id = video_info.get('id')
            
            downloaded_files = glob.glob(f"{OUTPUT_DIR}/{video_id}.*")
            if downloaded_files:
                return downloaded_files[0], title
    except Exception as e:
        print(f"⚠️ خطأ أثناء التنزيل من {channel_url}: {e}")
    
    return None, None

def upload_to_youtube(video_path, title, description="#shorts #quran"):
    """رفع الفيديو إلى يوتيوب باستخدام Credentials المعتمدة من GitHub Secrets"""
    print(f"🚀 جاري بدء رفع الفيديو إلى يوتيوب: {video_path}")

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("❌ خطأ: أسرار GitHub Secrets الخاصة بـ YouTube غير متوفرة أو ناقصة!")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_path, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⏳ نسبة الرفع: {int(status.progress() * 100)}%")

    print(f"✅ تم الرفع بنجاح! رابط الفيديو: https://youtu.be/{response['id']}")
    return response['id']

def main():
    ensure_directories()
    
    video_path = None
    video_title = None

    # البحث في قائمة الحسابات وتنزيل أول فيديو ينجح
    for channel in TARGET_CHANNELS:
        video_path, video_title = download_latest_video(channel)
        if video_path and os.path.exists(video_path):
            print(f"🎯 تم تنزيل الفيديو بنجاح: {video_path}")
            break

    if not video_path:
        print("❌ لم يتم العثور على أي فيديو لتنزيله أو رفعه.")
        return

    # رفع الفيديو بعد التنزيل
    try:
        upload_to_youtube(video_path, video_title)
    except Exception as e:
        print(f"❌ حدث خطأ أثناء عملية الرفع إلى يوتيوب: {e}")

if __name__ == "__main__":
    main()
