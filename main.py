import os
import glob
import requests
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= ⚙️ الإعدادات الأساسية =================
# ضع رابط حساب التيك توك الذي تريد السحب منه
import random

# قائمة الحسابات (قصص + قرآن ودينية)
TIKTOK_ACCOUNTS = [
    # حسابات قصص
    "https://www.tiktok.com/@story_account_1",
    "https://www.tiktok.com/@story_account_2",
    
    # حسابات قرآن وأدعية دينية
    "https://www.tiktok.com/@quran_account_1",
    "https://www.tiktok.com/@quran_account_2",
]

# اختيار حساب عشوائي أو التتابع في كل مرة يشتغل فيها السكريبت
TIKTOK_PROFILE_URL = random.choice(TIKTOK_ACCOUNTS)                                                                    

# رقم الواتساب لإرسال الإشعارات (بالصيغة الدولية بدون + أو 00 متبوعاً بـ @c.us)
# مثال لمصر: "201012345678@c.us"
DEFAULT_PHONE = "2010xxxxxxxx@c.us"
WHATSAPP_CHAT_ID = os.getenv("WHATSAPP_PHONE", DEFAULT_PHONE)
# ========================================================

def send_whatsapp_message(message):
    id_instance = os.environ.get("GREEN_ID_INSTANCE")
    api_token = os.environ.get("GREEN_API_TOKEN")
    
    if not id_instance or not api_token:
        print("⚠️ مفاتيح Green API غير متوفرة في متغيرات البيئة.")
        return
        
    url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
    payload = {
        "chatId": WHATSAPP_CHAT_ID,
        "message": message
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📲 حالة إرسال الواتساب: {response.status_code}")
    except Exception as e:
        print(f"⚠️ فشل إرسال رسالة الواتساب: {e}")

def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise Exception("مفاتيح YouTube API غير ممتلئة في GitHub Secrets.")
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    return build("youtube", "v3", credentials=creds)

def download_latest_tiktok_video(profile_url):
    print(f"📥 جاري فحص الحساب {profile_url} وتنزيل أحدث فيديو...")
    
    os.makedirs('final_videos', exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'final_videos/video.%(ext)s',
        'playlistend': 1,  # جلب أحدث فيديو فقط
        'quiet': False,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(profile_url, download=True)
        if 'entries' in info and len(info['entries']) > 0:
            video_info = info['entries'][0]
        else:
            video_info = info
            
    downloaded_files = glob.glob('final_videos/*')
    if not downloaded_files:
        raise Exception("فشل تنزيل الفيديو، لم يتم العثور على ملفات في المجلد.")
        
    video_file = downloaded_files[0]
    title = video_info.get('title', 'فيديو جديد')
    return video_file, title

def upload_to_youtube(video_path, title):
    print("🚀 جاري رفع الفيديو إلى يوتيوب كـ Shorts...")
    youtube = get_youtube_service()
    
    # اقتصاص العنوان وضمان إضافة وسم #Shorts
    clean_title = title[:70] if title else "فيديو جديد"
    full_title = f"{clean_title} #Shorts"
    
    body = {
        'snippet': {
            'title': full_title,
            'description': f"{title}\n\n#Shorts #TikTok #Trending",
            'tags': ['Shorts', 'TikTok', 'Viral'],
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus': 'public',  # خيارات: 'public', 'private', 'unlisted'
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = request.execute()
    video_id = response.get('id')
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"✅ تم الرفع بنجاح! الرابط: {video_url}")
    return video_url

def main():
    try:
        # 1. التنزيل
        video_path, title = download_latest_tiktok_video(TIKTOK_PROFILE_URL)
        
        # 2. الرفع
        video_url = upload_to_youtube(video_path, title)
        
        # 3. التنظيف التلقائي للمساحة
        if os.path.exists(video_path):
            os.remove(video_path)
            
        # 4. إشعار النجاح
        success_msg = f"✅ *تم نشر فيديو جديد بنجاح!*\n\n📌 *العنوان:* {title}\n🔗 *الرابط:* {video_url}"
        send_whatsapp_message(success_msg)
        
    except Exception as e:
        error_msg = f"❌ *حدث خطأ أثناء تشغيل الأتمتة:*\n{str(e)}"
        print(error_msg)
        
        # إرسال إشعار الخطأ للواتساب إذا أمكن
        try:
            send_whatsapp_message(error_msg)
        except Exception:
            pass
            
        # إجبار السكريبت على التوقف وإظهار فشل (Red Error) في GitHub Actions
        raise e

if __name__ == "__main__":
    main()
