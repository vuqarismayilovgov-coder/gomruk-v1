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
            try:
                pdf_images = convert_from_bytes(file.read())
                for idx, img in enumerate(pdf_images):
                    all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
            except Exception as e:
                st.error(f"PDF xətası: {e}")
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 Sənədləri Dərindən Analiz Et", use_container_width=True):
        if not all_pages:
            st.warning("Zəhmət olmasa sənəd yükləyin.")
        else:
            with st.spinner('Border sənədlərin "DNT"-sini oxuyur...'):
                try:
                    # İNVOYS VƏ CMR ÜÇÜN BİRLƏŞMİŞ PROMPT (Qızıl Versiya)
                    prompt = """
                    Sən peşəkar broker və OCR ekspertisən. Sənədləri (İnvoys və CMR) analiz et və JSON qaytar.
                    
                    1. İNVOYS MƏLUMATLARI (invoice_data):
                       - invoice_no: İnvoysun nömrəsi
                       - invoice_date: İnvoysun tarixi
                       - total_amount: İnvoysun cəmi məbləği
                       - currency: Valyuta kodu (USD, EUR, TRY və s.)
                    
                    2. HS KODLAR (items):
                       - hs_code: İki sətirdə yazılan rəqəmləri birləşdir (məs: 6106.90 + 90.00.00 = 6106909000). Yalnız 10 rəqəm.
                       - net: Netto çəki (məs: 101.08)
                       - gross: Brutto çəki (məs: 106.46)
                       - price: Malın qiyməti
                       - desc: Malın təsviri
                    
                    3. CMR MƏLUMATLARI (cmr_data):
                       - sender: Qrafa 1
                       - receiver: Qrafa 2
                       - truck_no: Qrafa 18 (Maşın nömrəsi)
                    
                    Mütləq bu strukturu qoru:
                    {
                      "invoice_data": {"invoice_no": "", "invoice_date": "", "total_amount": 0.0, "currency": ""},
                      "cmr_data": {"sender": "", "receiver": "", "truck_no": ""},
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