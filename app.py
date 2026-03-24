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

# CSS ilə interfeysi daha da təmizləyirik (Texniki məlumatların çıxmaması üçün)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- API ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Zəhmət olmasa Streamlit Secrets-də 'OPENAI_API_KEY' əlavə edin.")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | CMR & İnvoys Analitik Sistemi")
st.caption("Sənədləri yükləyin, HS kodları cəmləyin və CMR məlumatlarını birbaşa bəyannaməyə ötürün.")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("CMR və İnvoys sənədlərini bura atın", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            try:
                pdf