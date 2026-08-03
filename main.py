import os
import json
import asyncio
import requests
import edge_tts

# 1. جلب مفتاح OpenRouter من الأسرار
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_script():
    """توليد نص الفيديو باستخدام الذكاء الاصطناعي"""
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
                "content": "اكتب حقيقة علمية أو تاريخية قصيرة ومدهشة باللغة العربية المشوقة لتكون فيديو Shorts مدته 20 ثانية. قم بكتابة النص فقط بدون أي مقدمات أو خاتمة."
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    script = result['choices'][0]['message']['content'].strip()
    print("Generated Script:", script)
    return script

async def text_to_speech(text, output_file="audio.mp3"):
    """تحويل النص إلى صوت عربي ممتاز"""
    communicate = edge_tts.Communicate(text, voice="ar-EG-ShakirNeural")
    await communicate.save(output_file)
    print("Audio file generated successfully!")

if __name__ == "__main__":
    script_text = generate_script()
    asyncio.run(text_to_speech(script_text))
