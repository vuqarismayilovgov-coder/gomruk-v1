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

# --- API ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı!")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | CMR və İnvoys Analitiki")

uploaded_files = st.file_uploader("CMR, İnvoys və ya Digər sənədlər", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            pdf_images = convert_from_bytes(file.read())
            for idx, img in enumerate(pdf_images):
                all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 Sənədləri Kompleks Analiz Et"):
        with st.spinner('CMR və İnvoys məlumatları emal olunur...'):
            try:
                # CMR və HS kodlar üçün gücləndirilmiş PROMPT
                prompt = """
                Sən peşəkar gömrük brokerisən. Sənədləri (CMR və İnvoys) analiz et və JSON qaytar:
                
                1. CMR Məlumatları (cmr_data):
                   - sender (Qrafa 1): Ad və ünvan
                   - receiver (Qrafa 2): Ad və ünvan
                   - loading_place (Qrafa 4): Yer və tarix
                   - documents (Qrafa 5): Əlavə sənədlər (İnvoys no və s.)
                   - truck_number (Qrafa 18): Maşın nömrəsi
                   - trailer_number (Qrafa 18): Qoşqu nömrəsi
                   - driver_info (Qrafa 23): Sürücü adı və imza yeri
                   - custom_marks (Qrafa 15): Göndərən ölkə kodu
                
                2. Mal Məlumatları (items): 
                   - Hər bir sətirdə: hs_code (10 rəqəm), description, net_weight, gross_weight, price.
                
                ÇOX VACİB: Rəqəmləri təmiz çıxar (vergülsüz), HS kodları malın adından ayır.
                """
                
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
                st.success("✅ Kompleks analiz tamamlandı!")
            except Exception as e:
                st.error(f"Xəta: {e}")

# --- NƏTİCƏLƏR VƏ ANALİTİKA ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    cmr = res.get('cmr_data', {})
    items = res.get('items', [])

    # --- CMR BÖLMƏSİ ---
    st.header("🚛 CMR Məlumatları (Bəyannamə üçün)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("1. Göndərən", cmr.get('sender', ''), key="cmr_1")
        st.text_input("4. Yükləmə Yeri", cmr.get('loading_place', ''), key="cmr_4")
    with c2:
        st.text_input