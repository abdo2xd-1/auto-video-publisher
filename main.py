import os
import glob
import json
import time
import random
import re
import subprocess
import requests
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 📌 القائمة العشوائية الافتراضية (10 صفحة)
# ==========================================
DEFAULT_TARGET_CHANNELS = [
    "https://www.tiktok.com/@yasser_aldosari",
    "https://www.tiktok.com/@islamsobhiofficial",
    "https://www.tiktok.com/@alafasy",
    "https://www.tiktok.com/@maher_almuaiqly",
    "https://www.tiktok.com/@mansour_alsalmi",
    "https://www.tiktok.com/@hazza_alblushi",
    "https://www.tiktok.com/@sherif_mostafa",
    "https://www.tiktok.com/@ahmed_alnufais",
    "https://www.tiktok.com/@fcbarcelona",
    "https://www.tiktok.com/@khaby.lame",
]

MY_PHONE_NUMBER = "201211615424@c.us"
OUTPUT_DIR = "final_videos"
POSTED_HISTORY_FILE = "posted_videos.json"
USER_CHANNELS_FILE = "user_channels.json"

# ==========================================
# 💾 إدارة البيانات والملفات
# ==========================================
def load_json(filename, default_value):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default_value
    return default_value

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ensure_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# ==========================================
# 📱 فحص الواتساب لروابط الفيديوهات أو الصفحات
# ==========================================
def process_whatsapp_incoming():
    id_instance = os.environ.get("GREEN_ID_INSTANCE")
    api_token = os.environ.get("GREEN_API_TOKEN")

    if not id_instance or not api_token:
        return None

    url = f"https://api.green-api.com/waInstance{id_instance}/lastIncomingMessages/{api_token}?minutes=240"
    direct_video_url = None

    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            messages = res.json()
            user_channels = load_json(USER_CHANNELS_FILE, [])
            updated = False

            for msg in messages:
                sender = msg.get("senderData", {}).get("chatId")
                if sender == MY_PHONE_NUMBER:
                    text_data = msg.get("messageData", {}).get("textMessageData", {}).get("textMessage", "")
                    urls = re.findall(r'https?://[^\s]*tiktok\.com[^\s]*', text_data)

                    for link in urls:
                        # إذا كان رابط فيديو مباشر
                        if "/video/" in link or "vt.tiktok.com" in link or "vm.tiktok.com" in link:
                            direct_video_url = link
                        # إذا كان رابط صفحة/حساب
                        elif "@" in link:
                            clean_channel = link.split("?")[0]
                            if clean_channel not in user_channels:
                                user_channels.append(clean_channel)
                                updated = True
                                print(f"➕ تم إضافة صفحة جديدة من الواتساب: {clean_channel}")

            if updated:
                save_json(USER_CHANNELS_FILE, user_channels)

    except Exception as e:
        print(f"⚠️ خطأ أثناء قراءة رسائل الواتساب: {e}")

    return direct_video_url

# ==========================================
# 📱 إرسال إشعار الواتساب
# ==========================================
def send_whatsapp_message(text):
    id_instance = os.environ.get("GREEN_ID_INSTANCE")
    api_token = os.environ.get("GREEN_API_TOKEN")

    if not id_instance or not api_token:
        print("⚠️ مفاتيح Green API غير متوفرة.")
        return

    url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
    payload = {
        "chatId": MY_PHONE_NUMBER,
        "message": text
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        print(f"📱 نتيجة الواتساب ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"❌ خطأ إرسال الواتساب: {e}")

# ==========================================
# 🖼️ دمج اللوجو
# ==========================================
def apply_logo_watermark(input_video_path, logo_path="logo.png"):
    if not os.path.exists(logo_path):
        print(f"ℹ️ لم يتم العثور على ملف اللوجو ({logo_path})، سيتم النشر بدونه.")
        return input_video_path

    output_video_path = f"{OUTPUT_DIR}/watermarked_{random.randint(1000,9999)}.mp4"
    print("🎨 جاري دمج اللوجو مع الفيديو...")

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
        print(f"⚠️ تعذر وضع اللوجو: {e}")
        return input_video_path

# ==========================================
# 📥 تنزيل فيديو (بدون تكرار ومع معادلة الحسابات)
# ==========================================
def download_video(custom_video_url=None):
    posted_history = load_json(POSTED_HISTORY_FILE, [])
    
    # 1. حالة رابط فيديو مباشر مرسل على الواتساب
    if custom_video_url:
        print(f"📥 جاري معالجة فيديو مخصص من الواتساب: {custom_video_url}")
        ydl_opts = {
            'outtmpl': f'{OUTPUT_DIR}/downloaded_raw_%(id)s.%(ext)s',
            'format': 'mp4/bestvideo+bestaudio/best',
            'overwrites': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(custom_video_url, download=True)
            video_id = info.get('id')
            
            if video_id in posted_history:
                print("⚠️ هذا الفيديو المخصص تم نشره سابقاً!")
            else:
                title = info.get('title', 'فيديو خاص')
                downloaded_files = glob.glob(f"{OUTPUT_DIR}/downloaded_raw_*")
                if downloaded_files:
                    return downloaded_files[0], title, video_id

    # 2. احتساب الصفحات النشطة (حذف 10 عشوائية مقابل كل صفحة خاصة بك)
    user_channels = load_json(USER_CHANNELS_FILE, [])
    num_user_channels = len(user_channels)
    
    # استبعاد 10 صفحات افتراضية مقابل كل صفحة أضيفها المستخدم
    remove_count = num_user_channels * 10
    remaining_defaults = DEFAULT_TARGET_CHANNELS[remove_count:] if remove_count < len(DEFAULT_TARGET_CHANNELS) else []

    # القائمة الكلية القابلة للاختيار (صفحاتك + ما تبقى من العشوائي)
    active_pool = user_channels + remaining_defaults

    if not active_pool:
        active_pool = user_channels  # إذا انتهت القائمة العشوائية، نعتمد على صفحاتك فقط

    print(f"📊 القنوات المتاحة حالياً: {len(active_pool)} (صفحاتك: {len(user_channels)} | العشوائي المتبقي: {len(remaining_defaults)})")

    # 3. اختيار فيديو غير مكرر
    for attempt in range(15):
        selected_channel = random.choice(active_pool)
        random_video_index = random.randint(1, 15)
        print(f"🔍 [محاولة {attempt+1}] البحث في: {selected_channel} (فيديو {random_video_index})")

        ydl_opts = {
            'outtmpl': f'{OUTPUT_DIR}/downloaded_raw_%(id)s.%(ext)s',
            'playlist_items': str(random_video_index),
            'format': 'mp4/bestvideo+bestaudio/best',
            'match_filter': yt_dlp.utils.match_filter_func('duration <= 60'),
            'overwrites': True,
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(selected_channel, download=False)
                entries = info.get('entries', [])
                if entries:
                    video_data = entries[0]
                    vid_id = video_data.get('id')
                    
                    if vid_id in posted_history:
                        print(f"⏭️ تخطي Video ID: {vid_id} (تم نشره سابقاً)")
                        continue
                    
                    # تحميل الفيديو لأنه غير مكرر
                    ydl.download([video_data.get('webpage_url', selected_channel)])
                    title = video_data.get('title', 'فيديو جديد')
                    downloaded_files = glob.glob(f"{OUTPUT_DIR}/downloaded_raw_*")
                    if downloaded_files:
                        return downloaded_files[0], title, vid_id
        except Exception as e:
            print(f"⚠️ خطأ أثناء التنزيل: {e}")

    raise Exception("❌ لم يتم العثور على أي فيديو جديد غير مكرر.")

# ==========================================
# 📤 الرفع للقنوات
# ==========================================
def upload_to_all_youtube_channels(video_path, title):
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")

    channels = []
    if os.environ.get("YOUTUBE_REFRESH_TOKEN"):
        channels.append(("القناة الأولى 🔴", os.environ.get("YOUTUBE_REFRESH_TOKEN")))
    if os.environ.get("YOUTUBE_REFRESH_TOKEN_2"):
        channels.append(("القناة الثانية 🔵", os.environ.get("YOUTUBE_REFRESH_TOKEN_2")))

    if not channels:
        raise ValueError("❌ لا توجد رموز Refresh Tokens لقنوات يوتيوب!")

    results = []
    clean_title = title[:75] if title else "فيديو جديد"
    full_title = f"{clean_title} #Shorts"

    for ch_name, refresh_token in channels:
        print(f"🚀 جاري الرفع إلى {ch_name}...")
        try:
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
            request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()

            video_id = response.get("id")
            url = f"https://youtube.com/shorts/{video_id}"
            print(f"✅ تم الرفع على {ch_name}! الرابط: {url}")
            results.append((ch_name, url))
        except Exception as e:
            print(f"❌ فشل الرفع على {ch_name}: {e}")

    return results

def main():
    ensure_directories()
    try:
        # 1. قراءة الواتساب لمعالجة الصفحات الجديدة أو روابط الفيديوهات المباشرة
        direct_video_url = process_whatsapp_incoming()

        # 2. تنزيل فيديو جديد غير مكرر
        raw_video_path, title, video_id = download_video(custom_video_url=direct_video_url)

        # 3. دمج اللوجو
        final_video_path = apply_logo_watermark(raw_video_path, logo_path="logo.png")

        # 4. الرفع لقنوات يوتيوب
        results = upload_to_all_youtube_channels(final_video_path, title)

        # 5. تسجيل الـ ID لمنع التكرار مستقبلاً
        posted_history = load_json(POSTED_HISTORY_FILE, [])
        if video_id and video_id not in posted_history:
            posted_history.append(video_id)
            save_json(POSTED_HISTORY_FILE, posted_history)

        # 6. إرسال إشعار الواتساب
        links_text = "\n".join([f"{ch}: {url}" for ch, url in results])
        msg = f"🎉 *تم نشر فيديو Shorts جديد بنجاح!*\n\n📌 *ID الفيديو:* `{video_id}`\n📝 *العنوان:* {title}\n\n🔗 *الروابط:*\n{links_text}"
        send_whatsapp_message(msg)

        # تنظيف الملفات المؤقتة
        for file in glob.glob(f"{OUTPUT_DIR}/*"):
            try:
                os.remove(file)
            except Exception:
                pass

    except Exception as e:
        error_msg = f"❌ *حدث خطأ أثناء أتمتة النشر:*\n{str(e)}"
        print(error_msg)
        send_whatsapp_message(error_msg)
        raise e

if __name__ == "__main__":
    main()
