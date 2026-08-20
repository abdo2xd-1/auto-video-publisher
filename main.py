import os
import glob
import json
import time
import random
import re
import subprocess
import requests
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from instagrapi import Client

# ==========================================
# 📌 القوائم والملفات الأساسية
# ==========================================
TARGET_CHANNELS = [
    # --- صيانة وإصلاح الأجهزة المنزلية (غسالات، ثلاجات، تكييف، ميكروويف) ---
    "https://www.tiktok.com/@appliancerepairguy",
    "https://www.tiktok.com/@appliancedoctor",
    "https://www.tiktok.com/@fixitappliances",
    "https://www.tiktok.com/@proappliancerepair",
    "https://www.tiktok.com/@hvac_tech_tips",
    "https://www.tiktok.com/@hvacrepairpro",
    "https://www.tiktok.com/@washingmachinerepair",
    "https://www.tiktok.com/@fridge_repair_pro",
    "https://www.tiktok.com/@microwave_repair",
    "https://www.tiktok.com/@ac_repair_tips",
    "https://www.tiktok.com/@masterappliancetech",
    "https://www.tiktok.com/@home_repairs_101",
    "https://www.tiktok.com/@fix_everything_home",
    "https://www.tiktok.com/@electronicshomerepair",
    "https://www.tiktok.com/@appliancehero",
    "https://www.tiktok.com/@hvac_solutions",
    "https://www.tiktok.com/@home_equipment_fix",
    "https://www.tiktok.com/@cooling_heating_tech",
    "https://www.tiktok.com/@diy_appliance_repair",
    "https://www.tiktok.com/@fixmyfridge",
    "https://www.tiktok.com/@washer_dryer_fix",
    "https://www.tiktok.com/@appliance_parts_expert",
    "https://www.tiktok.com/@hvac_service_life",
    "https://www.tiktok.com/@electric_appliance_diy",
    "https://www.tiktok.com/@quick_home_repair",
    "https://www.tiktok.com/@household_tech_fix",
    "https://www.tiktok.com/@motor_repair_hub",
    "https://www.tiktok.com/@fan_and_motor_fix",
    "https://www.tiktok.com/@smart_appliances_repair",
    "https://www.tiktok.com/@home_cooling_expert",

    # --- صيانة هاردوير الكمبيوتر والماذربورد وكروت الشاشة ---
    "https://www.tiktok.com/@pc_repair_guy",
    "https://www.tiktok.com/@hardware_fix_pro",
    "https://www.tiktok.com/@motherboard_repair",
    "https://www.tiktok.com/@gpu_repair_lab",
    "https://www.tiktok.com/@laptop_hardware_fix",
    "https://www.tiktok.com/@pc_diagnostic_center",
    "https://www.tiktok.com/@cpu_delid_and_fix",
    "https://www.tiktok.com/@computer_resurrection",
    "https://www.tiktok.com/@custom_pc_restoration",
    "https://www.tiktok.com/@pc_board_repair",
    "https://www.tiktok.com/@graphics_card_fix",
    "https://www.tiktok.com/@laptop_board_doctor",
    "https://www.tiktok.com/@hardware_rescue",
    "https://www.tiktok.com/@clean_and_fix_pc",
    "https://www.tiktok.com/@thermal_paste_and_pads",
    "https://www.tiktok.com/@pc_troubleshoot_pro",
    "https://www.tiktok.com/@bios_chip_flashing",
    "https://www.tiktok.com/@pc_hardware_master",
    "https://www.tiktok.com/@powersupply_repair",
    "https://www.tiktok.com/@ram_vrm_repair",
    "https://www.tiktok.com/@broken_pc_rebuild",
    "https://www.tiktok.com/@pc_technician_life",
    "https://www.tiktok.com/@desktop_repair_lab",
    "https://www.tiktok.com/@gaming_pc_restoration",
    "https://www.tiktok.com/@hardware_mod_and_fix",

    # --- صيانة الدوائر الإلكترونية واللحام والقياس (Electronics & Soldering) ---
    "https://www.tiktok.com/@microsoldering_pro",
    "https://www.tiktok.com/@pcb_repair_expert",
    "https://www.tiktok.com/@soldering_skills",
    "https://www.tiktok.com/@electronics_diagnostics",
    "https://www.tiktok.com/@multimeter_mastery",
    "https://www.tiktok.com/@smd_rework_station",
    "https://www.tiktok.com/@circuit_board_revival",
    "https://www.tiktok.com/@bga_reballing_lab",
    "https://www.tiktok.com/@flux_and_solder",
    "https://www.tiktok.com/@electronic_components_fix",
    "https://www.tiktok.com/@capacitor_resistor_tech",
    "https://www.tiktok.com/@power_board_soldering",
    "https://www.tiktok.com/@microscope_soldering",
    "https://www.tiktok.com/@diode_transistor_fix",
    "https://www.tiktok.com/@circuit_short_finder",
    "https://www.tiktok.com/@thermal_cam_repair",
    "https://www.tiktok.com/@trace_repair_jumpers",
    "https://www.tiktok.com/@pcb_trace_soldering",
    "https://www.tiktok.com/@electronics_diy_lab",
    "https://www.tiktok.com/@schematic_diagram_fix",

    # --- صيانة شاشات وأجهزة كهربائية دقيقة ---
    "https://www.tiktok.com/@tv_panel_repair",
    "https://www.tiktok.com/@led_tv_backlight_fix",
    "https://www.tiktok.com/@monitor_repair_lab",
    "https://www.tiktok.com/@oled_screen_doctor",
    "https://www.tiktok.com/@audio_amplifier_fix",
    "https://www.tiktok.com/@speaker_electronics_repair",
    "https://www.tiktok.com/@inverter_repair_pro",
    "https://www.tiktok.com/@battery_pack_spotwelding",
    "https://www.tiktok.com/@ups_power_supply_fix",
    "https://www.tiktok.com/@induction_cooker_repair",

    # --- قنوات صيانة عربية متخصصة (هاردوير وإلكترونيات وأجهزة) ---
    "https://www.tiktok.com/@electronics_arabic",
    "https://www.tiktok.com/@pc_repair_arabic",
    "https://www.tiktok.com/@hardware_egypt",
    "https://www.tiktok.com/@home_appliances_fix_ar",
    "https://www.tiktok.com/@hvac_tech_arabic",
    "https://www.tiktok.com/@electronic_doctor_ar",
    "https://www.tiktok.com/@pc_doctor_ar",
    "https://www.tiktok.com/@solder_arabic_master",
    "https://www.tiktok.com/@appliances_maintenance_ar",
    "https://www.tiktok.com/@motherboard_arabic_fix",
    "https://www.tiktok.com/@electric_fix_arabic",
    "https://www.tiktok.com/@smart_fix_home_ar",
    "https://www.tiktok.com/@tv_repair_arabic",
    "https://www.tiktok.com/@laptop_repair_arabic",
    "https://www.tiktok.com/@tech_repair_ar"
]

MY_PHONE_NUMBER = "201211615424@c.us"
OUTPUT_DIR = "final_videos"
POSTED_HISTORY_FILE = "posted_videos.json"
USER_CHANNELS_FILE = "user_channels.json"

# ==========================================
# 💾 إدارة الملفات والبيانات
# ==========================================
def load_json(filename, default_value):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default_value
    return default_value

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ensure_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# ==========================================
# 📱 فحص رسائل الواتساب الواردة
# ==========================================
def process_whatsapp_incoming():
    id_instance = os.environ.get("GREEN_ID_INSTANCE")
    api_token = os.environ.get("GREEN_API_TOKEN")

    if not id_instance or not api_token:
        return None

    url = f"https://api.green-api.com/waInstance{id_instance}/lastIncomingMessages/{api_token}?minutes=240"
    direct_video_url = None

    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            messages = res.json()
            user_channels = load_json(USER_CHANNELS_FILE, [])
            updated = False

            for msg in messages:
                sender = msg.get("senderData", {}).get("chatId")
                if sender == MY_PHONE_NUMBER:
                    text_data = msg.get("messageData", {}).get("textMessageData", {}).get("textMessage", "")
                    urls = re.findall(r'https?://[^\s]*tiktok\.com[^\s]*', text_data)

                    for link in urls:
                        if "/video/" in link or "vt.tiktok.com" in link or "vm.tiktok.com" in link:
                            direct_video_url = link
                        elif "@" in link:
                            clean_channel = link.split("?")[0]
                            if clean_channel not in user_channels:
                                user_channels.append(clean_channel)
                                updated = True
                                print(f"➕ تم إضافة صفحة مخصصة جديدة: {clean_channel}")

            if updated:
                save_json(USER_CHANNELS_FILE, user_channels)

    except Exception as e:
        print(f"⚠️ خطأ أثناء قراءة الواتساب: {e}")

    return direct_video_url

def send_whatsapp_message(text):
    id_instance = os.environ.get("GREEN_ID_INSTANCE")
    api_token = os.environ.get("GREEN_API_TOKEN")

    if not id_instance or not api_token:
        return

    url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
    payload = {"chatId": MY_PHONE_NUMBER, "message": text}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"❌ خطأ إرسال الواتساب: {e}")

# ==========================================
# 🖼️ دمج العلامة المائية (اللوجو)
# ==========================================
def apply_logo_watermark(input_video_path, logo_path="logo.png"):
    if not os.path.exists(logo_path):
        print(f"ℹ️ لم يتم العثور على اللوجو ({logo_path}).")
        return input_video_path

    output_video_path = f"{OUTPUT_DIR}/watermarked_{random.randint(1000,9999)}.mp4"
    print("🎨 جاري وضع اللوجو...")
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', input_video_path,
        '-i', logo_path,
        '-filter_complex', '[1:v]scale=120:-1[logo];[0:v][logo]overlay=W-w-20:20',
        '-c:a', 'copy',
        output_video_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_video_path
    except Exception as e:
        print(f"⚠️ فشل إضافة اللوجو: {e}")
        return input_video_path

# ==========================================
# 📥 تنزيل الفيديو بدون تكرار
# ==========================================
def download_video(custom_video_url=None):
    posted_history = load_json(POSTED_HISTORY_FILE, [])

    if custom_video_url:
        print(f"📥 جاري معالجة فيديو مخصص من الواتساب: {custom_video_url}")
        ydl_opts = {'outtmpl': f'{OUTPUT_DIR}/downloaded_raw_%(id)s.%(ext)s', 'format': 'mp4/bestvideo+bestaudio/best', 'overwrites': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(custom_video_url, download=True)
            video_id = info.get('id')
            if video_id not in posted_history:
                downloaded_files = glob.glob(f"{OUTPUT_DIR}/downloaded_raw_*")
                if downloaded_files:
                    return downloaded_files[0], info.get('title', 'فيديو جديد'), video_id
            else:
                print("⚠️ هذا الفيديو تم نشره سابقاً!")

    user_channels = load_json(USER_CHANNELS_FILE, [])
    remove_count = len(user_channels) * 10
    remaining_defaults = DEFAULT_TARGET_CHANNELS[remove_count:] if remove_count < len(DEFAULT_TARGET_CHANNELS) else []
    active_pool = user_channels + remaining_defaults
    if not active_pool:
        active_pool = user_channels

    print(f"📊 القنوات النشطة: {len(active_pool)} (صفحاتك: {len(user_channels)})")

    for attempt in range(15):
        selected_channel = random.choice(active_pool)
        random_video_index = random.randint(1, 15)
        ydl_opts = {
            'outtmpl': f'{OUTPUT_DIR}/downloaded_raw_%(id)s.%(ext)s',
            'playlist_items': str(random_video_index),
            'format': 'mp4/bestvideo+bestaudio/best',
            'match_filter': yt_dlp.utils.match_filter_func('duration <= 60'),
            'overwrites': True,
            'quiet': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(selected_channel, download=False)
                entries = info.get('entries', [])
                if entries:
                    video_data = entries[0]
                    vid_id = video_data.get('id')
                    if vid_id not in posted_history:
                        ydl.download([video_data.get('webpage_url', selected_channel)])
                        downloaded_files = glob.glob(f"{OUTPUT_DIR}/downloaded_raw_*")
                        if downloaded_files:
                            return downloaded_files[0], video_data.get('title', 'فيديو جديد'), vid_id
                    else:
                        print(f"⏭️ تخطي فيديو مكرر (ID: {vid_id})")
        except Exception as e:
            print(f"⚠️ خطأ أثناء التنزيل: {e}")

    raise Exception("❌ لم يتم العثور على أي فيديو جديد غير مكرر.")

# ==========================================
# 📤 الرفع على قنوات يوتيوب
# ==========================================
def upload_to_youtube(video_path, title):
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    channels = []
    if os.environ.get("YOUTUBE_REFRESH_TOKEN"):
        channels.append(("اليوتيوب 1 🔴", os.environ.get("YOUTUBE_REFRESH_TOKEN")))
    if os.environ.get("YOUTUBE_REFRESH_TOKEN_2"):
        channels.append(("اليوتيوب 2 🔵", os.environ.get("YOUTUBE_REFRESH_TOKEN_2")))

    results = []
    full_title = f"{title[:75]} #Shorts"

    for ch_name, refresh_token in channels:
        print(f"🚀 جاري الرفع إلى {ch_name}...")
        try:
            creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret)
            youtube = build("youtube", "v3", credentials=creds)
            body = {"snippet": {"title": full_title, "description": f"{title}\n\n#Shorts #Viral", "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
            req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            res = None
            while res is None:
                _, res = req.next_chunk()

            yt_link = f"https://youtube.com/shorts/{res.get('id')}"
            print(f"✅ تم الرفع بنجاح على {ch_name}: {yt_link}")
            results.append(f"{ch_name}: {yt_link}")
        except Exception as e:
            print(f"❌ فشل الرفع على {ch_name}: {e}")
            results.append(f"{ch_name}: فشل الرفع ({e})")
    return results

# ==========================================
# 🟣 الرفع على انستجرام Reels (باستخدام INSTAGRAM_SESSION)
# ==========================================
def upload_to_instagram(video_path, caption):
    session_data = os.environ.get("INSTAGRAM_SESSION")
    if not session_data:
        print("⚠️ لم يتم العثور على INSTAGRAM_SESSION في GitHub Secrets.")
        return "انستجرام Reels 🟣: غير متوفرة بيانات الجلسة (INSTAGRAM_SESSION)"

    print("🚀 جاري الرفع إلى انستجرام Reels باستخدام Session...")
    try:
        cl = Client()
        cl.set_user_agent("Instagram 315.0.0.33.109 Android (33/13; 480dpi; 1080x2269; Xiaomi; POCO F3; alioth; qcom; en_US; 560877903)")

        # تحويل نصوص السشن من GitHub Secret إلى Dictionary
        session_dict = json.loads(session_data)
        cl.set_settings(session_dict)

        clean_caption = f"{caption[:1000]}\n\n#Reels #Shorts #Viral #Trending"
        media = cl.clip_upload(video_path, caption=clean_caption)
        print(f"✅ تم الرفع على انستجرام Reels بنجاح! ID: {media.pk}")
        return "انستجرام Reels 🟣: تم النشر بنجاح!"
    except Exception as e:
        print(f"❌ فشل الرفع على انستجرام: {e}")
        return f"انستجرام Reels 🟣: فشل الرفع ({str(e)[:80]})"

# ==========================================
# 🚀 التشغيل الرئيسي
# ==========================================
def main():
    ensure_directories()
    try:
        direct_video_url = process_whatsapp_incoming()
        raw_video_path, title, video_id = download_video(custom_video_url=direct_video_url)
        final_video_path = apply_logo_watermark(raw_video_path, logo_path="logo.png")

        # الرفع لكل من يوتيوب وانستجرام
        yt_results = upload_to_youtube(final_video_path, title)
        ig_result = upload_to_instagram(final_video_path, title)

        # حفظ سجل منع التكرار
        posted_history = load_json(POSTED_HISTORY_FILE, [])
        if video_id and video_id not in posted_history:
            posted_history.append(video_id)
            save_json(POSTED_HISTORY_FILE, posted_history)

        # تقرير الواتساب
        all_reports = yt_results + [ig_result]
        report_text = "\n".join(all_reports)
        msg = f"🎉 *تم نشر فيديو Shorts/Reels جديد!*\n\n📝 *العنوان:* {title}\n\n📊 *الحالة:*\n{report_text}"
        send_whatsapp_message(msg)

        # تنظيف
        for file in glob.glob(f"{OUTPUT_DIR}/*"):
            try:
                os.remove(file)
            except Exception:
                pass

    except Exception as e:
        error_msg = f"❌ *حدث خطأ أثناء أتمتة النشر:*\n{str(e)}"
        print(error_msg)
        send_whatsapp_message(error_msg)
        raise e

if __name__ == "__main__":
    main()
