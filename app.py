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

    # 🔹 提取座標 `(39.915432, -75.137098)`
    coords_match = re.search(r"\((-?\d+\.\d+),\s*(-?\d+\.\d+)\)", text)
    if coords_match:
        lat = round(float(coords_match.group(1)), 4)  # 經度縮短到 4 位數
        lng = round(float(coords_match.group(2)), 4)  # 緯度縮短到 4 位數
        coords = f"{lat}, {lng}"
    else:
        coords = "未知座標"

    print(f"提取座標: {coords}")  # 🔥 Debug: 確保座標正確

    # 🔹 使用 Google 翻譯 API 自動翻譯城市名稱
    translated_city = translate_city_google(location_name)
    
    print(f"翻譯前: {location_name}，翻譯後: {translated_city}")  # 🔥 Debug: 檢查翻譯結果

    # 整理輸出格式
    formatted_text = f"""
{flag} ✨{name_cn} {name_en} {gender} {iv} {size_info}
L {level} / CP {cp} {dsp}
🔧工具人⚙️{translated_city}
📍 {coords}
    """.strip()

    return formatted_text
