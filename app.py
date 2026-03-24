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
                - Qrafa 1: sender (Göndərən)
                - Qrafa 2: receiver (Alıcı)
                - Qrafa 4: loading_place (Yükləmə yeri)
                - Qrafa 5: documents (İnvoys nömrəsi və s.)
                - Qrafa 15: sender_country (Ölkə)
                - Qrafa 18: truck_reg_number (Maşın nömrəsi)
                - Qrafa 23: driver_info (Sürücü)
                
                JSON Formatı:
                {
                  "cmr": {"sender": "...", "receiver": "...", "truck": "...", "inv_no": "...", "loading": "...", "country": "..."},
                  "items": [{"hs_code": "1234567890", "net": 0.0, "gross": 0.0, "price": 0.0, "desc": "..."}]
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
                st.success("✅ Border bütün sənədləri düzgün analiz etdi!")
            except Exception as e:
                st.error(f"Xəta: {e}")

# --- NƏTİCƏLƏR VƏ HESABLAMALAR ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    cmr = res.get('cmr', {})
    items = res.get('items', [])

    # CMR BLOKU
    st.header("🚛 CMR Məlumatları")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**1. Göndərən:** {cmr.get('sender', 'N/A')}")
        st.info(f"**4. Yükləmə:** {cmr.get('loading', 'N/A')}")
        st.info(f"**15. Ölkə:** {cmr.get('country', 'N/A')}")
    with col2:
        st.info(f"**2. Alıcı:** {cmr.get('receiver', 'N/A')}")
        st.info(f"**18. Maşın:** {cmr.get('truck', 'N/A')}")
        st.info(f"**5. Sənəd:** {cmr.get('inv_no', 'N/A')}")

    # MALLAR VƏ HS KOD QRUPLAŞDIRMA
    st.divider()
    st.header("📊 Mal Hesabatı (HS Kod üzrə Toplanmış)")
    
    df = pd.DataFrame(items)
    if not df.empty:
        # Rəqəmləri təmizləyirik (yalnız rəqəm və nöqtə qalsın)
        for col in ['net', 'gross', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # Eyni HS kodları cəmləyirik
        summary = df.groupby('hs_code').agg({
            'desc': 'first',
            'net': 'sum',
            'gross': 'sum',
            'price': 'sum'
        }).reset_index()

        st.table(summary)

        # Final Cəmlər
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Netto", f"{summary['net'].sum():,.2f} kq")
        m2.metric("Toplam Brutto", f"{summary['gross'].sum():,.2f} kq")
        m3.metric("Toplam Qiymət", f"{summary['price'].sum():,.2f}")

    # Master JS
    st.divider()
    st.subheader("⚡ E-Customs Master Kod")
    js_code = f"""
    (function() {{
        const d = {{ s: "{cmr.get('sender', '')[:50]}", r: "{cmr.get('receiver', '')[:50]}", t: "{cmr.get('truck', '')}", i: "{cmr.get('inv_no', '')}" }};
        document.querySelector('[id*="CONSIGNOR"]').value = d.s;
        document.querySelector('[id*="CONSIGNEE"]').value = d.r;
        document.querySelector('[id*="TRANSPORT_REG"]').value = d.t;
        document.querySelector('[id*="INVOICE_NUMBER"]').value = d.i;
        alert('Border: Hazırdır!');
    }})();
    """.replace('\n', ' ')
    st.code(js_code, language="javascript")
else:
    st.info("Sənəd gözləyirəm, Border...")