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

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stExpander"] { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- API ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Streamlit Secrets-i yoxlayın.")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | CMR & İnvoys Analitik Sistemi")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("CMR və İnvoys sənədlərini bura atın", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

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

    if st.button("🚀 Kompleks Analizi Başlat", use_container_width=True):
        if not all_pages:
            st.warning("Sənəd yükləyin.")
        else:
            with st.spinner('Süni İntellekt oxuyur...'):
                try:
                    prompt = "CMR və İnvoysu analiz et. JSON qaytar: cmr_data (sender, receiver, loading_place, documents, truck_number, trailer_number, driver_info), items (hs_code, description, net_weight, gross_weight, price)."
                    content = [{"type": "text", "text": prompt}]
                    for page in all_pages:
                        b64 = encode_image(page["img"])
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": content}],
                        response_format={"type": "json_object"}
                    )
                    st.session_state['res_data'] = json.loads(response.choices[0].message.content)
                    st.success("✅ Analiz tamamlandı!")
                except Exception as e:
                    st.error(f"Xəta: {e}")

# --- NƏTİCƏLƏR ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    cmr = res.get('cmr_data', {})
    items = res.get('items', [])

    st.header("🚛 CMR Qrafaları")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**1. Göndərən:**\n\n{cmr.get('sender', 'N/A')}")
        st.success(f"**4. Yükləmə Yeri:**\n\n{cmr.get('loading_place', 'N/A')}")