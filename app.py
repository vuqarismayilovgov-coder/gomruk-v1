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

# --- API QOŞULMASI ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Streamlit Secrets hissəsini yoxlayın.")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=100)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | Mükəmməl Sənəd Analizi")
st.caption("İnvoys, CMR və GTİP kodlarının (iki sətirli olsa belə) dəqiq oxunması.")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("Sənədləri bura atın", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            try:
                pdf_images = convert_from_bytes(file.read())
                for idx, img in enumerate(pdf_images):
                    all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
            except Exception as e:
                st.error(f"PDF xətası: {e}")
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 Sənədləri Analiz Et", use_container_width=True):
        if not all_pages:
            st.warning("Zəhmət olmasa sənəd yükləyin.")
        else:
            with st.spinner('Border sənədlərin dərinliyinə enir...'):
                try:
                    # Dəqiqləşdirilmiş Prompt
                    prompt = """Sən gömrük ekspertisən. Bu JSON formatında cavab ver:
                    {
                      "invoice": {"no": "", "date": "", "total": 0.0, "cur": ""},
                      "cmr": {"sender