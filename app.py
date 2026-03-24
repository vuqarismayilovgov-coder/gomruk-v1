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
st.info("İnvoys (8001), CMR (2015) və Mənşə (7000) kodları ilə 44-cü qrafa inteqrasiyası.")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("Sənədləri (İnvoys, CMR, Mənşə) yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

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

    if st.button("🔍 Sənədləri Dərindən Analiz Et", use_container_width=True):
        with st.spinner('Border 44-cü qrafa kodlarını təyin edir...'):
            try:
                # 44-cü QRAFA ÜÇÜN ÖZƏL TƏLİMATLAR ƏLAVƏ EDİLDİ
                prompt = """
                Sən peşəkar broker və OCR ekspertisən. Sənədləri (İnvoys, CMR, Mənşə) analiz et və JSON qaytar.
                
                1. İNVOYS (invoice_data):
                   - no, date, total, cur.
                
                2. HS KODLAR (items):
                   - hs_code (iki sətiri birləşdir), net, gross, price, desc.
                
                3. CMR (cmr_data):
                   - sender, receiver, truck_no.
                
                4. 44-cü QRAFA (box_44):
                   - Əgər İnvoys tapılsa: {"code": "8001", "name": "INVOICE", "ref": "no"}
                   - Əgər CMR tapılsa: {"code": "2015", "name": "CMR", "ref": "truck_no"}
                   - Əgər Mənşə Sertifikatı tapılsa: {"code": "7000", "name": "CERTIFICATE OF ORIGIN", "ref": "doc_no"}
                
                JSON Strukturu:
                {
                  "invoice_data": {"no": "", "date": "", "total": 0.0, "cur": ""},
                  "cmr_data": {"sender": "", "receiver": "", "truck_no": ""},
                  "box_44": [{"code": "", "name": "", "ref": ""}],
                  "items": [{"hs_code": "", "net": 0.0, "gross": 0.0, "price": 0.0, "desc": ""}]
                }
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
                st.success("✅ Border bütün sənədləri və 44-cü qrafa kodlarını tapdı.")
            except Exception as e:
                st.error(f"Xəta: {e}")

# --- ANALİZ NƏTİCƏLƏRİ ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    inv = res.get('invoice_data',