import os
import json
import asyncio
import datetime
import urllib.request
import xml.etree.ElementTree as ET
import requests
import edge_tts
import subprocess

# جلب المفاتيح من الأسرار
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
            headlines.append(title)
        return "\n".join(headlines)
    except Exception as e:
        print("RSS Fetch Error:", e)
        return "لا توجد أحدث بيانات متاحة حالياً."

def generate_script_from_ai(prompt_context):
    """توليد السكربت عبر OpenRouter"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [
            {
                "role": "user",
                "content": prompt_context
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    return result['choices'][0]['message']['content'].strip()

async def text_to_speech(text, output_audio="audio.mp3"):
    """تحويل النص بصوت عربي شجي وممتاز"""
    communicate = edge_tts.Communicate(text, voice="ar-EG-ShakirNeural")
    await communicate.save(output_audio)

def create_short_video(audio_file, text_title, output_mp4):
    """دمج الصوت وخلفية سوداء راقية مع كتابة العنوان وتاريخ اليوم كـ MP4 راسي للـ Shorts/Reels"""
    today_str = get_today_date_str()
    # استخدام FFmpeg لإنشاء فيديو راسي 1080x1920
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=30",
        "-i", audio_file,
        "-vf", f"drawtext=text='{text_title}':fontcolor=yellow:fontsize=50:x=(w-text_w)/2:y=(h-text_h)/2-100,"
               f"drawtext=text='تاريخ اليوم\\: {today_str}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2+100",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        output_mp4
    ]
    subprocess.run(cmd, check=False)

def process_daily_news_video():
    """الفيديو الأول: أخبار اليوم"""
    print("--- جاري إعداد فيديو أخبار اليوم ---")
    today_date = get_today_date_str()
    
    # 1. جلب الأخبار الحية
    news_data = fetch_rss_headlines("https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar")
    
    prompt = f"إليك أهم عناوين الأخبار اليوم في مصر:\n{news_data}\n\nاكتب سكربت فيديو Shorts قصير جداً وموجز باللغة العربية بأسلوب إخباري مشوق مدته 20 ثانية لتلخيص هذه الأخبار. اكتب النص فقط بدون مقدمات."
    script = generate_script_from_ai(prompt)
    
    # 2. تحويل لصوت
    asyncio.run(text_to_speech(script, "news_audio.mp3"))
    
    # 3. إخراج الفيديو MP4
    create_short_video("news_audio.mp3", "أخبار اليوم", "daily_news_video.mp4")
    
    # 4. الوصف الخاص بالفيديو
    description = f"أخبار اليوم - {today_date}"
    print(f"✅ تم إنشاء فيديو الأخبار! الوصف: {description}")

def process_prices_video():
    """الفيديو الثاني: أسعار الذهب والفضة والدواجن"""
    print("--- جاري إعداد فيديو أسعار الذهب والفضة والدواجن ---")
    today_date = get_today_date_str()
    
    # 1. جلب أسعار الذهب والفضة والدواجن الحية اليوم
    rss_url = "https://news.google.com/rss/search?q=%DD0%B3%D8%B9%D8%B1+%D8%A7%D9%84%D8%B0%D9%87%D8%A8+%D9%88%D8%A7%D9%84%D9%81%D8%B6%D8%A9+%D9%88%D8%A7%D9%84%D8%AF%D9%88%D8%A7%D8%AC%D9%86+%D8%A7%D9%84%D9%8A%D9%88%D9%85+%D9%85%D8%B5%D8%B1&hl=ar&gl=EG&ceid=EG:ar"
    prices_data = fetch_rss_headlines(rss_url)
    
    prompt = f"إليك أحدث الأخبار والبيانات المتاحة عن أسعار الذهب والفضة والدواجن اليوم في مصر:\n{prices_data}\n\nاكتب سكربت فيديو Shorts قصير يذكر تحديث أسعار الذهب والفضة وبورصة الدواجن اليوم بأسلوب سريع ومباشر. اكتب السكربت فقط."
    script = generate_script_from_ai(prompt)
    
    # 2. تحويل لصوت
    asyncio.run(text_to_speech(script, "prices_audio.mp3"))
    
    # 3. إخراج الفيديو MP4
    create_short_video("prices_audio.mp3", "أسعار الذهب والفضة والدواجن", "daily_prices_video.mp4")
    
    # 4. الوصف الخاص بالفيديو
    description = f"أسعار الذهب والفضة والدواجن في البورصة اليوم - {today_date}"
    print(f"✅ تم إنشاء فيديو الأسعار! الوصف: {description}")

if __name__ == "__main__":
    process_daily_news_video()
    process_prices_video()
