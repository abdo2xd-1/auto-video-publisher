import os
import time
import subprocess
import yt_dlp

# =========================================================
# 📌 قائمة الـ 100 حساب تيك توك المستهدفة (50 قرآن + 50 قصص)
# =========================================================
TARGET_CHANNELS = [
    # ------------------------------------------------------
    # 📖 [ 50 حساب قرآن كريم وتلاوات خاشعة ]
    # ------------------------------------------------------
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
    "https://www.tiktok.com/@quran_english_sub",
    "https://www.tiktok.com/@quran_designs",
    "https://www.tiktok.com/@quran_reminder",
    "https://www.tiktok.com/@quran_status",
    "https://www.tiktok.com/@quran_daily_verses",
    "https://www.tiktok.com/@quran_shorts_ar",
    "https://www.tiktok.com/@tilawat_khashia",
    "https://www.tiktok.com/@quran.333",
    "https://www.tiktok.com/@quran_ar",
    "https://www.tiktok.com/@quran.verses1",
    "https://www.tiktok.com/@versesofquran",
    "https://www.tiktok.com/@quran.mp3",
    "https://www.tiktok.com/@holy_quran_1",
    "https://www.tiktok.com/@quran_karim_9",
    "https://www.tiktok.com/@quran_station",
    "https://www.tiktok.com/@quran_hd",
    "https://www.tiktok.com/@quran_radio",
    "https://www.tiktok.com/@quran_for_you",
    "https://www.tiktok.com/@quran_recitation",
    "https://www.tiktok.com/@quran_soul",
    "https://www.tiktok.com/@quran_light",
    "https://www.tiktok.com/@quran_islamic",
    "https://www.tiktok.com/@quran_noor",
    "https://www.tiktok.com/@quran_37",
    "https://www.tiktok.com/@tilawat_quran",
    "https://www.tiktok.com/@quran_live",
    "https://www.tiktok.com/@quran_karem_1",
    "https://www.tiktok.com/@quran_reminder1",
    "https://www.tiktok.com/@quran_audio",
    "https://www.tiktok.com/@quran_clips",
    "https://www.tiktok.com/@quran_peace",
    "https://www.tiktok.com/@quran_world",
    "https://www.tiktok.com/@quran_media",
    "https://www.tiktok.com/@quran_top",

    # ------------------------------------------------------
    # 🎭 [ 50 حساب قصص ريديت وحكايات درامية ]
    # ------------------------------------------------------
    "https://www.tiktok.com/@reddit.stories.ar",
    "https://www.tiktok.com/@arabic_reddit_stories",
    "https://www.tiktok.com/@reddit_stories_eg",
    "https://www.tiktok.com/@reddit_arabic",
    "https://www.tiktok.com/@reddit_stories_daily",
    "https://www.tiktok.com/@reddit.stories",
    "https://www.tiktok.com/@redditstories_ar",
    "https://www.tiktok.com/@reddit_drama",
    "https://www.tiktok.com/@redditstories_official",
    "https://www.tiktok.com/@reddit_tales",
    "https://www.tiktok.com/@reddit_storys_ar",
    "https://www.tiktok.com/@reddit_hub_ar",
    "https://www.tiktok.com/@reddit_stories_3",
    "https://www.tiktok.com/@reddit.stories.eg",
    "https://www.tiktok.com/@storytime_ar",
    "https://www.tiktok.com/@arabic_stories_1",
    "https://www.tiktok.com/@drama_stories_ar",
    "https://www.tiktok.com/@stories_reddit_ar",
    "https://www.tiktok.com/@reddit_arabic_stories",
    "https://www.tiktok.com/@reddit.shorts.ar",
    "https://www.tiktok.com/@reddit_talk_ar",
    "https://www.tiktok.com/@reddit_clips_ar",
    "https://www.tiktok.com/@reddit_stories101",
    "https://www.tiktok.com/@reddit_stories_hd",
    "https://www.tiktok.com/@reddit_stories_pro",
    "https://www.tiktok.com/@reddit_tales_ar",
    "https://www.tiktok.com/@reddit_arabic_official",
    "https://www.tiktok.com/@reddit_stories_arabic",
    "https://www.tiktok.com/@stories_ar_1",
    "https://www.tiktok.com/@reddit_stories_club",
    "https://www.tiktok.com/@reddit_stories_plus",
    "https://www.tiktok.com/@reddit_stories_box",
    "https://www.tiktok.com/@reddit_stories_world",
    "https://www.tiktok.com/@reddit_stories_vids",
    "https://www.tiktok.com/@reddit_stories_now",
    "https://www.tiktok.com/@reddit_stories_vip",
    "https://www.tiktok.com/@reddit_stories_hub",
    "https://www.tiktok.com/@reddit_stories_zone",
    "https://www.tiktok.com/@reddit_stories_time",
    "https://www.tiktok.com/@reddit_stories_app",
    "https://www.tiktok.com/@reddit_stories_net",
    "https://www.tiktok.com/@reddit_stories_tv",
    "https://www.tiktok.com/@reddit_stories_cast",
    "https://www.tiktok.com/@reddit_stories_feed",
    "https://www.tiktok.com/@reddit_stories_life",
    "https://www.tiktok.com/@reddit_stories_show",
    "https://www.tiktok.com/@reddit_stories_spot",
    "https://www.tiktok.com/@reddit_stories_channel",
    "https://www.tiktok.com/@reddit_stories_page",
    "https://www.tiktok.com/@reddit_stories_room"
]

WATERMARK_TEXT = "هل صليت على النبي اليوم"
OUTPUT_DIR = "final_videos"

def download_latest_from_tiktok(channel_url, output_filename):
    """تحميل أحدث فيديو بمرونة وبدون تأخير"""
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_filename,
        'playlist_items': '1',
        'overwrites': True,
        'quiet': True,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([channel_url])
        
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            return True, "تم التحميل بنجاح"
        return False, "لم يتم العثور على الفيديو أو الحجم صفر"
    except Exception as e:
        return False, str(e)

def apply_watermark(input_file, output_file, logo_image_path="logo.png"):
    """دمج العلامة المائية وتوحيد صيغة MP4 بجودة عالية"""
    if os.path.exists(logo_image_path):
        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-i", logo_image_path,
            "-filter_complex", "[1:v]scale=180:-1[logo];[0:v][logo]overlay=W-w-30:50",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            output_file
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-vf", f"drawtext=text='{WATERMARK_TEXT}':x=W-tw-40:y=60:fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            output_file
        ]
        
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(input_file):
        os.remove(input_file)

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    successful_count = 0
    failed_count = 0
    total_accounts = len(TARGET_CHANNELS)
    
    print(f"🚀 بدء معالجة {total_accounts} حساب تيك توك (قرآن وقصص)...\n")
    
    for idx, channel in enumerate(TARGET_CHANNELS, start=1):
        temp_input = f"temp_{idx}.mp4"
        final_output = os.path.join(OUTPUT_DIR, f"video_{idx}.mp4")
        
        print(f"[{idx}/{total_accounts}] 🔍 فحص الحساب: {channel}")
        success, msg = download_latest_from_tiktok(channel, temp_input)
        
        if success:
            try:
                apply_watermark(temp_input, final_output, logo_image_path="logo.png")
                successful_count += 1
                print(f"  └─ ✅ نجح التنزيل وإضافة العلامة المائية")
            except Exception as ex:
                print(f"  └─ ⚠️ فشل المونتاج: {ex}")
        else:
            failed_count += 1
            print(f"  └─ ❌ تعذر التحميل: {msg}")
            
        time.sleep(1) # مهلة ثانية واحدة لتفادي حظر الطلبات المتتالية
        
    print(f"\n📊 [ النتيجة النهائية ]: نجح معالجة {successful_count} فيديو | فشل {failed_count} حساب.")
