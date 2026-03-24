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

# Vizual təmizlik üçün CSS
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stExpander"] { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- API ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
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
                # PDF səhifələrini şəklə çeviririk
                pdf_images = convert_from_bytes(file.read())
                for idx, img in enumerate(pdf_images):
                    all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
            except Exception as e:
                st.error(f"PDF oxunarkən xəta: {e}")
        else:
            try:
                all_pages.append({"img": Image.open(file), "name": file.name})
            except Exception as e:
                st.error(f"Şəkil oxunarkən xəta: {e}")

    if st.button("🚀 Kompleks Analizi Başlat", use_container_width=True):
        if not all_pages:
            st.warning("Zəhmət olmasa əvvəlcə sənəd yükləyin.")
        else:
            with st.spinner('Süni İntellekt CMR və İnvoysu oxuyur...'):
                try:
                    prompt = """
                    Sən təcrübəli gömrük brokerisən. Sənədləri analiz et və bu JSON strukturunda cavab ver:
                    {
                      "cmr_data": {
                        "sender": "Qrafa 1",
                        "receiver": "Qrafa 2",
                        "loading_place": "Qrafa 4",
                        "documents": "Qrafa 5",
                        "truck_number": "Qrafa 18",
                        "trailer_number": "Qrafa 18",
                        "driver_info": "Qrafa 23"
                      },
                      "items": [
                        {"hs_code": "10 rəqəmli kod", "description": "təsvir", "net_weight": 0.0, "gross_weight": 0.0, "price": 0.0}
                      ]
                    }
                    HS kodları malın adından ayır. Rəqəmlərdən vergülləri sil.
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
                    st.success("✅ Analiz uğurla tamamlandı!")
                except Exception as e:
                    st.error(f"Analiz zamanı xəta: {e}")

# --- NƏTİCƏLƏR ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    cmr = res.get('cmr_data', {})
    items = res.get('items', [])

    st.header("🚛 CMR Qrafaları")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**1. Göndərən:**\n\n{cmr.get('sender', 'N/A')}")
        st.success(f"**4. Yükləmə Yeri:**\n\n{cmr.get('loading_place', 'N/A')}")
    with col2:
        st.info(f"**2. Alıcı:**\n\n{cmr.get('receiver', 'N/A')}")
        st.warning(f"**18. Nəqliyyat:**\n\n{cmr.get('truck_number', 'N/A')} / {cmr.get('trailer_number', 'N/A')}")
    with col3:
        st.info(f"**5. Sənədlər:**\n\n{cmr.get('documents', 'N/A')}")
        st.info(f"**23. Sürücü:**\n\n{cmr.get('driver_info', 'N/A')}")

    st.divider()
    st.header("📊 Mal Qrupları (HS Kod üzrə Cəmlənmiş)")
    
    df = pd.DataFrame(items)
    if not df.empty:
        # Rəqəmləri təmizlə
        for col in ['net_weight', 'gross_weight', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

        summary = df.groupby('hs_code').agg({
            'description': 'first',
            'net_weight': 'sum',
            'gross_weight': 'sum',
            'price': 'sum'
        }).reset_index()

        st.table(summary)

        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Netto", f"{summary['net_weight'].sum():,.2f} kq")
        m2.metric("Toplam Brutto", f"{summary['gross_weight'].sum():,.2f} kq")
        m3.metric("Toplam Qiymət", f"{summary['price'].sum():,.2f}")

    # MASTER JAVASCRIPT
    st.divider()
    st.subheader("⚡ E-Customs Avtomatik Doldurma Kodu")
    js_master = f"""
    (function() {{
        const d = {{
            s: "{str(cmr.get('sender', ''))[:50]}",
            r: "{str(cmr.get('receiver', ''))[:50]}",
            t: "{cmr.get('truck_number', '')}",
            i: "{cmr.get('documents', '')}"
        }};
        document.querySelector('[id*="CONSIGNOR"]').value = d.s;
        document.querySelector('[id*="CONSIGNEE"]').value = d.r;
        document.querySelector('[id*="TRANSPORT_REG"]').value = d.t;
        document.querySelector('[id*="INVOICE_NUMBER"]').value = d.i;
        alert('Borderpoint: Məlumatlar hazırdır!');
    }})();