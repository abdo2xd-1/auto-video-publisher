import os
import glob
import random
import subprocess
import requests
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 📌 قائمة الحسابات (قرآن + قصص)
# ==========================================
TARGET_CHANNELS = [
    # --- حسابات قرآن ودينية ---
    "https://www.tiktok.com/@yasser_aldosari",
    "https://www.tiktok.com/@islamsobhiofficial",
    "https://www.tiktok.com/@alafasy",
    "https://www.tiktok.com/@maher_almuaiqly",
    "https://www.tiktok.com/@mansour_alsalmi",
    "https://www.tiktok.com/@hazza_alblushi",
    "https://www.tiktok.com/@sherif_mostafa",
    "https://www.tiktok.com/@ahmed_alnufais",
    
    # --- حسابات قصص وترفيه ---
    "https://www.tiktok.com/@fcbarcelona",
    "https://www.tiktok.com/@khaby.lame",
]

MY_PHONE_NUMBER = "201211615424@c.us"
OUTPUT_DIR = "final_videos"

def ensure_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# ==========================================
# 📱 إرسال إشعار الواتساب عبر Green API
# ==========================================
def send_whatsapp_message(text):
    id_instance = os.environ.get("GREEN_ID_INSTANCE")
    api_token = os.environ.get("GREEN_API_TOKEN")

    if not id_instance or not api_token:
        print("⚠️ أسرار Green API غير متوفرة في GitHub Secrets.")
        return

    url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
    payload = {
        "chatId": MY_PHONE_NUMBER,
        "message": text
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        print(f"📱 استجابة الواتساب: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"❌ خطأ أثناء إرسال رسالة الواتساب: {e}")

# ==========================================
# 🖼️ دالة دمج اللوجو مع الفيديو عبر FFmpeg
# ==========================================
def apply_logo_watermark(input_video_path, logo_path="logo.png"):
    if not os.path.exists(logo_path):
        print(f"ℹ️ لم يتم العثور على ملف اللوجو ({logo_path}). سيتم النشر بدون لوجو.")
        return input_video_path

    output_video_path = f"{OUTPUT_DIR}/watermarked_video.mp4"
    print("🎨 جاري دمج اللوجو مع الفيديو...")

    # أمر FFmpeg لوضع اللوجو في أعلى اليمين بحجم مناسب
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', input_video_path,
        '-i', logo_path,
        '-filter_complex', '[1:v]scale=120:-1[logo];[0:v][logo]overlay=W-w-20:20',
        '-c:a', 'copy',
        output_video_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ تم إضافة اللوجو بنجاح!")
        return output_video_path
    except Exception as e:
        print(f"⚠️ فشل وضع اللوجو، سيتم استخدام الفيديو الأصلي: {e}")
        return input_video_path

# ==========================================
# 📥 تنزيل فيديو عشوائي تجنباً لتكرار الفيديو المثبت
# ==========================================
def download_random_latest_video():
    selected_channel = random.choice(TARGET_CHANNELS)
    # اختيار رقم فيديو عشوائي بين أحدث 1 إلى 10 فيديوهات
    random_video_index = random.randint(1, 10)
    
    print(f"🔍 جاري السحب من الحساب: {selected_channel} (فيديو رقم {random_video_index})")

    ydl_opts = {
        'outtmpl': f'{OUTPUT_DIR}/downloaded_raw.%(ext)s',
        'playlist_items': str(random_video_index),
        'format': 'mp4/bestvideo+bestaudio/best',
        'overwrites': True,
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(selected_channel, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                video_info = info['entries'][0]
            else:
                video_info = info

            title = video_info.get('title', 'فيديو جديد')
            downloaded_files = glob.glob(f"{OUTPUT_DIR}/downloaded_raw.*")
            
            if downloaded_files:
                return downloaded_files[0], title
    except Exception as e:
        print(f"⚠️ تعذر التنزيل، جاري المحاولة من حساب آخر: {e}")
        # محاولة احتياطية من حساب آخر
        return download_random_latest_video()

# ==========================================
# 📤 الرفع إلى يوتيوب
# ==========================================
def upload_to_youtube(video_path, title):
    print("🚀 جاري رفع الفيديو إلى يوتيوب...")

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    youtube = build("youtube", "v3", credentials=creds)

    clean_title = title[:75] if title else "فيديو جديد"
    full_title = f"{clean_title} #Shorts"

    request_body = {
        "snippet": {
            "title": full_title,
            "description": f"{title}\n\n#Shorts #Viral #Trending",
            "tags": ["Shorts", "TikTok", "Viral"],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
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

    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"✅ تم الرفع بنجاح! الرابط: {video_url}")
    return video_url

def main():
    ensure_directories()

    try:
        raw_video_path, title = download_random_latest_video()
        final_video_path = apply_logo_watermark(raw_video_path, logo_path="logo.png")
        youtube_url = upload_to_youtube(final_video_path, title)

        msg = f"🎉 *تم نشر فيديو جديد بنجاح!*\n\n📌 *العنوان:* {title}\n🔗 *الرابط:* {youtube_url}"
        send_whatsapp_message(msg)

        for file in glob.glob(f"{OUTPUT_DIR}/*"):
            try:
                os.remove(file)
            except Exception:
                pass

    except Exception as e:
        error_msg = f"❌ *حدث خطأ أثناء تشغيل الأتمتة:*\n{str(e)}"
        print(error_msg)
        send_whatsapp_message(error_msg)
        raise e

if __name__ == "__main__":
    main()
