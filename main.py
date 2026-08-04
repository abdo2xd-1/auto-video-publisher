import os
import subprocess
import yt_dlp

# قائمة القنوات والحسابات المستهدفة (يوتيوب وتيك توك)
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

# النص أو المعرف الخاص بك للعلامة المائية
WATERMARK_TEXT = "@MyChannelName"

def download_latest_from_channel(channel_url, output_filename="input_video.mp4"):
    """جلب وتحميل أحدث فيديو من رابط يوتيوب أو تيك توك"""
    print(f"🔍 جاري فحص الرابط: {channel_url}")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'playlistend': 1,  # تحميل أحدث فيديو واحد فقط
        'overwrites': True,
        'quiet': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([channel_url])
        if os.path.exists(output_filename):
            print("✅ تم تحميل أحدث فيديو بنجاح.")
            return True
    except Exception as e:
        print(f"⚠️ تعذر التحميل من {channel_url}: {e}")
    return False

def apply_watermark(input_file, output_file, logo_image_path="logo.png", text_brand="@Channel"):
    """دمج العلامة المائية فوق الفيديو"""
    print("🎨 جاري تطبيق العلامة المائية...")
    
    if os.path.exists(logo_image_path):
        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-i", logo_image_path,
            "-filter_complex", "overlay=W-w-30:30",
            "-codec:a", "copy",
            output_file
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-vf", f"drawtext=text='{text_brand}':x=W-tw-40:y=40:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.5",
            "-codec:a", "copy",
            output_file
        ]
        
    subprocess.run(cmd, check=True)
    print(f"✨ تم إنتاج الفيديو الجاهز: {output_file}")

if __name__ == "__main__":
    for channel in TARGET_CHANNELS:
        success = download_latest_from_channel(channel, "input_video.mp4")
        if success:
            apply_watermark("input_video.mp4", "output_watermarked.mp4", logo_image_path="logo.png", text_brand=WATERMARK_TEXT)
            break
