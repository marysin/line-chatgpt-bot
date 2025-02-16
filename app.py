import os
import re
import json
import requests
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from googletrans import Translator  # 引入 Google 翻譯 API
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 初始化 Flask
app = Flask(__name__)

# 初始化 LINE Bot
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化 Google 翻譯
translator = Translator()

# 設定儲存用戶標籤的檔案
USER_LABELS_FILE = "user_labels.json"

# 讀取 `pokemon_data.json`
try:
    with open("pokemon_data.json", "r", encoding="utf-8") as f:
        pokemon_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("⚠️ 無法讀取 `pokemon_data.json`，將使用原始寶可夢名稱")
    pokemon_data = {}

# 讀取 `user_labels.json`
def load_user_labels():
    try:
        with open(USER_LABELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_labels(user_labels):
    with open(USER_LABELS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_labels, f, ensure_ascii=False, indent=4)

# 初始化使用者標籤
user_labels = load_user_labels()

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot 正在運行..."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200  # 確保 LINE 正確接收 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 🔹 **檢查是否是設定名稱指令**
    if user_message.startswith("設定名稱"):
        new_label = user_message.replace("設定名稱", "").strip()
        if new_label:
            user_labels[user_id] = new_label  # **為該用戶設定標籤**
            save_user_labels(user_labels)  # **立即保存到 JSON 檔案**
            reply_text = f"✅ 你的標籤名稱已更新為：{new_label}"
        else:
            reply_text = "⚠️ 設定失敗，請輸入 `設定名稱 + 你想要的名稱`"
    else:
        # 🔹 **格式化寶可夢資訊**
        reply_text = format_pokemon_data(user_message, user_id)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
    
def country_to_flag(country_code):
    """將 `country_code` 轉換成對應國旗 Emoji"""
    if not country_code or country_code == "unknown":
        return "🏳️"  # 無法識別時使用白旗

    # **ISO 3166-1 轉換國旗**
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())


def format_pokemon_data(text, user_id):
    # **解析國家代碼，獲取對應國旗**
    flag_match = re.search(r":flag_(\w+):", text)
    country_code = flag_match.group(1).lower() if flag_match else "unknown"
    flag = country_to_flag(country_code)  # 🔹 轉換國家代碼為國旗

    # **檢查是否有 `shiny` 圖示**
    shiny_match = re.search(r"<a:shiny:\d+>", text)
    shiny_symbol = "✨" if shiny_match else ""

    # **提取寶可夢名稱（英文 & 轉換成中文）**
    name_match = re.search(r"\*\*\*(.*?)\*\*\*", text)
    name_en = name_match.group(1) if name_match else "未知寶可夢"
    name_cn = pokemon_data.get(name_en, name_en)  # 找不到則保留原名

    # **提取性別**
    gender = "♀" if "♀" in text else "♂"

    # **提取 IV**
    iv_match = re.search(r"IV(\d+)", text)
    iv = f"💯" if iv_match and iv_match.group(1) == "100" else f"IV {iv_match.group(1)}"

    # **提取 CP & L 等級**
    cp_match = re.search(r"\*\*CP(\d+)\*\*", text)
    level_match = re.search(r"\*\*L(\d+)\*\*", text)
    cp = cp_match.group(1) if cp_match else "未知"
    level = level_match.group(1) if level_match else "未知"

    # **提取 DSP 時間**
    dsp_match = re.search(r"DSP in (\d+)m", text)
    dsp = f"DSP:{dsp_match.group(1)}m" if dsp_match else "無 DSP 時間"

    # **提取體型與身高資訊**
    size_match = re.findall(r"\b(WXXL|WXXS|WXL|WXS|HXXL|HXXS|HXL|HXS)\b", text)
    size_info = " ".join(size_match) if size_match else ""

    # **提取地點名稱**
    location_match = re.findall(r"-\s\*?([\w\s,]+)\*?\s*-", text)
    location_name = location_match[0].strip() if location_match else "未知地點"

    # **嘗試翻譯地點**
    translated_city = translate_city_google(location_name)

    # **處理座標**
    coords_match = re.search(r"(-?\d+\.\d+),\s*(-?\d+\.\d+)", text)
    if coords_match:
        lat = round(float(coords_match.group(1)), 4)
        lng = round(float(coords_match.group(2)), 4)
        coords = f"{lat}, {lng}"
    else:
        coords = "未知座標"

    # **取得該用戶的 `custom_label`**
    custom_label = user_labels.get(user_id, "🔧工具人⚙️")

    # **組合輸出**
    formatted_text = f"""
{flag} {shiny_symbol}{name_cn} {name_en} {gender} {iv} {size_info}
L {level} / CP {cp} {dsp}
{custom_label} {translated_city}
📍 {coords}
""".strip()

    return formatted_text


def translate_city_google(city_en):
    """ 使用 Google 翻譯 API 將城市名稱轉換成中文 """
    try:
        # 如果地點包含 `,`，則拆分成 `城市` & `國家`
        if "," in city_en:
            city, country = city_en.split(",", 1)
            city = city.strip()
            country = country.strip()

            # 只翻譯 `城市`，保留 `國家`
            translated_city = translator.translate(city, src="en", dest="zh-tw").text
            return f"{translated_city}，{country}"
        else:
            # 直接翻譯整個地點名稱
            return translator.translate(city_en, src="en", dest="zh-tw").text
    except Exception as e:
        print(f"⚠️ 翻譯錯誤: {e}")
        return city_en  # 翻譯失敗則返回原始名稱

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
