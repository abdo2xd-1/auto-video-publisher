import os
import subprocess
import urllib.parse
import yt_dlp

# قائمة حسابات تيك توك (قصص وقرآن كريم)
TARGET_CHANNELS = [
    # --- حسابات قصص وريديت ---
    "https://www.tiktok.com/@reddit.stories.ar",
    "https://www.tiktok.com/@arabic_reddit_stories",
    "https://www.tiktok.com/@reddit_stories_eg",
    "https://www.tiktok.com/@reddit_arabic",
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_ريديت_بالعربي"),
    "https://www.tiktok.com/@" + urllib.parse.quote("حكايات_الذكاء_الاصطناعي"),
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_وحكايات_واقعية"),
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_قبل_النوم_AR"),
    "https://www.tiktok.com/@" + urllib.parse.quote("اعترافات_واقعية"),
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_دراما_غموض"),
    "https://www.tiktok.com/@" + urllib.parse.quote("حكايات_من_الحياة"),
    "https://www.tiktok.com/@" + urllib.parse.quote("روايات_قصيرة_ar"),
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_مؤثرة_AR"),
    "https://www.tiktok.com/@" + urllib.parse.quote("عالم_القصص_المترجمة"),
    "https://www.tiktok.com/@" + urllib.parse.quote("حكاية_في_دقيقة"),
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_جرائم_واقعية"),
    "https://www.tiktok.com/@" + urllib.parse.quote("غموض_وحكايات"),
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_تيكتوك_الشهيرة"),
    "https://www.tiktok.com/@" + urllib.parse.quote("قصص_ومواقف_صعبة"),
    "https://www.tiktok.com/@" + urllib.parse.quote("حكايات_الواقع"),

    # --- حسابات تلاوات القرآن الكريم والقراء ---
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
    "https://www.tiktok.com/@" + urllib.parse.quote("راحه_نفسيه_قران"),
    "https://www.tiktok.com/@" + urllib.parse.quote("تلاوات_مؤثرة"),
    "https://www.tiktok.com/@" + urllib.parse.quote("روائع_القرآن"),
    "https://www.tiktok.com/@" + urllib.parse.quote("نور_القرآن"),
    "https://www.tiktok.com/@" + urllib.parse.quote("ايات_من_الذكر_الحكيم"),
    "https://www.tiktok.com/@" + urllib.parse.quote("صدقة_جارية_قران"),
    "https://www.tiktok.com/@" + urllib.parse.quote("مجلس_القرآن"),
    "https://www.tiktok.com/@" + urllib.parse.quote("هدى_القرآن")
]

WATERMARK_TEXT = "هل صليت على النبي اليوم"
OUTPUT_DIR = "final_videos"

def download_latest_from_tiktok(channel_url, output_filename):
    """جلب وتحميل أحدث فيديو من تيك توك بأعلى جودة متوفرة"""
    print(f"\n🔍 جاري فحص الحساب: {channel_url}")
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_filename,
        'playlist_items': '1',  # أحدث فيديو فقط
        'overwrites': True,
        'quiet': False,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([channel_url])
        
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            print(f"✅ تم تحميل الفيديو بنجاح: {output_filename}")
            return True
        else:
            print(f"⚠️ لم يتم العثور على فيديوهات جديدة في: {channel_url}")
    except Exception as e:
        print(f"❌ تعذر التحميل من {channel_url}: {e}")
    return False

def apply_watermark(input_file, output_file, logo_image_path="logo.png", text_brand=WATERMARK_TEXT):
    """تطبيق العلامة المائية logo.png وتوحيد صيغة MP4 بجودة عالية"""
    print(f"🎨 جاري دمج العلامة المائية...")
    
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
            "-vf", f"drawtext=text='{text_brand}':x=W-tw-40:y=60:fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            output_file
        ]
        
    subprocess.run(cmd, check=True)
    print(f"✨ تم تجهيز الفيديو النهائي: {output_file}")
    
    # حذف الملف المؤقت لتوفير مساحة السيرفر
    if os.path.exists(input_file):
        os.remove(input_file)

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total_processed = 0
    for idx, channel in enumerate(TARGET_CHANNELS, start=1):
        temp_input = f"temp_{idx}.mp4"
        final_output = os.path.join(OUTPUT_DIR, f"video_{idx}.mp4")
        
        print(f"\n--- 🎬 [ معالجة الحساب {idx} من أصل {len(TARGET_CHANNELS)} ] ---")
        success = download_latest_from_tiktok(channel, temp_input)
        if success:
            apply_watermark(temp_input, final_output, logo_image_path="logo.png")
            total_processed += 1
            
    print(f"\n🎉 اكتمل العمل! تم معالجة وتجهيز {total_processed} فيديو بنجاح.")
