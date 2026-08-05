import os
import requests
import yt_dlp
import subprocess
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- المتغيرات البيئية ---
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

# قائمة التوكينات الخاصة بكل قناة
REFRESH_TOKENS = [
    os.getenv("YOUTUBE_REFRESH_TOKEN_1"),
    os.getenv("YOUTUBE_REFRESH_TOKEN_2")
]

GREEN_API_INSTANCE = os.getenv("GREEN_API_INSTANCE_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE_NUMBER")

# رابط تيك توك المستهدف (أو قائمة الحسابات)
TIKTOK_TARGET = "https://www.tiktok.com/@example_account"


def download_tiktok_video(url, output_path="downloaded.mp4"):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'overwrites': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path


def add_watermark(input_video, watermark_image="logo.png", output_video="final_video.mp4"):
    if not os.path.exists(watermark_image):
        print("ملف اللوجو غير موجود، سيتم رفع الفيديو بدون لوجو.")
        return input_video
    
    # دمج اللوجو في أعلى اليسار باستخدام FFmpeg
    cmd = f"ffmpeg -i {input_video} -i {watermark_image} -filter_complex 'overlay=10:10' -codec:a copy {output_video} -y"
    subprocess.run(cmd, shell=True, check=True)
    return output_video


def get_youtube_service(refresh_token):
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build("youtube", "v3", credentials=creds)


def upload_to_youtube(service, video_file, title, description):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["Shorts", "Islamic", "TikTok"],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return f"https://youtube.com/shorts/{response['id']}"


def send_whatsapp_notification(message):
    if not all([GREEN_API_INSTANCE, GREEN_API_TOKEN, WHATSAPP_PHONE]):
        print("بيانات Green API غير متوفرة، لن يتم إرسال إشعار.")
        return
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{WHATSAPP_PHONE}@c.us",
        "message": message
    }
    requests.post(url, json=payload)


def main():
    report = ["🤖 **تقرير النشر اليومي:**\n"]
    
    try:
        # 1. تنزيل الفيديو
        raw_video = download_tiktok_video(TIKTOK_TARGET)
        
        # 2. إضافة العلامة المائية
        final_video = add_watermark(raw_video)
        report.append("✅ تم تنزيل الفيديو وتعديله بنجاح.\n")
        
        # 3. الرفع على القنوات المحددة
        for idx, token in enumerate(REFRESH_TOKENS, start=1):
            if not token:
                report.append(f"⚠️ القناة {idx}: لم يتم ضبط Refresh Token.")
                continue
            
            try:
                service = get_youtube_service(token)
                video_url = upload_to_youtube(
                    service, 
                    final_video, 
                    "مقطع قصير #Shorts", 
                    "تم النشر تلقائياً بواسطة البوت"
                )
                report.append(f"🚀 **القناة {idx}:** {video_url}")
            except Exception as e:
                report.append(f"❌ **القناة {idx}:** فشل الرفع ({str(e)})")

    except Exception as e:
        report.append(f"💥 خطأ عام في السكربت: {str(e)}")

    # 4. إرسال النتيجة إلى الواتساب
    send_whatsapp_notification("\n".join(report))


if __name__ == "__main__":
    main()
