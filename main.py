import os
import json
import asyncio
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import requests
import edge_tts
from edge_tts import SubMaker
import subprocess
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont, ImageStat

# جلب مفتاح API من إعدادات GitHub Secrets
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def download_arabic_font():
    """تحميل خط عربي ممتاز لنصوص الفيديو"""
    font_path = "Amiri-Bold.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf"
        urllib.request.urlretrieve(url, font_path)
    return font_path

def fix_arabic_text(text):
    """تعديل اتجاه وتوصيل الحروف العربية لتظهر بشكل صحيح"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def get_today_date_str():
    return datetime.datetime.now().strftime("%Y/%m/%d")

def fetch_news_items(rss_url, max_items=8):
    """جلب العناوين من تغذية RSS"""
    items = []
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        root = ET.fromstring(html)
        
        for item in root.findall('.//item')[:max_items]:
            title = item.find('title').text if item.find('title') is not None else ""
            items.append({"title": title})
    except Exception as e:
        print("RSS Fetch Error:", e)
    return items

def get_topic_image(keyword, output_path="background.jpg"):
    """تحميل صورة خلفية مناسبة للحدث بدقة عالية"""
    try:
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://source.unsplash.com/1080x1920/?{encoded_kw},news"
        urllib.request.urlretrieve(url, output_path)
        img = Image.open(output_path)
        img.verify()
        return output_path
    except Exception:
        # خلفية احتياطية أنيقة في حالة تعذر التحميل
        img = Image.new("RGB", (1080, 1920), color=(18, 24, 38))
        img.save(output_path)
        return output_path

def detect_best_text_color(image, region):
    """تحليل سطوع الخلفية لتحديد هل يُكتب باللون الأسود أم الأبيض"""
    try:
        crop_box = image.crop(region)
        gray_crop = crop_box.convert("L")
        stat = ImageStat.Stat(gray_crop)
        avg_brightness = stat.mean[0] # القيمة من 0 (أسود) إلى 255 (أبيض)
        
        # إذا كانت الخلفية فاتحة -> نص أسود بإطار أبيض
        if avg_brightness > 135:
            return (15, 15, 15, 255), (255, 255, 255, 255)
        # إذا كانت الخلفية غامقة -> نص أبيض بإطار أسود
        else:
            return (255, 255, 255, 255), (0, 0, 0, 255)
    except Exception:
        return (255, 255, 255, 255), (0, 0, 0, 255)

def create_video_overlay_frame(text_line, bg_image_path, output_path="frame.png", width=1080, height=1920):
    """رسم النص العربي بدقة فوق الخلفية مع تحديد لون الخط تلقائياً"""
    font_path = download_arabic_font()
    
    bg_img = Image.open(bg_image_path).convert("RGBA").resize((width, height))
    draw = ImageDraw.Draw(bg_img)
    
    try:
        font_caption = ImageFont.truetype(font_path, 58)
    except Exception:
        font_caption = ImageFont.load_default()
        
    fixed_caption = fix_arabic_text(text_line)
    
    bbox = draw.textbbox((0, 0), fixed_caption, font=font_caption)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) // 2
    y = height - 420
    
    region = (max(0, x - 25), max(0, y - 25), min(width, x + text_w + 25), min(height, y + text_h + 25))
    
    text_color, stroke_color = detect_best_text_color(bg_img, region)
    
    draw.text((x, y), fixed_caption, font=font_caption, fill=text_color, stroke_width=4, stroke_fill=stroke_color)
    
    bg_img.save(output_path)
    return output_path

def get_active_free_models():
    """جلب النماذج المجانية النشطة تلقائياً لتفادي أخطاء 404"""
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
    raise Exception("فشل الحصول على السكربت من جميع النماذج المتاحة.")

async def generate_speech_and_subtitles(text, audio_out="audio.mp3"):
    """توليد الصوت والتزامن الصوتي"""
    communicate = edge_tts.Communicate(text, voice="ar-EG-ShakirNeural")
    submaker = SubMaker()
    
    with open(audio_out, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                
    return submaker.get_srt()

def create_90s_video(audio_file, captions_summary, keyword_topic, output_mp4):
    """إنتاج الفيديو النهائي بصيغة Shorts مدته 90 ثانية"""
    bg_img = get_topic_image(keyword_topic, "bg_current.jpg")
    overlay_img = "final_frame.png"
    
    create_video_overlay_frame(captions_summary, bg_img, overlay_img)
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", overlay_img,
        "-i", audio_file,
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_mp4
    ]
    subprocess.run(cmd, check=True)

def process_daily_news():
    print("--- 🎬 جاري إعداد فيديو الأخبار (90 ثانية) ---")
    items = fetch_news_items("https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar", max_items=8)
    headlines_str = "\n".join([it['title'] for it in items])
    
    prompt = f"""إليك أهم عناوين الأخبار اليوم في مصر:
{headlines_str}

اكتب سكربت فيديو Shorts تفصيلي باللغة العربية بأسلوب إخباري مشوق وغني بالمعلومات يستغرق عند القراءة 90 ثانية كاملة (حوالي 180 إلى 220 كلمة). 
اكتب النص المباشر فقط للإلقاء بدون أي مقدمات أو إشارات مشهدية."""

    script = generate_script_from_ai(prompt)
    asyncio.run(generate_speech_and_subtitles(script, "news_90s.mp3"))
    
    main_topic = items[0]['title'] if items else "egypt news"
    short_caption = "أهم أخبار وتطورات اليوم في مصر"
    
    create_90s_video("news_90s.mp3", short_caption, main_topic, "daily_news_90s.mp4")
    print("✅ تم إنشاء فيديو الأخبار الـ 90 ثانية بنجاح!")

def process_daily_prices():
    print("--- 🎬 جاري إعداد فيديو الأسعار (90 ثانية) ---")
    search_query = urllib.parse.quote("سعر الذهب والفضة والدواجن اليوم مصر")
    items = fetch_news_items(f"https://news.google.com/rss/search?q={search_query}&hl=ar&gl=EG&ceid=EG:ar", max_items=8)
    prices_str = "\n".join([it['title'] for it in items])
    
    prompt = f"""إليك أحدث الأخبار والبيانات عن الأسعار اليوم:
{prices_str}

اكتب سكربت فيديو Shorts شاملاً يغطي تحديثات أسعار الذهب بمختلف الأعيرة والفضة وبورصة الدواجن والبيض اليوم في مصر بالتفصيل. 
يجب أن تكون مدة القراءة 90 ثانية تقريباً (حوالي 180 إلى 220 كلمة). اكتب النص المباشر فقط."""

    script = generate_script_from_ai(prompt)
    asyncio.run(generate_speech_and_subtitles(script, "prices_90s.mp3"))
    
    short_caption = "تحديث أسعار الذهب والفضة وبورصة الدواجن"
    create_90s_video("prices_90s.mp3", short_caption, "gold prices market", "daily_prices_90s.mp4")
    print("✅ تم إنشاء فيديو الأسعار الـ 90 ثانية بنجاح!")

if __name__ == "__main__":
    process_daily_news()
    process_daily_prices()
