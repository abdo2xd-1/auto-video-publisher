import os
import subprocess
import yt_dlp

# قائمة الـ 10 قنوات المستهدفة
TARGET_CHANNELS = [
    "https://www.youtube.com/@hafu/shorts",
    "https://www.youtube.com/@D_fax2/shorts",
    "https://www.youtube.com/@ThrowerJBL/shorts",
    "https://www.youtube.com/@TayceerTV/shorts",
    "https://www.youtube.com/@Storeis_1/shorts",
    "https://www.youtube.com/@Thegreat_Quran/shorts",
    "https://www.tiktok.com/@abo.3aid",
    "https://www.tiktok.com/@chahr_205",
    "https://www.tiktok.com/@rj3vy",
    "https://www.tiktok.com/@_n1zir"
]

WATERMARK_TEXT = "هل صليت على النبي اليوم"
OUTPUT_DIR = "final_videos"

def download_latest_from_channel(channel_url, output_filename):
    """تحميل أحدث فيديو بفرز ترميز H.264 متوافق مع كافة المشغلات"""
    print(f"\n🔍 جاري فحص الرابط: {channel_url}")
    ydl_opts = {
        'format': 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'playlistend': 1,
        'overwrites': True,
        'quiet': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([channel_url])
        if os.path.exists(output_filename):
            print(f"✅ تم تحميل الفيديو خام بنجاح: {output_filename}")
            return True
    except Exception as e:
        print(f"⚠️ تعذر التحميل من {channel_url}: {e}")
    return False

def apply_watermark(input_file, output_file, logo_image_path="logo.png", text_brand=WATERMARK_TEXT):
    """دمج اللوجو بحجم مخصص (180px) وإعادة الترميز بشكل قياسي"""
    print(f"🎨 جاري إضافة العلامة المائية...")
    
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
    print(f"✨ تم إنتاج الفيديو النهائي: {output_file}")
    
    # مسح الفيديو الخام المؤقت
    if os.path.exists(input_file):
        os.remove(input_file)

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for idx, channel in enumerate(TARGET_CHANNELS, start=1):
        temp_input = f"temp_{idx}.mp4"
        final_output = os.path.join(OUTPUT_DIR, f"video_{idx}.mp4")
        
        print(f"\n--- 🎬 [ معالجة القناة {idx} من أصل {len(TARGET_CHANNELS)} ] ---")
        success = download_latest_from_channel(channel, temp_input)
        if success:
            apply_watermark(temp_input, final_output, logo_image_path="logo.png")
