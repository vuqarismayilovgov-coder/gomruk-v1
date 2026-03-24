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
    st.error("API açarı tapılmadı!")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=95)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | Tam Analiz Paneli")

uploaded_files = st.file_uploader("Sənədləri bura atın", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            pdf_images = convert_from_bytes(file.read())
            for idx, img in enumerate(pdf_images):
                all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🚀 Bütün Qrafaları Analiz Et", use_container_width=True):
        with st.spinner('Border bütün sənədləri incələyir...'):
            try:
                # Maksimum məlumat üçün PROMPT yeniləndi
                prompt = """
                Sən peşəkar brokerisən. Sənəddən bu məlumatları tap və JSON qaytar:
                1. 'general': sender (1. qrafa), receiver (2. qrafa), invoice_no (5. qrafa), truck_no (18. qrafa), trailer_no (18. qrafa), shipping_date, sender_country (15. qrafa), currency (22. qrafa).
                2. 'items': hər mal üçün [hs_code, description, net_weight, gross_weight, price].
                
                DİQQƏT: Heç birini boş buraxma. Əgər sənəddə varsa, mütləq tap.
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
            except Exception as e:
                st.error(f"Xəta: {e}")

# --- NƏTİCƏLƏRİN GÖSTƏRİLMƏSİ (Bütün xanalar bura əlavə edildi) ---
if 'res_data' in st.session_state:
    data = st.session_state['res_data']
    gen = data.get('general', {})
    items = data.get('items', [])

    st.header("🚛 Bəyannamə üçün Əsas Məlumatlar")
    
    # Xanaları 3 sütun şəklində mütləq göstəririk
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.text_area("1. Göndərən", gen.get('sender', 'Tapılmadı'), height=100)
        st.text_input("15. Göndərən Ölkə", gen.get('sender_country', 'N/A'))
        st.text_input("5. İnvoys No", gen.get('invoice_no', 'N/A'))

    with c2:
        st.text_area("2. Alıcı", gen.get('receiver', 'Tapılmadı'), height=100)
        st.text_input("18. Maşın / Qoşqu", f"{gen.get('truck_no', '')} / {gen.get('trailer_no', '')}")
        st.text_input("Tarix", gen.get('shipping_date', 'N/A'))

    with c3:
        st.metric("22. Valyuta", gen.get('currency', 'USD'))
        st.info(f"**Yükləmə Yeri:** {gen.get('loading_place', 'Tapılmadı')}")

    # Malların Cədvəli
    st.divider()
    st.subheader("📊 Mal Məlumatları (Cəmlənmiş)")
    df = pd.DataFrame(items)
    if not df.empty:
        # Rəqəm təmizləmə
        for col in ['net_weight', 'gross_weight', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        summary = df.groupby('hs_code').agg({'description': 'first', 'net_weight': 'sum', 'gross_weight': 'sum', 'price': 'sum'}).reset_index()
        st.table(summary)
        
        # Cəmlər
        m1, m2, m3 = st.columns(3)
        m1.metric("Cəmi Netto", f"{summary['net_weight'].sum():,.2f}")
        m2.metric("Cəmi Brutto", f"{summary['gross_weight'].sum():,.2f}")
        m3.metric("Cəmi İnvoys Dəyəri", f"{summary['price'].sum():,.2f}")

else:
    st.info("Sənəd gözləyirəm, Border...")