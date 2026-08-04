import os
import requests
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 1. إرسال إشعار الواتساب عبر Green API
# ==========================================
def send_green_api_message(text):
    id_instance = os.environ.get("GREEN_ID_INSTANCE")
    api_token = os.environ.get("GREEN_API_TOKEN")
    my_phone = "201211615424@c.us"

    if not id_instance or not api_token:
        print("⚠️ لم يتم ضبط أسرار Green API في GitHub Secrets.")
        return

    url = f"https://7107.api.greenapi.com/waInstance{id_instance}/sendMessage/{api_token}"
    payload = {
        "chatId": my_phone,
        "message": text
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            print("📱 تم إرسال إشعار الواتساب بنجاح!")
        else:
            print(f"⚠️ خطأ أثناء إرسال الإشعار: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"❌ خطأ أثناء الاتصال بـ Green API: {e}")


# ==========================================
# 2. الاتصال بـ YouTube API
# ==========================================
def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("❌ أسرار YouTube API غير مكتملة في GitHub Secrets.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    return build("youtube", "v3", credentials=creds)


# ==========================================
# 3. تنزيل فيديو تيك توك
# ==========================================
def download_tiktok_video(tiktok_url, output_filename="video.mp4"):
    print(f"📥 جاري تنزيل الفيديو من: {tiktok_url}")
    
    ydl_opts = {
        'outtmpl': output_filename,
        'format': 'bestvideo+bestaudio/best',
        'overwrites': True,
        'quiet': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(tiktok_url, download=True)
        title = info_dict.get('title', 'فيديو جديد')
        return output_filename, title


# ==========================================
# 4. رفع الفيديو إلى يوتيوب
# ==========================================
def upload_to_youtube(youtube, video_path, title):
    print("📤 جاري رفع الفيديو إلى يوتيوب...")
    
    body = {
        'snippet': {
            'title': title[:100],  # الحد الأقصى للعنوان في يوتيوب 100 حرف
            'description': f'{title}\n\n#Shorts #TikTok',
            'tags': ['Shorts', 'TikTok', 'Automation'],
            'categoryId': '22'  # 22 = People & Blogs
        },
        'status': {
            'privacyStatus': 'public',  # خيارات: 'public', 'unlisted', 'private'
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"📊 التقدم: {int(status.progress() * 100)}%")

    video_id = response.get('id')
    print(f"✅ تم الرفع بنجاح! ID الفيديو: {video_id}")
    return video_id


# ==========================================
# 5. دالة التشغيل الرئيسية
# ==========================================
def main():
    # يمكنك وضع رابط الفيديو أو جلبه من متغيرات البيئة
    tiktok_url = os.environ.get("TIKTOK_URL", "https://www.tiktok.com/@username/video/1234567890")

    try:
        # تنزيل الفيديو
        video_file, video_title = download_tiktok_video(tiktok_url)

        # الاتصال بـ يوتيوب
        youtube = get_youtube_service()

        # رفع الفيديو
        youtube_id = upload_to_youtube(youtube, video_file, video_title)
        youtube_url = f"https://youtu.be/{youtube_id}"

        # إرسال إشعار النجاح على الواتساب
        success_msg = (
            f"🎉 *تم نشر فيديو جديد بنجاح!*\n\n"
            f"📌 *العنوان:* {video_title}\n"
            f"🔗 *الرابط:* {youtube_url}"
        )
        send_green_api_message(success_msg)

        # حذف ملف الفيديو المؤقت بعد الرفع
        if os.path.exists(video_file):
            os.remove(video_file)

    except Exception as e:
        error_msg = f"❌ *حدث خطأ أثناء تنفيذ الأتمتة:*\n{str(e)}"
        print(error_msg)
        send_green_api_message(error_msg)


if __name__ == "__main__":
    main()
