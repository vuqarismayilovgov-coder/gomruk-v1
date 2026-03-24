import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI
import io
import base64
import json
from pdf2image import convert_from_bytes

# --- SƏHİFƏ AYARLARI ---
st.set_page_config(page_title="Borderpoint AI Pro", layout="wide", page_icon="🚢")

# --- API AÇARI ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Streamlit Secrets bölməsində OPENAI_API_KEY əlavə edin.")

# --- KÖMƏKÇİ FUNKSİYALAR ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- SİDEBAR VƏ BAŞLIQ ---
st.sidebar.title("🚀 Borderpoint AI")
st.sidebar.info("CMR və İnvoys sənədlərini avtomatik analiz edib e-customs qrafalarına uyğunlaşdırır.")

if st.sidebar.button("Yaddaşı Təmizlə"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.title("📑 Borderpoint | E-Customs Avtomatlaşdırma")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("Sənədləri yükləyin (PDF, JPG, PNG)", 
                                  type=["jpg", "png", "jpeg", "pdf"], 
                                  accept_multiple_files=True)

all_analysis_pages = []

if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            try:
                pdf_images = convert_from_bytes(file.read())
                for idx, page_img in enumerate(pdf_images):
                    all_analysis_pages.append({"img": page_img, "name": f"{file.name} (Səh {idx+1})"})
            except Exception as e:
                st.error(f"PDF oxunarkən xəta: {e}")
        else:
            img = Image.open(file)
            all_analysis_pages.append({"img": img, "name": file.name})

    st.subheader(f"📸 Yüklənmiş {len(all_analysis_pages)} səhifə")
    
    # --- ANALİZ PROSESİ ---
    if st.button("🔍 Sənədləri Analiz Et"):
        with st.spinner('Süni İntellekt qrafaları müəyyən edir...'):
            try:
                prompt_text = """
                Sən peşəkar gömrük brokerisən. Sənədlərdən aşağıdakı qrafaları tap:
                - sender: CMR 1. qrafadakı göndərən adı və ünvanı.
                - receiver: CMR 2. qrafadakı alıcı adı və ünvanı.
                - invoice_info: CMR 5. qrafadakı invoys nömrəsi və tarixi.
                - sender_country: CMR 15. qrafadakı göndərən ölkə.
                - truck_number: Sənədin yuxarı sağında və ya aşağıda (23, 25 qrafalar) tapılan maşın nömrəsi.