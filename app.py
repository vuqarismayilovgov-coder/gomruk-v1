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

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Streamlit Secrets hissəsini yoxlayın.")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=100)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | Tam Sənəd Analitiki")
st.info("İnvoys Nömrəsi, Tarixi, Valyutası və HS Kodların 100% dəqiqliklə oxunması.")

uploaded_files = st.file_uploader("Sənədləri (İnvoys, CMR) yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            pdf_images = convert_from_bytes(file.read())
            for idx, img in enumerate(pdf_images):
                all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 Sənədləri Dərindən Analiz Et", use_container_width=True):
        with st.spinner('Border sənədlərin "DNT"-sini oxuyur...'):
            try:
                # İNVOYS VƏ CMR ÜÇÜN BİRLƏŞMİŞ PROMPT
                prompt = """
                Sən peşəkar broker və OCR ekspertisən. Sənədləri (İnvoys və CMR) analiz et və JSON qaytar.
                
                1. İNVOYS MƏLUMATLARI (invoice_data):
                   - invoice_no: İnvoysun nömrəsi (məs: INV-123)
                   - invoice_date: İnvoysun tarixi (məs: 24.03.2026)
                   - total