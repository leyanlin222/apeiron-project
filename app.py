import streamlit as st
import base64
import json
import requests
import random
import time
import math
from openai import OpenAI
from PIL import Image, ImageStat

# --- 1. 基础配置 ---
st.set_page_config(page_title="APEIRON", page_icon="🔮", layout="centered")

# --- 辅助函数：生成随机星空数据 ---
def generate_stars(count):
    stars = []
    for _ in range(count):
        x = random.randint(0, 2000)
        y = random.randint(0, 2000)
        opacity = random.random()
        stars.append(f"{x}px {y}px 0 rgba(255, 255, 255, {opacity})")
    return ", ".join(stars)

# --- 辅助函数：生成 LUMINE 字母流星 (保留优化后的平衡版) ---
def generate_lumine_stars(count):
    base_chars = list("LUMINE")
    num_sets = math.ceil(count / len(base_chars))
    char_pool = base_chars * num_sets
    random.shuffle(char_pool)
    selected_chars = char_pool[:count]

    elements = []
    for char in selected_chars:
        left = random.randint(0, 100)
        top = random.randint(0, 2000)
        opacity = random.uniform(0.1, 0.4)
        size = random.randint(5, 8) # 保持微小尺寸
        element = f'<div style="position: absolute; left: {left}vw; top: {top}px; color: rgba(255,255,255,{opacity}); font-size: {size}px; font-weight: 200; user-select: none;">{char}</div>'
        elements.append(element)
    return "".join(elements)

# 生成星空
stars_small = generate_stars(700)
stars_medium = generate_stars(200)
stars_large = generate_stars(100)
lumine_stars_html = generate_lumine_stars(24)

# --- CSS 视觉环境 ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400&display=swap');
    
    .stApp {{ background: transparent !important; }}
    header, footer {{ visibility: hidden !important; }}

    /* --- 银河背景 --- */
    .galaxy-bg {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: radial-gradient(ellipse at bottom, #1B2735 0%, #090A0F 100%);
        z-index: -100; overflow: hidden;
    }}
    .star-layer {{ position: absolute; top: 0; left: 0; width: 1px; height: 1px; background: transparent; z-index: -99; }}
    .lumine-layer {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -98; animation: starMove 130s linear infinite; }}
    
    .stars-1 {{ box-shadow: {stars_small}; animation: starMove 100s linear infinite; }}
    .stars-2 {{ box-shadow: {stars_medium}; width: 2px; height: 2px; animation: starMove 150s linear infinite; }}
    .stars-3 {{ box-shadow: {stars_large}; width: 3px; height: 3px; animation: starMove 200s linear infinite; }}

    @keyframes starMove {{ from {{ transform: translateY(0px); }} to {{ transform: translateY(-2000px); }} }}

    /* --- 通用样式 --- */
    h1, h2, h3, p, div, span, label {{ color: #ffffff !important; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.5) !important; backdrop-filter: blur(10px); border-right: 1px solid rgba(255,255,255,0.1); }}
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{ background-color: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; color: #fff !important; }}
    
    /* 上传框 */
    [data-testid="stFileUploader"] {{ margin-top: 10px; }}
    [data-testid="stFileUploader"] section {{ background-color: rgba(255, 255, 255, 0.1) !important; border: 1px dashed rgba(255, 255, 255, 0.4) !important; border-radius: 12px; padding: 30px; transition: all 0.3s; }}
    [data-testid="stFileUploader"] section:hover {{ background-color: rgba(255, 255, 255, 0.2) !important; border-color: #fff !important; }}
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] label {{ color: rgba(255, 255, 255, 0.9) !important; }}
    [data-testid="stFileUploader"] svg {{ filter: brightness(0) invert(1) !important; opacity: 0.8; }}
    [data-testid="stFileUploader"] button {{ display: none; }}

    /* 标题 APEIRON (无署名) */
    h2 {{
        text-align: center; font-weight: 200 !important; font-size: 3.5rem !important;
        letter-spacing: 14px !important; text-shadow: 0 0 10px rgba(255,255,255,0.8), 0 0 30px rgba(255,255,255,0.3);
        margin-bottom: 40px; margin-top: 20px; text-transform: uppercase;
    }}

    /* 球体动画 */
    .blob-wrapper {{ display: flex; justify-content: center; align-items: center; height: 350px; width: 100%; position: relative; }}
    .blob {{
        width: 220px; height: 220px; background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: inset 0 0 30px rgba(255,255,255,0.05), 0 0 20px rgba(255,255,255,0.05);
        backdrop-filter: blur(12px); z-index: 1; border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; transition: all 0.5s ease;
    }}
    .blob.idle {{ animation: liquid-morph 12s ease-in-out infinite; }}
    @keyframes liquid-morph {{
        0% {{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; transform: rotate(0deg) scale(1); }}
        33% {{ border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; transform: rotate(120deg) scale(1.1, 0.9); }}
        66% {{ border-radius: 70% 30% 30% 70% / 60% 40% 60% 40%; transform: rotate(240deg) scale(0.9, 1.1); }}
        100% {{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; transform: rotate(360deg) scale(1); }}
    }}
    .blob.processing {{
        width: 150px; height: 150px; background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.8), rgba(118,75,162,0.4));
        box-shadow: 0 0 50px rgba(118, 75, 162, 0.8); animation: chaos-morph 0.6s linear infinite;
    }}
    @keyframes chaos-morph {{
        0% {{ border-radius: 50%; transform: scale(1); }}
        25% {{ border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; }}
        50% {{ border-radius: 70% 30% 30% 70% / 70% 70% 30% 30%; transform: scale(0.9); }}
        75% {{ border-radius: 40% 60% 60% 40% / 60% 40% 40% 60%; }}
        100% {{ border-radius: 50%; transform: scale(1); }}
    }}
</style>

<div class="galaxy-bg">
    <div class="star-layer stars-1"></div>
    <div class="star-layer stars-2"></div>
    <div class="star-layer stars-3"></div>
    <div class="lumine-layer">{lumine_stars_html}</div>
</div>
""", unsafe_allow_html=True)

# --- 2. API 配置 ---
api_key_default = ""
loaded_from_secrets = False
try:
    if "ALIYUN_KEY" in st.secrets:
        api_key_default = st.secrets["ALIYUN_KEY"]
        loaded_from_secrets = True
except: pass

if not loaded_from_secrets and "api_key_input" in st.session_state:
    api_key_default = st.session_state.api_key_input

st.sidebar.markdown("### ⚙️ SYSTEM")
if not loaded_from_secrets:
    aliyun_key = st.sidebar.text_input("API Key", value=api_key_default, type="password")
    if aliyun_key: st.session_state.api_key_input = aliyun_key
else:
    aliyun_key = api_key_default

layout_style = st.sidebar.selectbox("Composition", ("Stacked (Default)", "Asymmetric", "Diagonal", "Grouped"))
client = None
if aliyun_key:
    client = OpenAI(api_key=aliyun_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

# --- 3. 核心逻辑 (恢复原始音乐逻辑) ---
def search_music_from_itunes(query, style_category):
    base_url = "https://itunes.apple.com/search"
    clean_query = query.replace('，', ',').replace('、', ' ').replace('/', ' ').split(',')[0].strip()
    search_term = clean_query
    
    if style_category == "Traditional":
        if "Chinese" not in search_term: search_term = f"Chinese Traditional {clean_query}"
    elif style_category == "Industrial": search_term = f"{clean_query} Cinematic"
    elif style_category == "Sport": search_term = f"{clean_query} Workout Phonk"
    elif style_category in ["LightFood", "RichFood", "Art", "Healing"]:
        if "Instrumental" not in search_term and "Piano" not in search_term and "Guitar" not in search_term:
             search_term = f"{search_term} Instrumental"
        if style_category == "LightFood": search_term = f"{search_term} Relaxing"
        elif style_category == "Healing": 
            if "Guitar" in search_term: search_term = "Guitar Lullaby Instrumental"
            else: search_term = "Relaxing Piano Music"
    elif style_category == "Urban": search_term = f"{clean_query} Chill Lofi"
    elif style_category == "Cyber": search_term = f"{clean_query} Phonk"
    if len(search_term.split()) > 5: search_term = " ".join(search_term.split()[-3:])
    
    try:
        response = requests.get(base_url, params={"term": search_term, "media": "music", "entity": "song", "limit": 40}, timeout=10)
        data = response.json()
        if data.get('resultCount', 0) > 0:
            results = data['results']
            # 只做基础过滤
            safe_list = [r for r in results if "instrumental" in r.get('trackName','').lower() or "piano" in r.get('trackName','').lower() or "lofi" in r.get('trackName','').lower()]
            if safe_list: results = safe_list
            final_pool = [r for r in results if r.get('artworkUrl100')]
            if not final_pool: final_pool = results
            song = random.choice(final_pool)
            return {"title": song.get('trackName'), "artist": song.get('artistName'), "audio_url": song.get('previewUrl'), "found": True}
        else: return {"found": False}
    except Exception as e: return {"found": False, "error": str(e)}

def calculate_brightness(image):
    return ImageStat.Stat(image.convert('L')).mean[0]

# --- 4. 主界面 ---
st.markdown("<h2 style='text-align: center;'>APEIRON</h2>", unsafe_allow_html=True)
stage = st.empty()
uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if not uploaded_file:
    stage.markdown("""
        <div class="blob-wrapper"><div class="blob idle"></div></div>
        <div style="text-align:center; color:rgba(255,255,255,0.7); font-size:12px; margin-top:-30px; letter-spacing:1px;">WAITING FOR VISUAL INPUT...</div>
    """, unsafe_allow_html=True)

elif uploaded_file and client:
    stage.markdown("""
        <div class="blob-wrapper"><div class="blob processing"></div></div>
        <div style="text-align:center; color:#fff; font-size:14px; margin-top:-30px; letter-spacing:2px; text-shadow:0 0 10px #fff;">PROCESSING...</div>
    """, unsafe_allow_html=True)
    
    time.sleep(0.5)
    
    try:
        # --- 恢复原始图片读取 (不压缩) ---
        image = Image.open(uploaded_file)
        img_w, img_h = image.size
        display_height = int(700 * (img_h / img_w))
        brightness_val = calculate_brightness(image)
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')

        # --- 恢复原始 Prompt (包含 Sport/Happy 等) ---
        prompt_text = """
        You are a minimalist aesthetic director. Analyze image. Return JSON.
        【1. Style】Traditional(Guzheng), Sport(Phonk), Happy(Pop), Industrial(Cinematic), Cyber(Phonk), Art(Piano), Healing(Lullaby), LightFood(Guitar), RichFood(Jazz), Urban(Lofi), Dim(Jazz).
        【2. Layout】"left", "right", "top", "bottom", "center" (Find negative space).
        【3. Copy】Traditional:Chinese. Others:English (Poetic, 3 lines).
        JSON format: {"style_category": "", "layout_position": "", "search_query": "", "lyrics": []}
        """

        response = client.chat.completions.create(
            model="qwen-vl-max",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt_text}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
        )
        
        content = response.choices[0].message.content.replace("```json", "").replace("```", "")
        ai_result = json.loads(content)
        
        style_cat = ai_result.get("style_category", "Lofi")
        search_query = ai_result.get("search_query", "Lofi")
        layout_pos = ai_result.get("layout_position", "bottom").lower()
        lyrics_list = ai_result.get("lyrics", [])

        # 视觉混合模式
        is_food = style_cat in ["LightFood", "RichFood"]
        if is_food: op_high, op_low, blend_mode = "0.3)", "0.05)", "normal"
        elif brightness_val < 70: op_high, op_low, blend_mode = "0.5)", "0.15)", "multiply"
        elif brightness_val > 190: op_high, op_low, blend_mode = "0.35)", "0.05)", "normal"
        else: op_high, op_low, blend_mode = "0.4)", "0.1)", "normal"

        song_data = search_music_from_itunes(search_query, style_cat)
        if not song_data["found"]: song_data = search_music_from_itunes("Piano", style_cat)
        final_audio = song_data.get("audio_url")

        font_imports = """
        @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Pinyon+Script&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap');
        """
        
        styles_map = {
            "Urban": {"font": "'Dancing Script', cursive", "color": "#fff", "shadow": "0 2px 5px rgba(0,0,0,0.8)", "writing": "horizontal-tb", "overlay_base": "rgba(10, 10, 10, "},
            "Dim": {"font": "'Pinyon Script', cursive", "color": "#e0d0c0", "shadow": "0 2px 4px #000", "writing": "horizontal-tb", "overlay_base": "rgba(0, 0, 0, "},
            "Art": {"font": "'Pinyon Script', cursive", "color": "#fdfbf7", "shadow": "0 2px 10px rgba(0,0,0,1)", "writing": "horizontal-tb", "overlay_base": "rgba(30, 30, 30, "},
            "Healing": {"font": "'Dancing Script', cursive", "color": "#ffffff", "shadow": "0 2px 8px rgba(0,0,0,0.8)", "writing": "horizontal-tb", "overlay_base": "rgba(60, 50, 40, "},
            "LightFood": {"font": "'Dancing Script', cursive", "color": "#fff", "shadow": "0 1px 5px rgba(0,0,0,0.7)", "writing": "horizontal-tb", "overlay_base": "rgba(0, 0, 0, "},
            "RichFood": {"font": "'Dancing Script', cursive", "color": "#fff", "shadow": "0 1px 5px rgba(0,0,0,0.7)", "writing": "horizontal-tb", "overlay_base": "rgba(0, 0, 0, "},
            "Traditional": {"font": "'Ma Shan Zheng', cursive", "color": "#f0e6d2", "shadow": "2px 2px 4px rgba(0,0,0,0.9)", "writing": "vertical-rl", "overlay_base": "rgba(40, 20, 10, "},
            "Sport": {"font": "'Permanent Marker', cursive", "color": "#ccff00", "shadow": "2px 2px 0px #000", "writing": "horizontal-tb", "overlay_base": "rgba(20, 20, 25, "},
            "Happy": {"font": "'Permanent Marker', cursive", "color": "#fff", "shadow": "2px 2px 0px #000, 4px 4px 0px #ff0055", "writing": "horizontal-tb", "overlay_base": "rgba(20, 0, 10, "},
            "Cyber": {"font": "'Orbitron', sans-serif", "color": "#00ffea", "shadow": "0 0 5px #000, 0 0 10px #00ffea", "writing": "horizontal-tb", "overlay_base": "rgba(5, 0, 20, "},
            "Industrial": {"font": "'Share Tech Mono', monospace", "color": "#ffcc00", "shadow": "1px 1px 0px #000, 2px 2px 0px #000", "writing": "horizontal-tb", "overlay_base": "rgba(10, 10, 15, "},
        }
        config = styles_map.get(style_cat, styles_map.get("Urban"))
        base_str = config["overlay_base"]

        if layout_pos == "left":
            box_css = "top: 50%; left: 10%; transform: translateY(-50%); width: 50%;"
            overlay_css = f"linear-gradient(to right, {base_str}{op_high} 0%, {base_str}{op_low} 60%, transparent 100%)"
            box_align = "flex-start"
        elif layout_pos == "right":
            box_css = "top: 50%; right: 5%; transform: translateY(-50%); width: 50%;"
            overlay_css = f"linear-gradient(to left, {base_str}{op_high} 0%, {base_str}{op_low} 60%, transparent 100%)"
            box_align = "flex-end"
        elif layout_pos == "top":
            box_css = "top: 5%; left: 0; width: 100%;"
            overlay_css = f"linear-gradient(to bottom, {base_str}{op_high} 0%, {base_str}{op_low} 50%, transparent 100%)"
            box_align = "center"
        elif layout_pos == "center":
            box_css = "top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%;"
            center_op = "0.25)" if is_food or brightness_val > 150 else "0.4)"
            overlay_css = f"{base_str}{center_op}"
            box_align = "center"
        else: # bottom
            box_css = "bottom: 10%; left: 0; width: 100%;"
            overlay_css = f"linear-gradient(to top, {base_str}{op_high} 0%, {base_str}{op_low} 50%, transparent 100%)"
            box_align = "center"

        lyric_line_css = "margin: 5px 0; text-align: center;"
        lyrics_wrapper_css = f"display: flex; flex-direction: column; align-items: {box_align};"

        if layout_style == "Asymmetric":
            formatted_lyrics = [
                f'<div class="lyric-line" style="text-align: left; margin-left: 0;">{lyrics_list[0]}</div>',
                f'<div class="lyric-line" style="text-align: center; margin: 15px 0;">{lyrics_list[1]}</div>' if len(lyrics_list) > 1 else "",
                f'<div class="lyric-line" style="text-align: right; margin-right: 0;">{lyrics_list[2]}</div>' if len(lyrics_list) > 2 else ""
            ]
            lyrics_html = "".join(formatted_lyrics)
            lyrics_wrapper_css = "display: flex; flex-direction: column; width: 100%;"
        elif layout_style == "Diagonal":
            formatted_lyrics = []
            for i, line in enumerate(lyrics_list):
                formatted_lyrics.append(f'<div class="lyric-line" style="text-align: left; margin-left: {i * 40}px;">{line}</div>')
            lyrics_html = "".join(formatted_lyrics)
        elif layout_style == "Grouped":
            formatted_lyrics = []
            if len(lyrics_list) > 0:
                formatted_lyrics.append(f'<div><div class="lyric-line">{lyrics_list[0]}</div></div>')
                if len(lyrics_list) > 1:
                    formatted_lyrics.append(f'<div style="margin-top:25px;"><div class="lyric-line">{lyrics_list[-1]}</div></div>')
            lyrics_html = "".join(formatted_lyrics)
        else:
            lyrics_html = "".join([f'<div class="lyric-line">{line}</div>' for line in lyrics_list])

        final_html = f"""
        <style>
            {font_imports}
            body {{ margin: 0; overflow: hidden; background-color: transparent; }}
            .poster-container {{
                position: relative; width: 100%; height: auto;
                border-radius: 44px; overflow: hidden;
                background-color: rgba(0,0,0,0.5); backdrop-filter: blur(20px);
                border: 4px solid rgba(255, 255, 255, 0.15);
                box-shadow: 0 30px 80px rgba(0,0,0,0.8);
                animation: glass-pop 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
            }}
            @keyframes glass-pop {{ from {{ transform: scale(0.9) translateY(20px); opacity: 0; }} to {{ transform: scale(1) translateY(0); opacity: 1; }} }}
            .bg-image {{ display: block; width: 100%; height: auto; pointer-events: none; }}
            .overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: {overlay_css}; mix-blend-mode: {blend_mode}; pointer-events: none; z-index: 1; }}
            .lyrics-box {{ position: absolute; {box_css} z-index: 999; cursor: grab; {lyrics_wrapper_css} }}
            .vertical-wrapper {{ writing-mode: vertical-rl; text-orientation: upright; letter-spacing: 4px; height: 350px; display: flex; gap: 15px; align-items: center; }}
            .lyric-line {{ 
                font-family: {config['font']}; font-size: {'36px' if 'Script' in config['font'] else '28px'}; 
                color: {config['color']}; text-shadow: 0 2px 4px rgba(0,0,0,0.9);
                font-weight: 400; line-height: 1.5; padding: 0 10px; {lyric_line_css}
            }}
        </style>
        
        <div class="poster-container" id="container">
            <img src="data:image/jpeg;base64,{base64_image}" class="bg-image">
            <div class="overlay"></div>
            <div class="lyrics-box" id="draggable">
                {f'<div class="vertical-wrapper">{lyrics_html}</div>' if config["writing"] == 'vertical-rl' else lyrics_html}
            </div>
        </div>
        
        <script>
            const dragItem = document.querySelector("#draggable");
            const container = document.querySelector("#container");
            let active = false;
            let currentX; let currentY; let initialX; let initialY; let xOffset = 0; let yOffset = 0;
            function dragStart(e) {{
                if (e.type === "touchstart") {{ initialX = e.touches[0].clientX - xOffset; initialY = e.touches[0].clientY - yOffset; }} 
                else {{ initialX = e.clientX - xOffset; initialY = e.clientY - yOffset; }}
                if (dragItem.contains(e.target)) {{ active = true; }}
            }}
            function dragEnd(e) {{ initialX = currentX; initialY = currentY; active = false; }}
            function drag(e) {{
                if (active) {{
                    e.preventDefault();
                    if (e.type === "touchmove") {{ currentX = e.touches[0].clientX - initialX; currentY = e.touches[0].clientY - initialY; }} 
                    else {{ currentX = e.clientX - initialX; currentY = e.clientY - initialY; }}
                    xOffset = currentX; yOffset = currentY;
                    setTranslate(currentX, currentY, dragItem);
                }}
            }}
            function setTranslate(xPos, yPos, el) {{ el.style.transform = "translate3d(" + xPos + "px, " + yPos + "px, 0)"; }}
            dragItem.addEventListener("touchstart", dragStart, false);
            dragItem.addEventListener("mousedown", dragStart, false);
            window.addEventListener("touchend", dragEnd, false);
            window.addEventListener("mouseup", dragEnd, false);
            window.addEventListener("touchmove", drag, false);
            window.addEventListener("mousemove", drag, false);
            document.body.addEventListener("mouseleave", dragEnd, false);
        </script>
        """

        stage.empty()
        if final_audio:
            st.audio(final_audio, format="audio/mp4", start_time=0)
        else:
            st.warning("Silent Mode (Music not found)")
            
        st.components.v1.html(final_html, height=display_height + 40)

    except Exception as e:
        st.error(f"Error: {e}")

elif not client:
    st.info("Input API Key in Sidebar")
