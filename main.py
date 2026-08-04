import os
import re
import glob
import json
import asyncio
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import requests
import edge_tts
import subprocess
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont, ImageStat

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_arabic_font(size=52):
    """جلب الخط العربي المباشر المثبت على السيرفر لتفادي أي تشويه"""
    system_font_path = "/usr/share/fonts/truetype/amiri/Amiri-Bold.ttf"
    if os.path.exists(system_font_path):
        return ImageFont.truetype(system_font_path, size)
    try:
        return ImageFont.truetype("Amiri-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

def fix_arabic_text(text):
    """تعديل وتشكيل الحروف العربية واتجاه الكتابة"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def fetch_news_items_with_images(rss_url, max_items=5):
    """جلب قائمة الأخبار اليومية"""
    items = []
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        root = ET.fromstring(html)
        
        for idx, item in enumerate(root.findall('.//item')[:max_items]):
            title = item.find('title').text if item.find('title') is not None else f"خبر {idx+1}"
            items.append({"title": title})
    except Exception as e:
        print("RSS Fetch Error:", e)
    return items

def download_image_for_topic(keyword, output_path, fallback_color=(20, 30, 45)):
    """تحميل صورة خلفية متغيرة ومتناسقة مع عنوان الخبر"""
    try:
        clean_kw = re.sub(r'[^\w\s]', '', keyword)[:30]
        encoded_kw = urllib.parse.quote(clean_kw)
        url = f"https://picsum.photos/seed/{encoded_kw}/1080/1920"
        urllib.request.urlretrieve(url, output_path)
        img = Image.open(output_path)
        img.verify()
        return output_path
    except Exception:
        img = Image.new("RGB", (1080, 1920), color=fallback_color)
        img.save(output_path)
        return output_path

def detect_best_text_color(image, region):
    """فحص سطوع الصورة وتحديد هل يُكتب باللون الأبيض أو الأسود"""
    try:
        crop_box = image.crop(region)
        gray_crop = crop_box.convert("L")
        stat = ImageStat.Stat(gray_crop)
        avg_brightness = stat.mean[0]
        
        if avg_brightness > 135:
            return (10, 10, 10, 255), (255, 255, 255, 255)  # نص أسود بإطار أبيض
        else:
            return (255, 255, 255, 255), (0, 0, 0, 255)      # نص أبيض بإطار أسود
    except Exception:
        return (255, 255, 255, 255), (0, 0, 0, 255)

def render_scene_frame(text_line, bg_image_path, output_path, width=1080, height=1920):
    """تركيب كتابة الخبر العربي الصحيحة فوق الصورة"""
    bg_img = Image.open(bg_image_path).convert("RGBA").resize((width, height))
    draw = ImageDraw.Draw(bg_img)
    font_caption = get_arabic_font(52)
    
    fixed_caption = fix_arabic_text(text_line)
    
    bbox = draw.textbbox((0, 0), fixed_caption, font=font_caption)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) // 2
    y = height - 450
    
    region = (max(0, x - 20), max(0, y - 20), min(width, x + text_w + 20), min(height, y + text_h + 20))
    text_color, stroke_color = detect_best_text_color(bg_img, region)
    
    draw.text((x, y), fixed_caption, font=font_caption, fill=text_color, stroke_width=4, stroke_fill=stroke_color)
    bg_img.save(output_path)

def get_active_free_models():
    """جلب النماذج المجانية المتاحة حالياً على OpenRouter"""
    url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            models_data = response.json().get('data', [])
            free_models = [m['id'] for m in models_data if m.get('id', '').endswith(':free')]
            if free_models:
                return free_models
    except Exception:
        pass
    return ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.2-1b-instruct:free"]

def generate_script_from_ai(prompt_context):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip() if OPENROUTER_API_KEY else ''}",
        "Content-Type": "application/json"
    }
    for model in get_active_free_models():
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_context}]
        }
        try:
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                content = res.json()['choices'][0]['message']['content']
                if content:
                    return content.strip()
        except Exception:
            continue
    raise Exception("فشل الحصول على السكربت من جميع النماذج.")

async def generate_speech(text, audio_out="audio.mp3"):
    """توليد الملف الصوتي بواسطة Edge TTS"""
    communicate = edge_tts.Communicate(text, voice="ar-EG-ShakirNeural")
    await communicate.save(audio_out)

def create_slideshow_video(news_items, audio_file, output_mp4, target_duration=90):
    """إنتاج فيديو مدته 90 ثانية تتنقل فيه الصور مع العناوين"""
    num_items = len(news_items) if news_items else 1
    per_image_duration = target_duration / num_items
    
    frames = []
    for i, item in enumerate(news_items):
        bg_path = f"bg_{i}.jpg"
        frame_path = f"frame_{i}.png"
        
        download_image_for_topic(item['title'], bg_path)
        render_scene_frame(item['title'][:45], bg_path, frame_path)
        frames.append((frame_path, per_image_duration))
        
    with open("input_slides.txt", "w", encoding="utf-8") as f:
        for frame_path, dur in frames:
            f.write(f"file '{frame_path}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{frames[-1][0]}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", "input_slides.txt",
        "-i", audio_file,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    subprocess.run(cmd, check=True)

def process_daily_news():
    print("--- 🎬 جاري إعداد فيديو الأخبار (90 ثانية) ---")
    items = fetch_news_items_with_images("https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar", max_items=5)
    headlines_str = "\n".join([f"- {it['title']}" for it in items])
    
    prompt = f"""إليك عناوين الأخبار اليوم في مصر:
{headlines_str}

اكتب سكربت فيديو إخباري Shorts ممتع وطويل بالتفاصيل يتناول هذه الأخبار بشرح مشوق.
يجب أن يكون السكربت طويلاً يحتوي على 280 إلى 320 كلمة تقريباً حتى تستغرق قراءته 90 ثانية كاملة بصوت متأنٍ.
اكتب النص المباشر فقط للإلقاء بدون أي مقدمات أو هوامش."""

    script = generate_script_from_ai(prompt)
    asyncio.run(generate_speech(script, "news_90s.mp3"))
    create_slideshow_video(items, "news_90s.mp3", "daily_news_90s.mp4", target_duration=90)
    print("✅ فيديو الأخبار الـ 90 ثانية جاهز!")

def process_daily_prices():
    print("--- 🎬 جاري إعداد فيديو الأسعار (90 ثانية) ---")
    search_query = urllib.parse.quote("سعر الذهب والفضة والدواجن اليوم مصر")
    items = fetch_news_items_with_images(f"https://news.google.com/rss/search?q={search_query}&hl=ar&gl=EG&ceid=EG:ar", max_items=5)
    prices_str = "\n".join([f"- {it['title']}" for it in items])
    
    prompt = f"""إليك تحديثات الأسعار اليوم في مصر:
{prices_str}

اكتب سكربت فيديو Shorts تفصيلي وشامل يغطي حركة أسعار الذهب بمختلف الأعيرة والفضة وبورصة الدواجن والبيض اليوم في مصر.
يجب أن يكون النص طويلاً ومفصلاً يتكون من 280 إلى 320 كلمة لتدوم القراءة 90 ثانية بالتمام.
اكتب النص المباشر للإلقاء فقط."""

    script = generate_script_from_ai(prompt)
    asyncio.run(generate_speech(script, "prices_90s.mp3"))
    create_slideshow_video(items, "prices_90s.mp3", "daily_prices_90s.mp4", target_duration=90)
    print("✅ فيديو الأسعار الـ 90 ثانية جاهز!")

if __name__ == "__main__":
    process_daily_news()
    process_daily_prices()
