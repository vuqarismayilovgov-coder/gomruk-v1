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
    image.save(buffered, format="JPEG", quality=100)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | Çoxsaylı Mal Analizi")
st.info("Malların sayı çox olduqda sətirləri itirməmək üçün gücləndirilmiş rejim.")

uploaded_files = st.file_uploader("Sənədləri yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

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

    if st.button("🔍 Malları Sətir-Sətir Analiz Et", use_container_width=True):
        if not all_pages:
            st.warning("Sənəd yükləyin.")
        else:
            with st.spinner('Border hər sətiri tək-tək yoxlayır...'):
                try:
                    # GÜCLƏNDİRİLMİŞ MULTİ-ITEM PROMPT
                    prompt = """
                    Sən peşəkar broker və OCR mütəxəssisisən. Sənəddəki CƏDVƏLİ sətir-sətir analiz et.
                    
                    HƏR BİR MAL ÜÇÜN MÜTLƏQ QAYDALAR:
                    1. GTİP (HS CODE): İki sətirdə olan rəqəmləri (məs. 6106.90 və 90.00.00) birləşdirib 10 rəqəmli vahid kod et.
                    2. SƏTİR İZLƏMƏ: Hər bir HS kodun qarşısındakı Netto, Brutto və Qiyməti başqa sətirlərlə qarışdırma. Onlar eyni üfüqi xətt üzrə olmalıdır.
                    3. RƏQƏMLƏR: Vergülləri sil, yalnız nöqtə və rəqəm saxla.
                    
                    JSON strukturunda hər bir malı 'items' siyahısına sətir ardıcıllığı ilə əlavə et:
                    {
                      "invoice_data": {"no": "", "date": "", "total": 0.0, "cur": ""},
                      "cmr_data": {"sender": "", "receiver": "", "truck_no": ""},
                      "items": [
                        {"hs_code": "10 rəqəm", "net": 0.0, "gross": 0.0, "price": 0.0, "desc": "məhsul təsviri"}
                      ]
                    }
                    Heç bir malı ötürmə!
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
                    st.success("✅ Analiz tamamlandı!")
                except Exception as e:
                    st.error(f"Analiz xətası: {e}")

if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    items = res.get('items', [])
    
    # MALLARIN CƏDVƏLİ
    if items:
        st.header("📊 Malların Siyahısı")
        df = pd.DataFrame(items)
        
        # Sütun adlarını və rəqəmləri təmizləyirik
        for col in ['net', 'gross', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # Orijinal siyahını göstər
        st.write("#### Oxunan bütün sətirlər:")
        st.dataframe(df, use_container_width=True)
        
        # HS Kod üzrə cəmlənmiş halı
        st.divider()
        st.write("#### 📦 GTİP üzrə Toplanmış Hesabat (Bəyannamə üçün):")
        summary = df.groupby('hs_code').agg({'desc': 'first', 'net': 'sum', 'gross': 'sum', 'price': 'sum'}).reset_index()
        st.table(summary)

        m1, m2, m3 = st.columns(3)
        m1.metric("Cəmi Netto", f"{summary['net'].sum():,.2f}")
        m2.metric("Cəmi Brutto", f"{summary['gross'].sum():,.2f}")
        m3.metric("Cəmi Qiymət", f"{summary['price'].sum():,.2f}")
else:
    st.info("Border sənəd gözləyir...")