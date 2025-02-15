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

# 讀取寶可夢名稱對應表
with open("pokemon_data.json", "r", encoding="utf-8") as f:
    pokemon_data = json.load(f)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot 正在運行..."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK"

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 呼叫資料整理函數
    formatted_message = format_pokemon_data(user_message)

    # 回應整理後的內容
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=formatted_message)
    )

def format_pokemon_data(text):
    # 提取國旗
    flag_match = re.search(r":flag_(\w+):", text)
    flag = f"🇺🇸" if flag_match else ""

    # 提取寶可夢名稱（英文 & 轉換成中文）
    name_match = re.search(r"\*\*\*(.*?)\*\*\*", text)
    name_en = name_match.group(1) if name_match else "未知寶可夢"
    name_cn = pokemon_data.get(name_en, name_en)  # 找不到則保留原名

    # 提取性別
    gender = "♀" if "♀" in text else "♂"

    # 提取 IV
    iv_match = re.search(r"IV(\d+)", text)
    iv = f"💯" if iv_match and iv_match.group(1) == "100" else f"IV {iv_match.group(1)}"

    # 提取 CP & L 等級
    cp_match = re.search(r"\*\*CP(\d+)\*\*", text)
    level_match = re.search(r"\*\*L(\d+)\*\*", text)
    cp = cp_match.group(1) if cp_match else "未知"
    level = level_match.group(1) if level_match else "未知"

    # 提取 DSP 時間
    dsp_match = re.search(r"DSP in (\d+)m", text)
    dsp = f"DSP:{dsp_match.group(1)}m" if dsp_match else "無 DSP 時間"

    # 提取體型與身高資訊（WXXL, HXS）
    size_match = re.findall(r"\b(WXXL|WXXS|WXL|WXS|HXXL|HXXS|HXL|HXS)\b", text)
    size_info = " ".join(size_match) if size_match else ""

    # 提取地點（修正不匹配的格式）
    location_match = re.search(r"-\s([\w\s,]+)-", text)  # 匹配 `- 城市, 國家 -`
    location_name = location_match.group(1).strip() if location_match else "未知地點"

    print(f"原始地點: {location_name}")  # 🔥 Debug: 檢查是否成功提取地點

    # 🔹 使用 Google 翻譯 API 自動翻譯城市名稱
    translated_city = translate_city_google(location_name)
    
    print(f"翻譯前: {location_name}，翻譯後: {translated_city}")  # 🔥 Debug: 檢查翻譯結果

    # 整理輸出格式
    formatted_text = f"""
{flag} ✨{name_cn} {name_en} {gender} {iv} {size_info}
L {level} / CP {cp} {dsp}
🔧工具人⚙️{translated_city}
    """.strip()

    return formatted_text

def translate_city_google(city_en):
    """ 使用 Google 翻譯將城市名稱轉換成中文 """
    translated = translator.translate(city_en, src="en", dest="zh-tw")
    return translated.text

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
