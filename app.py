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
                st.error(f"PDF oxunarkən xəta: {e}")
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 Sənədləri Dərindən Analiz Et", use_container_width=True):
        if not all_pages:
            st.warning("Zəhmət olmasa sənəd yükləyin.")
        else:
            with st.spinner('Border sənədləri analiz edir...'):
                try:
                    prompt = """
                    Sən peşəkar broker və OCR ekspertisən. Sənədləri analiz et və JSON qaytar.
                    
                    1. İNVOYS MƏLUMATLARI (invoice_data):
                       - invoice_no, invoice_date, total_amount, currency.
                    
                    2. HS KODLAR (items):
                       - hs_code (iki sətiri birləşdir), net, gross, price, desc.
                    
                    3. CMR MƏLUMATLARI (cmr_data):
                       - sender, receiver, truck_no.
                    
                    JSON strukturunu qoru:
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
                    st.success("✅ Border bütün məlumatları tapdı.")
                except Exception as e:
                    st.error(f"Analiz xətası: {e}")

# --- ANALİZ NƏTİCƏLƏRİ ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    inv = res.get('invoice_data', {})
    cmr = res.get('cmr_data', {})
    items = res.get('items', [])

    st.header("💰 İnvoys və Maliyyə")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("İnvoys No", inv.get('invoice_no', 'N/A'))
    col2.metric("Tarix", inv.get('invoice_date', 'N/A'))
    col3.metric("Məbləğ", f"{inv.get('total_amount', 0):,.2f}")
    col4.metric("Valyuta", inv.get('currency', 'USD'))

    st.divider()
    st.header("🚛 Nəqliyyat (CMR)")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Göndərən:** {cmr.get('sender', 'N/A')}")
    c2.write(f"**Alıcı:** {cmr.get('receiver', 'N/A')}")
    c3.write(f"**Maşın No:** {cmr.get('truck_no', 'N/A')}")

    st.divider()
    if items:
        df = pd.DataFrame(items)
        for col in ['net', 'gross', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        summary = df.groupby('hs_code').agg({'desc': 'first', 'net': 'sum', 'gross': 'sum', 'price': 'sum'}).reset_index()
        st.write("### 📊 GTİP üzrə Toplanmış Siyahı")
        st.table(summary)

        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Netto", f"{summary['net'].sum():,.2f}")
        m2.metric("Toplam Brutto", f"{summary['gross'].sum():,.2f}")
        m3.metric("Toplam Qiymət", f"{summary['price'].sum():,.2f}")
else:
    st.info("Border analiz üçün sənəd gözləyir...")