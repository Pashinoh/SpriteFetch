import os
import io
import re
import time
import base64
import zipfile
import warnings
import logging
from urllib.parse import urljoin, urlparse, unquote

import requests
import cloudscraper
from bs4 import BeautifulSoup
import streamlit as st
from PIL import Image, ImageDraw

# ==========================================
# OPTIMIZATION: DISABLE ALL BACKGROUND LOGS
# ==========================================
os.environ["STREAMLIT_LOGGER_LEVEL"] = "error"
warnings.filterwarnings("ignore")
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('cloudscraper').setLevel(logging.CRITICAL)
logging.getLogger('streamlit').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context').setLevel(logging.CRITICAL)

# ==========================================
# DYNAMIC FAVICON GENERATOR (16x16 Pixel Art)
# ==========================================
favicon = Image.new('RGBA', (16, 16), (255, 255, 255, 0))
d = ImageDraw.Draw(favicon)
# Black Base Folder
d.rectangle([1, 2, 7, 3], fill='#000000')
d.rectangle([1, 4, 15, 14], fill='#000000')
# Yellow & Orange Accents
d.rectangle([2, 3, 6, 4], fill='#FFDE00')
d.rectangle([2, 5, 14, 13], fill='#FFAA00')
# White Sprite with Red Eyes
d.rectangle([4, 7, 12, 11], fill='#FFFFFF')
d.rectangle([5, 8, 7, 10], fill='#FF2400')
d.rectangle([9, 8, 11, 10], fill='#FF2400')

st.set_page_config(page_title="SpriteFetch", page_icon=favicon, layout="centered", initial_sidebar_state="collapsed")

# ==========================================
# SEO META TAGS INJECTION
# ==========================================
st.markdown("""
    <meta name="description" content="SpriteFetch - A neo-retro web asset ingestor & SVG compiler. Extract and download web graphics easily.">
    <meta name="keywords" content="SpriteFetch, asset extractor, web scraper, SVG compiler, image downloader, pixel art, retro tool">
    <meta name="author" content="SpriteFetch">
""", unsafe_allow_html=True)

# ==========================================
# CONFIGURATION & ENVIRONMENT
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

# Attempt to create downloads folder (safe for cloud deployment)
try:
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
except (PermissionError, OSError):
    # Fall back to temporary directory for cloud platforms
    DOWNLOAD_DIR = None

# STATE MACHINE INITIALIZATION
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'target_url' not in st.session_state:
    st.session_state.target_url = ""
if 'keyword' not in st.session_state:
    st.session_state.keyword = ""
if 'scraped_assets' not in st.session_state:
    st.session_state.scraped_assets = []
if 'selected_assets' not in st.session_state:
    st.session_state.selected_assets = []
if 'success_count' not in st.session_state:
    st.session_state.success_count = 0
if 'all_selected' not in st.session_state:
    st.session_state.all_selected = True
if 'output_format' not in st.session_state:
    st.session_state.output_format = "SVG"

# Dynamic Download Variables
if 'download_data' not in st.session_state:
    st.session_state.download_data = None
if 'download_filename' not in st.session_state:
    st.session_state.download_filename = ""
if 'download_mime' not in st.session_state:
    st.session_state.download_mime = ""

# ==========================================
# CORE SCRAPER LOGIC & BYPASS ENGINE
# ==========================================
def robust_fetch(url, timeout=15):
    """Multi-layered scraper to bypass Cloudflare and Datacenter IP blocks"""
    # Build a friendly header set; some hosts reject default python UA
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    # Try cloudscraper first (handles common Cloudflare protections)
    try:
        scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "desktop": True})
        res = scraper.get(url, headers=base_headers, timeout=timeout, allow_redirects=True)
        if res is not None and getattr(res, 'status_code', None) == 200:
            return res
        logging.getLogger('spritefetch').warning(f"robust_fetch: cloudscraper returned {getattr(res, 'status_code', None)} for {url}")
    except Exception as e:
        logging.getLogger('spritefetch').warning(f"robust_fetch: cloudscraper error for {url}: {e}")

    # Fallback: plain requests with a slightly different header set
    try:
        headers = base_headers.copy()
        # Add some headers that sometimes help with basic bot checks
        headers.update({"X-Requested-With": "XMLHttpRequest", "DNT": "1"})
        res = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if getattr(res, 'status_code', None) != 200:
            logging.getLogger('spritefetch').warning(f"robust_fetch: requests returned {getattr(res, 'status_code', None)} for {url}; headers used: {headers}")
        return res
    except Exception as e:
        logging.getLogger('spritefetch').error(f"robust_fetch: requests exception for {url}: {e}")
        class DummyResponse:
            status_code = 500
            text = str(e)
            content = b""
        return DummyResponse()

def convert_to_embedded_svg(img_bytes: bytes, original_format: str) -> bytes:
    """Wraps raster bytes into a scalable SVG vector container"""
    try:
        encoded_string = base64.b64encode(img_bytes).decode('utf-8')
        with Image.open(io.BytesIO(img_bytes)) as img:
            width, height = img.size
        
        mime_type = f"image/{original_format.lower().replace('jpg', 'jpeg')}"
        svg_template = (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
            f'  <image width="{width}" height="{height}" xlink:href="data:{mime_type};base64,{encoded_string}"/>\n'
            f'</svg>'
        )
        return svg_template.encode('utf-8')
    except Exception:
        return b""

def sanitize_filename(url: str, fallback_index: int) -> str:
    """Extracts and cleans the filename from a URL"""
    try:
        path = urlparse(url).path
        raw_name = os.path.basename(path)
        decoded_name = unquote(raw_name)
        name_without_ext = os.path.splitext(decoded_name)[0]
        if "?" in name_without_ext:
            name_without_ext = name_without_ext.split("?")[0]
        clean_name = re.sub(r'[\\/*?:"<>|]', "", name_without_ext).strip()
        return clean_name if len(clean_name) > 1 else f"sprite_{fallback_index}"
    except Exception:
        return f"sprite_{fallback_index}"

def extract_image_urls(soup: BeautifulSoup, target_url: str) -> list:
    """Finds all valid image sources in the DOM"""
    extracted_urls = set()
    tags_and_attrs = [
        ('img', ['src', 'data-src', 'data-lazy-src', 'srcset', 'data-src-fast', 'data-original']),
        ('source', ['srcset', 'src', 'data-srcset'])
    ]
    for tag_name, attrs in tags_and_attrs:
        for element in soup.find_all(tag_name):
            for attr in attrs:
                val = element.get(attr)
                if val:
                    if ',' in val:
                        val = val.split(',')[0].strip().split(' ')[0]
                    absolute_url = urljoin(target_url, val)
                    extracted_urls.add(absolute_url)
                    break
    valid_assets = []
    for url in extracted_urls:
        if "blank.gif" in url or url.startswith('data:') or not urlparse(url).path:
            continue
        if '/revision/' in url:  
            url = url.split('/revision/')[0]
        ext = os.path.splitext(urlparse(url).path)[1].lower().replace('.', '')
        if not ext:
            if 'png' in url.lower(): ext = 'png'
            elif 'jpg' in url.lower() or 'jpeg' in url.lower(): ext = 'jpg'
            elif 'webp' in url.lower(): ext = 'webp'
            else: ext = 'png'
        if ext in ['png', 'jpg', 'jpeg', 'webp']:
            valid_assets.append((url, ext))
    return valid_assets


# ==========================================
# PRESENTATION LAYER (CSS GLOBAL)
# ==========================================
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

if st.session_state.theme == 'light':
    bg_color = "#FAFAFA"
    dot_color = "#cccccc"
    text_color = "#000000"
    container_bg = "#FFFFFF"
    border_color = "#000000"
    shadow_color = "#000000"
    sub_text = "#555555"
    input_bg = "#FFFFFF"
    input_shadow = "#E0E0E0"
    secondary_btn_bg = "#FFFFFF"
    secondary_btn_hover = "#F0F0F0"
    placeholder_color = "0, 0, 0"
    img_bg = "#f1f1f1"
    toggle_icon = "☾"
    toggle_justify = "flex-end"
    toggle_pad = "padding-right: 8px;"
    toggle_thumb_pos = "left: 4px;"
    toggle_track_bg = "#CCCCCC"
    toggle_thumb_bg = "#000000"
else:
    bg_color = "#121212"
    dot_color = "#333333"
    text_color = "#FFFFFF"
    container_bg = "#1e1e1e"
    border_color = "#FFFFFF"
    shadow_color = "#FFFFFF"
    sub_text = "#AAAAAA"
    input_bg = "#2c2c2c"
    input_shadow = "#121212"
    secondary_btn_bg = "#2c2c2c"
    secondary_btn_hover = "#3d3d3d"
    placeholder_color = "255, 255, 255"
    img_bg = "#2c2c2c"
    toggle_icon = "☀"
    toggle_justify = "flex-start"
    toggle_pad = "padding-left: 8px;"
    toggle_thumb_pos = "left: 44px;"
    toggle_track_bg = "#000000"
    toggle_thumb_bg = "#FFFFFF"

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Silkscreen&family=VT323&display=swap');

        *, html, body, p, span, div, label, input, button, a, [data-testid="stToast"] {{
            font-family: 'VT323', monospace !important;
        }}

        /* Smooth Dark/Light Mode Transition */
        html, body, [data-testid="stAppViewContainer"], .block-container, div, p, span, label, h1, h2, h3, h4, h5, h6 {{
            transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease, background-image 0.4s ease;
        }}

        html, body, [data-testid="stAppViewContainer"] {{
            background-color: {bg_color} !important;
            background-image: radial-gradient({dot_color} 2px, transparent 2px) !important;
            background-size: 24px 24px !important;
            color: {text_color} !important;
        }}
        
        header[data-testid="stHeader"] {{ display: none !important; }}
        
        .block-container {{ 
            background-color: {container_bg} !important;
            border: 4px solid {border_color} !important;
            box-shadow: 10px 10px 0px {shadow_color} !important;
            padding: 2.5rem !important; 
            margin-top: 4rem !important; 
            margin-bottom: 4rem !important;
            max-width: 680px !important;
            border-radius: 0px !important;
            overflow: visible !important;
        }}
        
        .st-emotion-cache-1jicfl2, .st-emotion-cache-1104q3j {{ padding: 0px !important; }}
                @media (max-width: 768px) {{
            .block-container {{ 
                padding: 1.5rem !important; 
                margin-top: 1rem !important; 
                margin-bottom: 1rem !important;
                box-shadow: 6px 6px 0px {shadow_color} !important;
            }}
            .pixel-title {{ font-size: 2.2rem !important; }}
            .header-container {{ padding-bottom: 1rem; margin-bottom: 1rem; }}
            .stTextInput>div>div>input {{ height: 48px !important; font-size: 1.2rem !important; }}
            button[kind="primary"], button[kind="primaryFormSubmit"], 
            button[kind="secondary"], button[kind="secondaryFormSubmit"], 
            .stDownloadButton>button {{
                height: 48px !important;
                font-size: 1rem !important;
            }}
        }}
                .header-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 4px dashed {border_color};
            padding-bottom: 1.5rem;
        }}
        
        .pixel-title {{
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 2.8rem !important;
            color: {text_color};
            margin-top: 0.5rem;
            margin-bottom: 0px;
        }}
        
        .pixel-sub {{
            font-size: 1.5rem !important;
            color: {sub_text};
            line-height: 1.2;
            margin-top: 0.5rem;
        }}
        
        .stTextInput label p, .stSelectbox label p {{
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 0.95rem !important;
            color: {text_color} !important;
            margin-bottom: 0.5rem;
        }}
        
        /* -------------------------------------- */
        /* INPUT FIELDS & TEXT AREAS              */
        /* -------------------------------------- */
        div[data-baseweb="input"] {{
            background-color: transparent !important;
            border: none !important;
            overflow: visible !important;
        }}
        div[data-baseweb="input"]:focus-within {{
            box-shadow: none !important;
            border: none !important;
        }}
        .stTextInput>div>div>input {{
            font-size: 1.5rem !important;
            background-color: {input_bg} !important;
            border: 4px solid {border_color} !important;
            color: {text_color} !important;
            border-radius: 0px !important;
            padding: 10px 1rem !important;
            height: 56px !important;
            box-shadow: inset 4px 4px 0px {input_shadow};
            transition: all 0.1s ease;
            caret-color: {text_color} !important;
            caret-shape: block !important;
        }}
        
        .stTextInput>div>div>input::placeholder {{ color: rgba({placeholder_color}, 0.4) !important; }}
        .stTextInput>div>div>input:focus {{
            background-color: {input_bg} !important;
            color: {text_color} !important;
            border: 4px solid {border_color} !important;
            box-shadow: inset 4px 4px 0px {input_shadow} !important;
            outline: none !important;
        }}

        /* -------------------------------------- */
        /* SELECTBOX FIX (NO CLIPPING)            */
        /* -------------------------------------- */
        div[data-baseweb="select"] > div {{
            background-color: {input_bg} !important;
            border: 4px solid {border_color} !important;
            border-radius: 0px !important;
            box-shadow: inset 4px 4px 0px {input_shadow} !important;
            min-height: 56px !important; 
            display: flex;
            align-items: center;
            cursor: pointer;
        }}
        div[data-baseweb="select"] * {{
            font-family: 'VT323', monospace !important;
            font-size: 1.6rem !important;
            color: {text_color} !important;
            line-height: normal !important; 
        }}

        /* Make custom block wrapper for selectbox invisible */
        div[data-testid="stSelectbox"] {{
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }}

        /* -------------------------------------- */
        /* FORM FIX (NO INNER BORDER)             */
        /* -------------------------------------- */
        div[data-testid="stForm"] {{
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
        }}

        /* -------------------------------------- */
        /* IMAGE PREVIEW FIX                      */
        /* -------------------------------------- */
        [data-testid="stImage"] {{
            border: 4px solid {border_color} !important;
            box-shadow: 4px 4px 0px {shadow_color} !important;
            margin-bottom: 0.5rem;
            background-color: {img_bg};
            border-radius: 0px !important;
            display: flex !important;
            justify-content: center !important;
        }}
        [data-testid="stImage"] img {{
            border: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
            border-radius: 0px !important;
        }}

        /* -------------------------------------- */
        /* FULLSCREEN IMAGE FIX                   */
        /* -------------------------------------- */
        div[role="dialog"] {{
            background-color: rgba(0, 0, 0, 0.5) !important;
        }}
        div[role="dialog"] [data-testid="stImage"] {{
            border: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }}
        div[role="dialog"] img {{
            border: 6px solid {border_color} !important;
            box-shadow: 12px 12px 0px {shadow_color} !important;
            background-color: {container_bg} !important;
            max-width: 80vw !important;
            max-height: 80vh !important;
            object-fit: contain !important;
            margin: auto !important;
        }}
        /* Remove thin border/rounding around the preview container */
        .preview-grid div[data-testid="stContainer"],
        .preview-grid div[data-testid="stContainer"] > div,
        .preview-grid div[data-testid="stVerticalBlock"] {{
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            border-radius: 0px !important;
            background: transparent !important;
        }}
        [data-testid="StyledFullScreenButton"] {{
            right: 5px !important;
            top: 5px !important;
            z-index: 10 !important;
        }}

        /* -------------------------------------- */
        /* BUTTON STYLES                          */
        /* -------------------------------------- */
        button[kind="primary"], button[kind="primaryFormSubmit"] {{
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 1.1rem !important;
            background-color: #F16D34 !important; 
            color: #FFFFFF !important;
            border: 4px solid {border_color} !important;
            border-radius: 0px !important;
            height: 56px !important;
            width: 100% !important;
            box-shadow: 6px 6px 0px {shadow_color} !important;
            transition: all 0.1s ease;
            margin: 0px !important; 
        }}
        button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {{ background-color: #D65E2C !important; }}
        button[kind="primary"]:active, button[kind="primaryFormSubmit"]:active {{
            transform: translate(6px, 6px);
            box-shadow: 0px 0px 0px {shadow_color} !important;
        }}
        
        .stDownloadButton>button {{
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 1.1rem !important;
            background-color: #F16D34 !important; 
            color: #FFFFFF !important;
            border: 4px solid {border_color} !important;
            border-radius: 0px !important;
            height: 56px !important;
            width: 100% !important;
            box-shadow: 6px 6px 0px {shadow_color} !important;
            transition: all 0.1s ease;
            margin: 0px !important; 
        }}
        .stDownloadButton>button:hover {{ background-color: #D65E2C !important; }}
        .stDownloadButton>button:active {{
            transform: translate(6px, 6px);
            box-shadow: 0px 0px 0px {shadow_color} !important;
        }}
        
        button[kind="secondary"], button[kind="secondaryFormSubmit"] {{
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 1.1rem !important;
            background-color: {secondary_btn_bg} !important; 
            color: {text_color} !important;
            border: 4px solid {border_color} !important;
            border-radius: 0px !important;
            height: 56px !important;
            width: 100% !important;
            box-shadow: 6px 6px 0px {shadow_color} !important;
            transition: all 0.1s ease;
            margin: 0px !important;
        }}
        button[kind="secondary"]:hover, button[kind="secondaryFormSubmit"]:hover {{ background-color: {secondary_btn_hover} !important; }}
        button[kind="secondary"]:active, button[kind="secondaryFormSubmit"]:active {{
            transform: translate(6px, 6px);
            box-shadow: 0px 0px 0px {shadow_color} !important;
        }}
        
        /* Fullscreen Button */
        button[title="View fullscreen"] {{
            background-color: {container_bg} !important;
            border: 2px solid {border_color} !important;
            box-shadow: 2px 2px 0px {shadow_color} !important;
            opacity: 1 !important;
            visibility: visible !important;
            border-radius: 0px !important;
        }}
        button[title="View fullscreen"] svg {{
            stroke: {text_color} !important;
        }}
        
        /* Pixel-like Toggle/Slider and Checkbox Alignment */
        [data-testid="stCheckbox"], [data-testid="stToggle"] {{
            display: flex !important;
            align-items: center !important;
        }}
        [data-testid="stCheckbox"] label, [data-testid="stToggle"] label {{
            display: flex !important;
            align-items: center !important;
        }}
        [data-testid="stCheckbox"] label p, [data-testid="stToggle"] label p {{ 
            font-size: 1.4rem !important; 
            color: {text_color} !important; 
            font-weight: 600;
            margin: 0px !important;
            padding-left: 5px !important;
        }}
        
        /* Pixel-like Checkbox */
        [data-testid="stCheckbox"] * {{
            border-radius: 0px !important;
        }}
        

        /* Add gap below text inputs */
        div[data-testid="stTextInput"] {{
            margin-bottom: 2rem !important;
        }}
        
        code {{ font-size: 1.4rem !important; background-color: {input_shadow} !important; border: 2px dashed {border_color}; color: {text_color} !important; }}
        hr {{ display: none; }}

        .loading-box {{
            background-color: #F16D34; 
            color: #FFFFFF;
            border: 4px solid {border_color};
            box-shadow: 10px 10px 0px {shadow_color};
            padding: 30px 40px;
            text-align: center;
            font-size: 1.8rem;
            margin: 2rem auto;
        }}
        .box-error {{ background-color: #FF2400; }}
        .box-warning {{ background-color: #F16D34; color: #FFFFFF; }}
    </style>
""", unsafe_allow_html=True)

svg_logo = """
<svg width="68" height="68" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 3H6V4H8V5H14V13H2V3Z" fill="#000000"/>
    <path d="M3 4H5V5H7V6H13V12H3V4Z" fill="#FFDE00"/>
    <path d="M1 7H15V14H1V7Z" fill="#000000"/>
    <path d="M2 8H14V13H2V8Z" fill="#FFAA00"/>
    <path d="M5 4H11V8H5V4Z" fill="#FFFFFF"/>
    <path d="M6 5H8V7H6V5Z" fill="#FF2400"/>
    <path d="M9 6H10V7H9V6Z" fill="#FF2400"/>
</svg>
"""

# Render Header (Hidden during loading phases)
if st.session_state.step not in ['scanning', 'processing']:
    st.markdown(
        '<div class="header-container">'
        f'{svg_logo}'
        '<div class="pixel-title">SpriteFetch</div>'
        '<p class="pixel-sub">/// RETRO ASSET INGESTOR /// <br> Extract web graphics and compile to scalable vectors.</p>'
        '</div>', 
        unsafe_allow_html=True
    )

# ==========================================
# STATE MACHINE SYSTEM
# ==========================================

# ----------------- PHASE 1: INPUT -----------------
if st.session_state.step == 'input':
    url_input = st.text_input("TARGET URL:", placeholder="https://domain.com/path", value=st.session_state.target_url)
    
    keyword_input = st.text_input("FILTER KEYWORD (OPTIONAL):", placeholder="e.g., logo, icon, background", value=st.session_state.keyword)
    
    if st.button("SCAN TARGET", type="primary", use_container_width=True):
        if not url_input or url_input == "https://":
            st.toast("SYSTEM ERROR: INVALID URL")
        else:
            st.session_state.target_url = url_input
            st.session_state.keyword = keyword_input
            st.session_state.step = 'scanning'
            st.rerun()

# ----------------- PHASE 2: SCANNING -----------------
elif st.session_state.step == 'scanning':
    status_box = st.empty()
    status_box.markdown("""
        <div class="loading-box">
            PINGING SERVER & SCANNING DOM...
        </div>
    """, unsafe_allow_html=True)
    
    try:
        response = robust_fetch(st.session_state.target_url, timeout=15)
        
        if response.status_code != 200:
            status_box.markdown(f"""<div class="loading-box box-error">CONNECTION FAILED [CODE: {response.status_code}]</div>""", unsafe_allow_html=True)
            time.sleep(2.5)
            st.session_state.step = 'input'
            st.rerun()
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            discovered_assets = extract_image_urls(soup, st.session_state.target_url)
            
            # Filter assets if keywords are provided
            if st.session_state.keyword:
                raw_keywords = st.session_state.keyword.split(',')
                keywords = [k.strip().lower() for k in raw_keywords if k.strip()]
                
                if keywords:
                    discovered_assets = [
                        (url, ext) for url, ext in discovered_assets 
                        if any(kw in url.lower() for kw in keywords)
                    ]
            
            if not discovered_assets:
                status_box.markdown("""<div class="loading-box box-warning">NO SPRITES FOUND MATCHING CRITERIA.</div>""", unsafe_allow_html=True)
                time.sleep(2.5)
                st.session_state.step = 'input'
                st.rerun()
            else:
                st.session_state.scraped_assets = []
                total_assets = len(discovered_assets)
                
                for index, (asset_url, extension) in enumerate(discovered_assets):
                    pct = int((index + 1) / total_assets * 100)
                    bar = "█" * (pct // 5) + "-" * (20 - (pct // 5))
                    status_box.markdown(f"""
                        <div class="loading-box">
                            FETCHING PREVIEWS...<br>
                            [{bar}] {pct}%
                        </div>
                    """, unsafe_allow_html=True)
                    
                    try:
                        time.sleep(0.01)
                        res = robust_fetch(asset_url, timeout=10)
                        if res.status_code == 200:
                            st.session_state.scraped_assets.append({
                                'id': index, 'url': asset_url, 'ext': extension, 'bytes': res.content
                            })
                    except:
                        continue
                
                if len(st.session_state.scraped_assets) > 0:
                    st.session_state.step = 'select'
                    st.session_state.all_selected = True
                    for i in range(len(st.session_state.scraped_assets)):
                        st.session_state[f"chk_{i}"] = True
                    st.rerun()
                else:
                    status_box.markdown("""<div class="loading-box box-warning">FAILED TO DOWNLOAD ANY IMAGES.</div>""", unsafe_allow_html=True)
                    time.sleep(2.5)
                    st.session_state.step = 'input'
                    st.rerun()
                    
    except Exception as e:
        status_box.markdown(f"""<div class="loading-box box-error">FATAL ERROR: {e}</div>""", unsafe_allow_html=True)
        time.sleep(2.5)
        st.session_state.step = 'input'
        st.rerun()

# ----------------- PHASE 3: SELECTION -----------------
elif st.session_state.step == 'select':
    st.markdown(f"""
        <div style="background-color: #FFFFFF; color: #000000; border: 4px solid #000000; padding: 10px; box-shadow: 4px 4px 0px #000000; text-align: center; font-size: 1.5rem; margin-bottom: 1.5rem;">
            FOUND {len(st.session_state.scraped_assets)} SPRITES. SELECT TO INGEST:
        </div>
    """, unsafe_allow_html=True)
    
    st.session_state.output_format = st.selectbox("CHOOSE OUTPUT FORMAT:", ["SVG", "PNG", "JPG", "WEBP"])
    st.write("")
    
    def toggle_all():
        is_checked = st.session_state.master_check
        st.session_state.all_selected = is_checked
        for i in range(len(st.session_state.scraped_assets)):
            st.session_state[f"chk_{i}"] = is_checked

    st.checkbox("SELECT / DESELECT ALL ASSETS", value=st.session_state.all_selected, key="master_check", on_change=toggle_all)
    st.write("")
    
    with st.form("selection_form"):
        st.markdown("<div class='preview-grid'>", unsafe_allow_html=True)
        with st.container(height=380):
            # SPACER: Memastikan tombol fullscreen tidak terpotong container atas
            st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
            
            cols = st.columns(4)
            for i, asset in enumerate(st.session_state.scraped_assets):
                with cols[i % 4]:
                    try:
                        # Ensures images fit their columns responsively
                        st.image(asset['bytes'], use_container_width=True)
                    except:
                        st.write("[ERROR]")
                    val = st.session_state.get(f"chk_{i}", True)
                    st.checkbox(f"#{i+1}", value=val, key=f"chk_{i}")
                st.markdown("</div>", unsafe_allow_html=True)
                    
        st.write("") 
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            cancel_btn = st.form_submit_button("CANCEL", type="secondary", use_container_width=True)
        with col_btn2:
            process_btn = st.form_submit_button("PROCESS SELECTED", type="primary", use_container_width=True)

    if cancel_btn:
        st.session_state.step = 'input'
        st.session_state.scraped_assets = []
        st.rerun()
        
    if process_btn:
        selected_indices = [i for i in range(len(st.session_state.scraped_assets)) if st.session_state[f"chk_{i}"]]
        if not selected_indices:
            st.toast("ERROR: NO ASSETS SELECTED")
        else:
            st.session_state.selected_assets = selected_indices
            st.session_state.step = 'processing'
            st.rerun()

# ----------------- PHASE 4: PROCESSING -----------------
elif st.session_state.step == 'processing':
    loading_placeholder = st.empty()
    loading_placeholder.markdown("""<div class="loading-box">INITIALIZING PROCESS...</div>""", unsafe_allow_html=True)
    time.sleep(0.5) 
    
    selected_indices = st.session_state.selected_assets
    target_format = st.session_state.output_format
    success_count = 0
    
    # IF 1 IMAGE -> DIRECT FILE DOWNLOAD (NO ZIP)
    if len(selected_indices) == 1:
        sel_idx = selected_indices[0]
        asset = st.session_state.scraped_assets[sel_idx]
        
        loading_placeholder.markdown(f"""
            <div class="loading-box">
                CONVERTING TO {target_format}...<br>
                [████████████████████] 100%
            </div>
        """, unsafe_allow_html=True)
        
        processed_data = None
        file_ext = ""
        mime_type = ""
        
        if target_format == "SVG":
            processed_data = convert_to_embedded_svg(asset['bytes'], asset['ext'])
            file_ext = "svg"
            mime_type = "image/svg+xml"
        else:
            try:
                with Image.open(io.BytesIO(asset['bytes'])) as img:
                    out_buffer = io.BytesIO()
                    if target_format == "JPG":
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.save(out_buffer, format="JPEG")
                        file_ext = "jpg"
                        mime_type = "image/jpeg"
                    elif target_format == "PNG":
                        img.save(out_buffer, format="PNG")
                        file_ext = "png"
                        mime_type = "image/png"
                    elif target_format == "WEBP":
                        img.save(out_buffer, format="WEBP")
                        file_ext = "webp"
                        mime_type = "image/webp"
                    processed_data = out_buffer.getvalue()
            except:
                processed_data = None
                
        if processed_data:
            base_name = sanitize_filename(asset['url'], 1)
            st.session_state.download_data = processed_data
            st.session_state.download_filename = f"{base_name}.{file_ext}"
            st.session_state.download_mime = mime_type
            success_count = 1
            
        time.sleep(0.5)
        
    # IF > 1 IMAGE -> ZIP BUNDLE
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, sel_idx in enumerate(selected_indices):
                asset = st.session_state.scraped_assets[sel_idx]
                pct = int((idx + 1) / len(selected_indices) * 100)
                bar = "█" * (pct // 5) + "-" * (20 - (pct // 5))
                
                loading_placeholder.markdown(f"""
                    <div class="loading-box">
                        CONVERTING TO {target_format}...<br>
                        [{bar}] {pct}%
                    </div>
                """, unsafe_allow_html=True)
                
                processed_data = None
                file_ext = ""
                
                if target_format == "SVG":
                    processed_data = convert_to_embedded_svg(asset['bytes'], asset['ext'])
                    file_ext = "svg"
                else:
                    try:
                        with Image.open(io.BytesIO(asset['bytes'])) as img:
                            out_buffer = io.BytesIO()
                            if target_format == "JPG":
                                if img.mode in ("RGBA", "P"):
                                    img = img.convert("RGB")
                                img.save(out_buffer, format="JPEG")
                                file_ext = "jpg"
                            elif target_format == "PNG":
                                img.save(out_buffer, format="PNG")
                                file_ext = "png"
                            elif target_format == "WEBP":
                                img.save(out_buffer, format="WEBP")
                                file_ext = "webp"
                            processed_data = out_buffer.getvalue()
                    except:
                        processed_data = None
                        
                if processed_data:
                    base_name = sanitize_filename(asset['url'], success_count + 1)
                    zip_file.writestr(f"{base_name}.{file_ext}", processed_data)
                    success_count += 1
                    
                time.sleep(0.05) 
                
        time.sleep(0.5)
        st.session_state.download_data = zip_buffer.getvalue()
        st.session_state.download_filename = "spritefetch_assets.zip"
        st.session_state.download_mime = "application/zip"
    
    st.session_state.success_count = success_count
    st.session_state.step = 'result'
    st.rerun()

# ----------------- PHASE 5: RESULT & DOWNLOAD -----------------
elif st.session_state.step == 'result':
    st.markdown(f"""
        <div style="background-color: #F16D34; color: #FFFFFF; border: 4px solid #000000; padding: 15px; font-size: 1.8rem; text-align: center; box-shadow: 6px 6px 0px #000000; margin-bottom: 2rem;">
            <b>STAGE CLEARED!</b><br>{st.session_state.success_count} SPRITES PROCESSED AS {st.session_state.output_format}.
        </div>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("NEW TARGET", type="secondary", use_container_width=True):
            st.session_state.step = 'input'
            st.session_state.scraped_assets = []
            st.session_state.zip_buffer = None
            st.session_state.download_data = None
            st.rerun()
            
    with col_btn2:
        btn_label = "DOWNLOAD ASSET" if st.session_state.success_count == 1 else "DOWNLOAD .ZIP"
        if st.session_state.download_data:
            st.download_button(
                label=btn_label,
                data=st.session_state.download_data,
                file_name=st.session_state.download_filename,
                mime=st.session_state.download_mime,
                use_container_width=True
            )
        else:
            st.warning("FAILED TO GENERATE FILES.")

# ==========================================
# INSERTION POINT & THEME TOGGLE
# ==========================================
st.markdown("---")
col_blank, col_btn = st.columns([10, 1])
with col_btn:
    theme_btn_label = "☀" if st.session_state.theme == 'dark' else "☾"
    if st.button(theme_btn_label, type="secondary", use_container_width=True, key="theme_toggle_btn"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()