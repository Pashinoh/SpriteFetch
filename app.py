import os
import io
import re
import time
import base64
import zipfile
import warnings
import logging
from urllib.parse import urljoin, urlparse, unquote

# ==========================================
# OPTIMASI: MATIKAN 100% SPAM TERMINAL
# ==========================================
os.environ["STREAMLIT_LOGGER_LEVEL"] = "error" # Matikan log Streamlit di OS
warnings.filterwarnings("ignore")
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('cloudscraper').setLevel(logging.CRITICAL)
logging.getLogger('streamlit').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context').setLevel(logging.CRITICAL)

import cloudscraper
from bs4 import BeautifulSoup
import streamlit as st
from PIL import Image, ImageDraw

# ==========================================
# DYNAMIC FAVICON GENERATOR (16x16 Pixel Art)
# ==========================================
favicon = Image.new('RGBA', (16, 16), (255, 255, 255, 0))
d = ImageDraw.Draw(favicon)
d.rectangle([1, 2, 7, 3], fill='#000000')
d.rectangle([1, 4, 15, 14], fill='#000000')
d.rectangle([2, 3, 6, 4], fill='#FFDE00')
d.rectangle([2, 5, 14, 13], fill='#FFAA00')
d.rectangle([4, 7, 12, 11], fill='#FFFFFF')
d.rectangle([5, 8, 7, 10], fill='#FF2400')
d.rectangle([9, 8, 11, 10], fill='#FF2400')

st.set_page_config(page_title="SpriteFetch", page_icon=favicon, layout="centered", initial_sidebar_state="collapsed")

# ==========================================
# CONFIGURATION & ENVIRONMENT
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# STATE MACHINE INITIALIZATION
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'target_url' not in st.session_state:
    st.session_state.target_url = ""
if 'scraped_assets' not in st.session_state:
    st.session_state.scraped_assets = []
if 'selected_assets' not in st.session_state:
    st.session_state.selected_assets = []
if 'zip_buffer' not in st.session_state:
    st.session_state.zip_buffer = None
if 'success_count' not in st.session_state:
    st.session_state.success_count = 0
if 'all_selected' not in st.session_state:
    st.session_state.all_selected = True

# ==========================================
# CORE SCRAPER LOGIC
# ==========================================
def convert_to_embedded_svg(img_bytes: bytes, original_format: str) -> bytes:
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
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Silkscreen&family=VT323&display=swap');

        *, html, body, p, span, div, label, input, button, a, [data-testid="stToast"] {
            font-family: 'VT323', monospace !important;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background-color: #FAFAFA !important;
            background-image: radial-gradient(#cccccc 2px, transparent 2px) !important;
            background-size: 24px 24px !important;
            color: #000000 !important;
        }
        
        header[data-testid="stHeader"] { display: none !important; }
        
        .block-container { 
            background-color: #FFFFFF !important;
            border: 4px solid #000000 !important;
            box-shadow: 10px 10px 0px #000000 !important;
            padding: 2.5rem !important; 
            margin-top: 4rem !important; 
            margin-bottom: 4rem !important;
            max-width: 680px !important;
            border-radius: 0px !important;
            overflow: visible !important;
        }
        
        .st-emotion-cache-1jicfl2, .st-emotion-cache-1104q3j { padding: 0px !important; }
        
        .header-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 4px dashed #000000;
            padding-bottom: 1.5rem;
        }
        
        .pixel-title {
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 2.8rem !important;
            color: #000000;
            margin-top: 0.5rem;
            margin-bottom: 0px;
            text-transform: none;
        }
        
        .pixel-sub {
            font-size: 1.5rem !important;
            color: #555555;
            line-height: 1.2;
            margin-top: 0.5rem;
        }
        
        .stTextInput label p {
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 0.95rem !important;
            color: #000000 !important;
            margin-bottom: 0.5rem;
        }
        
        .stTextInput>div>div>input {
            font-size: 1.5rem !important;
            background-color: #FFFFFF !important;
            border: 4px solid #000000 !important;
            color: #000000 !important;
            border-radius: 0px !important;
            padding: 0.75rem 1rem !important;
            height: 56px;
            box-shadow: inset 4px 4px 0px #E0E0E0;
            transition: all 0.1s ease;
        }
        
        .stTextInput>div>div>input::placeholder { color: rgba(0, 0, 0, 0.4) !important; }
        .stTextInput>div>div>input:focus {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 4px solid #000000 !important;
            box-shadow: inset 4px 4px 0px #E0E0E0 !important;
            outline: none !important;
        }
        
        button[kind="primary"], button[kind="primaryFormSubmit"] {
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 1.1rem !important;
            background-color: #2D68FF !important; 
            color: #FFFFFF !important;
            border: 4px solid #000000 !important;
            border-radius: 0px !important;
            height: 56px !important;
            width: 100% !important;
            box-shadow: 6px 6px 0px #000000 !important;
            transition: all 0.1s ease;
            margin: 0px !important; 
        }
        button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover { background-color: #1A4BCC !important; }
        button[kind="primary"]:active, button[kind="primaryFormSubmit"]:active {
            transform: translate(6px, 6px);
            box-shadow: 0px 0px 0px #000000 !important;
        }
        
        .stDownloadButton>button {
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 1.1rem !important;
            background-color: #FFDE00 !important; 
            color: #000000 !important;
            border: 4px solid #000000 !important;
            border-radius: 0px !important;
            height: 56px !important;
            width: 100% !important;
            box-shadow: 6px 6px 0px #000000 !important;
            transition: all 0.1s ease;
            margin: 0px !important; 
        }
        .stDownloadButton>button:hover { background-color: #E5C700 !important; }
        .stDownloadButton>button:active {
            transform: translate(6px, 6px);
            box-shadow: 0px 0px 0px #000000 !important;
        }
        
        button[kind="secondary"], button[kind="secondaryFormSubmit"] {
            font-family: 'Silkscreen', sans-serif !important;
            font-size: 1.1rem !important;
            background-color: #FFFFFF !important; 
            color: #000000 !important;
            border: 4px solid #000000 !important;
            border-radius: 0px !important;
            height: 56px !important;
            width: 100% !important;
            box-shadow: 6px 6px 0px #000000 !important;
            transition: all 0.1s ease;
            margin: 0px !important;
        }
        button[kind="secondary"]:hover, button[kind="secondaryFormSubmit"]:hover { background-color: #F0F0F0 !important; }
        button[kind="secondary"]:active, button[kind="secondaryFormSubmit"]:active {
            transform: translate(6px, 6px);
            box-shadow: 0px 0px 0px #000000 !important;
        }
        
        [data-testid="stCheckbox"] label p { font-size: 1.4rem !important; color: #000000 !important; font-weight: 600; }
        [data-testid="stImage"] img {
            border: 4px solid #000000 !important;
            box-shadow: 4px 4px 0px #000000 !important;
            margin-bottom: 0.5rem;
            background-color: #f1f1f1;
        }
        code { font-size: 1.4rem !important; background-color: #E0E0E0 !important; border: 2px dashed #000000; color: #000000 !important; }
        hr { display: none; }

        /* LOADING BOX DI TENGAH LAYAR (Bukan Overlay) */
        .loading-box {
            background-color: #2D68FF; 
            color: #FFFFFF;
            border: 4px solid #000000;
            box-shadow: 10px 10px 0px #000000;
            padding: 30px 40px;
            text-align: center;
            font-size: 1.8rem;
            margin: 2rem auto;
        }
        .box-error { background-color: #FF2400; }
        .box-warning { background-color: #FFDE00; color: #000000; }
    </style>
""", unsafe_allow_html=True)

# 8-Bit Pixel Folder SVG Logo
svg_logo = """
<svg width="240" height="64" viewBox="0 0 320 80" fill="none" xmlns="http://www.w3.org/2000/svg">
    <svg x="0" y="0" width="64" height="64" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
        <path d="M2 3H6V4H8V5H14V13H2V3Z" fill="#000000"/>
        <path d="M3 4H5V5H7V6H13V12H3V4Z" fill="#FFDE00"/>
        <path d="M1 7H15V14H1V7Z" fill="#000000"/>
        <path d="M2 8H14V13H2V8Z" fill="#FFAA00"/>
        <path d="M5 4H11V8H5V4Z" fill="#FFFFFF"/>
        <path d="M6 5H8V7H6V5Z" fill="#FF2400"/>
        <path d="M9 6H10V7H9V6Z" fill="#FF2400"/>
    </svg>
    <text x="82" y="48" font-family="Silkscreen, VT323, monospace" font-size="28" fill="#000000" style="font-weight:700;">SpriteFetch</text>
</svg>
"""

# Render Header (Hanya di-render jika bukan fase loading, biar layar fokus loading saja)
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
    st.write("") 
    if st.button("SCAN TARGET", type="primary", use_container_width=True):
        if not url_input or url_input == "https://":
            st.toast("SYSTEM ERROR: INVALID URL", icon="👾")
        else:
            st.session_state.target_url = url_input
            st.session_state.step = 'scanning'
            st.rerun()

# ----------------- PHASE 2: SCANNING (PURE LOADING) -----------------
elif st.session_state.step == 'scanning':
    status_box = st.empty()
    status_box.markdown("""
        <div class="loading-box">
            PINGING SERVER & SCANNING DOM...
        </div>
    """, unsafe_allow_html=True)
    
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        response = scraper.get(st.session_state.target_url, timeout=15)
        
        if response.status_code != 200:
            status_box.markdown(f"""<div class="loading-box box-error">CONNECTION FAILED [CODE: {response.status_code}]</div>""", unsafe_allow_html=True)
            time.sleep(2)
            st.session_state.step = 'input'
            st.rerun()
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            discovered_assets = extract_image_urls(soup, st.session_state.target_url)
            
            if not discovered_assets:
                status_box.markdown("""<div class="loading-box box-warning">NO SPRITES FOUND ON THIS STAGE.</div>""", unsafe_allow_html=True)
                time.sleep(2)
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
                        time.sleep(0.01) # Ultra cepat
                        res = scraper.get(asset_url, timeout=10)
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
                    time.sleep(2)
                    st.session_state.step = 'input'
                    st.rerun()
                    
    except Exception as e:
        status_box.markdown(f"""<div class="loading-box box-error">FATAL ERROR: {e}</div>""", unsafe_allow_html=True)
        time.sleep(2)
        st.session_state.step = 'input'
        st.rerun()

# ----------------- PHASE 3: SELECTION -----------------
elif st.session_state.step == 'select':
    st.markdown(f"""
        <div style="background-color: #FFFFFF; color: #000000; border: 4px solid #000000; padding: 10px; box-shadow: 4px 4px 0px #000000; text-align: center; font-size: 1.5rem; margin-bottom: 1.5rem;">
            FOUND {len(st.session_state.scraped_assets)} SPRITES. SELECT TO INGEST:
        </div>
    """, unsafe_allow_html=True)
    
    def toggle_all():
        is_checked = st.session_state.master_check
        st.session_state.all_selected = is_checked
        for i in range(len(st.session_state.scraped_assets)):
            st.session_state[f"chk_{i}"] = is_checked

    st.checkbox("SELECT / DESELECT ALL ASSETS", value=st.session_state.all_selected, key="master_check", on_change=toggle_all)
    st.write("")
    
    with st.form("selection_form"):
        with st.container(height=380):
            cols = st.columns(4)
            for i, asset in enumerate(st.session_state.scraped_assets):
                with cols[i % 4]:
                    try:
                        st.image(asset['bytes'], use_container_width=True)
                    except:
                        st.write("[ERROR]")
                    val = st.session_state.get(f"chk_{i}", True)
                    st.checkbox(f"#{i+1}", value=val, key=f"chk_{i}")
                    
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
            st.toast("ERROR: NO ASSETS SELECTED", icon="🛑")
        else:
            # SIMPAN DATA DAN HANCURKAN FORM DENGAN RERUN
            st.session_state.selected_assets = selected_indices
            st.session_state.step = 'processing'
            st.rerun()

# ----------------- PHASE 4: PROCESSING (PURE LOADING) -----------------
elif st.session_state.step == 'processing':
    loading_placeholder = st.empty()
    
    loading_placeholder.markdown("""<div class="loading-box">INITIALIZING CONVERSION...</div>""", unsafe_allow_html=True)
    time.sleep(0.5) 
    
    zip_buffer = io.BytesIO()
    success_count = 0
    selected_indices = st.session_state.selected_assets
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, sel_idx in enumerate(selected_indices):
            asset = st.session_state.scraped_assets[sel_idx]
            pct = int((idx + 1) / len(selected_indices) * 100)
            bar = "█" * (pct // 5) + "-" * (20 - (pct // 5))
            
            loading_placeholder.markdown(f"""
                <div class="loading-box">
                    CONVERTING TO SVG...<br>
                    [{bar}] {pct}%
                </div>
            """, unsafe_allow_html=True)
            
            svg_data = convert_to_embedded_svg(asset['bytes'], asset['ext'])
            if svg_data:
                base_name = sanitize_filename(asset['url'], success_count + 1)
                filename = f"{base_name}.svg"
                
                local_filepath = os.path.join(DOWNLOAD_DIR, filename)
                loop_counter = 1
                while os.path.exists(local_filepath):
                    filename = f"{base_name}_{loop_counter}.svg"
                    local_filepath = os.path.join(DOWNLOAD_DIR, filename)
                    loop_counter += 1
                    
                with open(local_filepath, 'wb') as local_file:
                    local_file.write(svg_data)
                    
                zip_file.writestr(filename, svg_data)
                success_count += 1
                
            time.sleep(0.1) 
    
    st.session_state.zip_buffer = zip_buffer.getvalue()
    st.session_state.success_count = success_count
    st.session_state.step = 'result'
    st.rerun()

# ----------------- PHASE 5: RESULT & DOWNLOAD -----------------
elif st.session_state.step == 'result':
    st.markdown(f"""
        <div style="background-color: #00FF41; color: #000000; border: 4px solid #000000; padding: 15px; font-size: 1.8rem; text-align: center; box-shadow: 6px 6px 0px #000000; margin-bottom: 2rem;">
            <b>STAGE CLEARED!</b><br>{st.session_state.success_count} SPRITES CONVERTED TO SVG.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='font-family: Silkscreen; font-size: 1rem; margin-bottom: 0px;'>LOCAL PATH:</p>", unsafe_allow_html=True)
    st.code(DOWNLOAD_DIR, language="text")
    st.write("")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("NEW TARGET", type="secondary", use_container_width=True):
            st.session_state.step = 'input'
            st.session_state.scraped_assets = []
            st.session_state.zip_buffer = None
            st.rerun()
            
    with col_btn2:
        st.download_button(
            label="DOWNLOAD .ZIP",
            data=st.session_state.zip_buffer,
            file_name="spritefetch_assets.zip",
            mime="application/zip",
            use_container_width=True
        )