import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI
import io
import base64
import json
from pdf2image import convert_from_bytes
import re

# --- SƏHİFƏ AYARLARI ---
st.set_page_config(page_title="Borderpoint AI Pro", layout="wide", page_icon="🚢")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Streamlit Secrets-i yoxlayın.")

def encode_image(image):
    buffered = io.BytesIO()
    # Keyfiyyəti 100% edirik ki, xırda rəqəmlər dumanlı görünməsin
    image.save(buffered, format="JPEG", quality=100)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | Super-Dəqiq HS Kod & CMR Analizi")

uploaded_files = st.file_uploader("CMR və İnvoysları yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            pdf_images = convert_from_bytes(file.read())
            for idx, img in enumerate(pdf_images):
                all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 Dəqiq Analizi Başlat", use_container_width=True):
        with st.spinner('Border HS kodları və CMR qrafalarını santimetr-santimetr yoxlayır...'):
            try:
                # HS Kodlar üçün xüsusi SƏRT PROMPT
                prompt = """
                Sən peşəkar gömrük brokerisən. Sənədləri (İnvoys və CMR) analiz et və JSON qaytar.
                
                HS KODLARI ÜÇÜN QAYDA:
                1. Sənəddəki hər bir malın 10 rəqəmli HS kodunu (XİF MN) tap.
                2. Əgər kod 8 və ya 10 rəqəmlidirsə, onu mütləq ayır. Malın adındakı rəqəmlərlə qarışdırma.
                3. Hər malın: hs_code, net_weight, gross_weight, price, description məlumatlarını götür.
                
                CMR QRAFALARI ÜÇÜN QAYDA:
                - Qrafa 1: sender (Göndər