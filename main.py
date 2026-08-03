import os
import json
import asyncio
import datetime
import urllib.request
import xml.etree.ElementTree as ET
import requests
import edge_tts
import subprocess
import arabic_reshaper
from bidi.algorithm import get_display

# جلب المفاتيح من الأسرار
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def download_arabic_font():
    """تحميل خط عربي ممتاز لنصوص الفيديو إذا لم يكن موجوداً"""
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
        urllib.request.urlretrieve(url, font_path)
    return font_path

def fix_arabic_text(text):
    """تعديل اتجاه وتوصيل الحروف العربية لتظهر بشكل صحيح في الفيديو"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def get_today_date_str():
    """تاريخ اليوم بتنسيق YYYY/MM/DD"""
    return datetime.datetime.now().strftime("%Y/%m/%d")

def fetch_rss_headlines(query_url, max_items=5):
    """جلب أحدث الأخبار والبيانات الحية اليوم مجاناً عبر RSS"""
    try:
        req = urllib.request.Request(query_url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        root = ET.fromstring(html)
        headlines = []
        for item in root.findall('.//item')[:max_items]:
            title = item.find('title').text
            if title:
                headlines.append(title)
        return "\n".join(headlines)
    except Exception as e:
        print("RSS Fetch Error:", e)
        return "لا توجد أحدث بيانات متاحة حالياً."

def generate_script_from_ai(prompt_context):
    """توليد السكربت عبر OpenRouter باللغة العربية مع فحص دقيق للخطأ"""
    if not OPENROUTER_API_KEY:
        raise Exception("خطأ: مفتاح OPENROUTER_API_KEY غير موجود أو غير معرف في أسرار GitHub Secrets!")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {
                "role": "user",
                "content": prompt_context
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"❌ خطأ من OpenRouter (الكود {response.status_code}):", response.text)
        raise Exception(f"فشل الطلب من OpenRouter API: {response.text}")

    result = response.json()
    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content'].strip()
    else:
        print("❌ استجابة غير متوقعة من API:", result)
        raise Exception("لم يتم استلام نص من الذكاء الاصطناعي.")

async def text_to_speech(text, output_audio="audio.mp3"):
    """تحويل النص بصوت عربي شجي وممتاز"""
    communicate = edge_tts.Communicate(text, voice="ar-EG-ShakirNeural")
    await communicate.save(output_audio)

def create_short_video(audio_file, arabic_title, output_mp4):
    """صناعة فيديو راسي بصوت وعنوان عربي واضحة عبر ملفات نصية لتفادي خطأ FFmpeg"""
    font_path = download_arabic_font()
    today_str = get_today_date_str()
    
    # تنسيق النصوص العربية
    fixed_title = fix_arabic_text(arabic_title)
    fixed_date = fix_arabic_text(f"تاريخ اليوم: {today_str}")
    
    # حفظ النصوص في ملفات نصية مؤقتة تفادياً لمشاكل FFmpeg
    with open("title.txt", "w", encoding="utf-8") as f:
        f.write(fixed_title)
        
    with open("date.txt", "w", encoding="utf-8") as f:
        f.write(fixed_date)
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=30",
        "-i", audio_file,
        "-vf", f"drawtext=fontfile={font_path}:textfile=title.txt:fontcolor=yellow:fontsize=55:x=(w-text_w)/2:y=(h-text_h)/2-100,"
               f"drawtext=fontfile={font_path}:textfile=date.txt:fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2+100",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        output_mp4
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg Stderr Error:", res.stderr)
        raise Exception("فشل في معالجة الفيديو بواسطة FFmpeg")

def process_daily_news_video():
    """الفيديو الأول: أخبار اليوم"""
    print("--- جاري إعداد فيديو أخبار اليوم ---")
    today_date = get_today_date_str()
    
    news_data = fetch_rss_headlines("https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar")
    prompt = f"إليك أهم عناوين الأخبار اليوم في مصر:\n{news_data}\n\nاكتب سكربت فيديو Shorts قصير جداً باللغة العربية بأسلوب إخباري مشوق مدته 20 ثانية. اكتب النص فقط بدون أي مقدمات."
    script = generate_script_from_ai(prompt)
    
    asyncio.run(text_to_speech(script, "news_audio.mp3"))
    
    video_title = "أخبار اليوم"
    video_description = f"أخبار اليوم - {today_date}"
    
    create_short_video("news_audio.mp3", video_title, "daily_news_video.mp4")
    
    print(f"✅ فيديو الأخبار جاهز!")
    print(f"العنوان: {video_title}")
    print(f"الوصف: {video_description}\n")

def process_prices_video():
    """الفيديو الثاني: أسعار الذهب والفضة والدواجن"""
    print("--- جاري إعداد فيديو أسعار الذهب والفضة والدواجن ---")
    today_date = get_today_date_str()
    
    rss_url = "https://news.google.com/rss/search?q=%DD0%B3%D8%B9%D8%B1+%D8%A7%D9%84%D8%B0%D9%87%D8%A8+%D9%8والفضة+%D9%88%D8%A7%D9%84%D8%AF%D9%88%D8%A7%D8%AC%D9%86+%D8%A7%D9%84%D9%8A%D9%88%D9%85+%D9%85%D8%B5%D8%B1&hl=ar&gl=EG&ceid=EG:ar"
    prices_data = fetch_rss_headlines(rss_url)
    
    prompt = f"إليك أحدث الأخبار والبيانات المتاحة عن أسعار الذهب والفضة والدواجن اليوم في مصر:\n{prices_data}\n\nاكتب سكربت فيديو Shorts قصير يذكر تحديث أسعار الذهب والفضة وبورصة الدواجن اليوم بأسلوب سريع ومباشر باللغة العربية. اكتب السكربت فقط."
    script = generate_script_from_ai(prompt)
    
    asyncio.run(text_to_speech(script, "prices_audio.mp3"))
    
    video_title = "أسعار الذهب والفضة والدواجن"
    video_description = f"أسعار الذهب والفضة والدواجن في البورصة اليوم - {today_date}"
    
    create_short_video("prices_audio.mp3", video_title, "daily_prices_video.mp4")
    
    print(f"✅ فيديو الأسعار جاهز!")
    print(f"العنوان: {video_title}")
    print(f"الوصف: {video_description}\n")

if __name__ == "__main__":
    process_daily_news_video()
    process_prices_video()
