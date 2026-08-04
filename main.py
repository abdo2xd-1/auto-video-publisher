import os
import subprocess
import yt_dlp

# قائمة القنوات والحسابات المستهدفة
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

def download_latest_from_channel(channel_url, output_filename="input_video.mp4"):
    """جلب وتحميل أحدث فيديو من يوتيوب أو تيك توك"""
    print(f"🔍 جاري فحص الرابط: {channel_url}")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'playlistend': 1,
        'overwrites': True,
        'quiet': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([channel_url])
        if os.path.exists(output_filename):
            print("✅ تم تحميل الفيديو بنجاح.")
            return True
    except Exception as e:
        print(f"⚠️ تعذر التحميل من {channel_url}: {e}")
    return False

def apply_watermark(input_file, output_file, logo_image_path="logo.png", text_brand=WATERMARK_TEXT):
    """دمج اللوجو بحجم مخصص (180px) في أعلى اليمين أو نص احتياطي"""
    print("🎨 جاري تطبيق العلامة المائية...")
    
    # إذا كانت صورة logo.png موجودة يتم تصغيرها وتطبيقهما أعلى اليمين
    if os.path.exists(logo_image_path):
        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-i", logo_image_path,
            "-filter_complex", "[1:v]scale=180:-1[logo];[0:v][logo]overlay=W-w-30:50",
            "-codec:a", "copy",
            output_file
        ]
    else:
        # نص احتياطي في حال عدم وجود الملف
        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-vf", f"drawtext=text='{text_brand}':x=W-tw-40:y=60:fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5",
            "-codec:a", "copy",
            output_file
        ]
        
    subprocess.run(cmd, check=True)
    print(f"✨ تم إنتاج الفيديو الجاهز: {output_file}")

if __name__ == "__main__":
    for channel in TARGET_CHANNELS:
        success = download_latest_from_channel(channel, "input_video.mp4")
        if success:
            apply_watermark("input_video.mp4", "output_watermarked.mp4", logo_image_path="logo.png")
            break
