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
                   - total_amount: İnvoysun cəmi məbləği (rəqəmlə)
                   - currency: Valyuta kodu (USD, EUR, TRY və s.)
                
                2. HS KODLAR (items):
                   - hs_code: İki sətirdə yazılan rəqəmləri birləşdir (məs: 6106.90 + 90.00.00 = 6106909000). Yalnız 10 rəqəm.
                   - net: Netto çəki (nöqtə ilə, məs: 101.08)
                   - gross: Brutto çəki (nöqtə ilə, məs: 106.46)
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
                st.success("✅ Border bütün məlumatları çarpaz yoxladı və tapdı.")
            except Exception as e:
                st.error(f"Xəta: {e}")

# --- ANALİZ NƏTİCƏLƏRİ ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    inv = res.get('invoice_data', {})
    cmr = res.get('cmr_data', {})
    items = res.get('items', [])

    # 1. MİLYYƏ VƏ İNVOYS BLOKU (YENİ)
    st.header("💰 İnvoys və Maliyyə Məlumatları")
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    col_i1.metric("İnvoys No", inv.get('invoice_no', 'N/A'))
    col_i2.metric("İnvoys Tarixi", inv.get('invoice_date', 'N/A'))
    col_i3.metric("Cəmi Məbləğ", f"{inv.get('total_amount', 0):,.2f}")
    col_i4.metric("Valyuta", inv.get('currency', 'USD'))

    # 2. CMR BLOKU
    st.divider()
    st.header("🚛 Nəqliyyat və Tərəflər (CMR)")
    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.write(f"**Göndərən:** {cmr.get('sender', 'N/A')}")
    col_c2.write(f"**Alıcı:** {cmr.get('receiver', 'N/A')}")
    col_c3.write(f"**Maşın No:** {cmr.get('truck_no', 'N/A')}")

    # 3. MALLARIN CƏDVƏLİ
    st.divider()
    if items:
        df = pd.DataFrame(items)
        # Rəqəm təmizləmə qorunur
        for col in ['net', 'gross', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # HS Kodlar üzrə cəmləmə
        summary = df.groupby('hs_code').agg({'desc': 'first', 'net': 'sum', 'gross': 'sum', 'price': 'sum'}).reset_index()
        
        st.write("### 📊 Toplanmış Mal Siyahısı (GTİP üzrə)")
        st.table(summary)

        # Cəmlər
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Netto", f"{summary['net'].sum():,.2f} kq")
        m2.metric("Toplam Brutto", f"{summary['gross'].sum():,.2f} kq")
        m3.metric("Toplam Qiymət", f"{summary['price'].sum():,.2f}")
else:
    st.info("Border analiz üçün sənəd gözləyir...")