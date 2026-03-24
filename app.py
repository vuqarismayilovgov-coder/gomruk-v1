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
    st.error("API açarı tapılmadı! Secrets hissəsini yoxlayın.")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=100) # Maksimum keyfiyyət
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | Mükəmməl Oxuma və Analiz")
st.info("Məqsəd: GTİP, Çəki və Qiymət məlumatlarının 100% dəqiqliklə çıxarılması.")

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

    if st.button("🔍 Sənədləri Dərindən Analiz Et", use_container_width=True):
        with st.spinner('Border sətir-sətir, rəqəm-rəqəm oxuyur...'):
            try:
                # "Mükəmməl Oxuma" üçün xüsusi ssenari
                prompt = """
                Sən yüksək dəqiqlikli OCR və Gömrük Ekspertisən. Sənədləri (İnvoys və CMR) analiz et.
                
                GTİP (HS CODE) ÜÇÜN XÜSUSİ TƏLİMAT:
                - GTİP sütununda rəqəmlər iki sətir halında yazıla bilər (məsələn, yuxarıda 6106,90, aşağıda 90,00,00). 
                - Sən bu iki sətri MÜTLƏQ birləşdirməlisən. 
                - Nəticə yalnız rəqəmlərdən ibarət 10 rəqəmli vahid kod olmalıdır (məsələn: 6106909000).
                - Aradakı nöqtə və vergülləri sil.

                ÇƏKİ VƏ QİYMƏT ÜÇÜN XÜSUSİ TƏLİMAT:
                - "BRÜT KG", "NET KG" və "FİYAT" sütunlarını tap.
                - Rəqəmləri olduğu kimi (məsələn, 101,08) oxu və JSON-da nöqtə ilə (101.08) göstər.
                
                CMR QRAFALARI:
                - Qrafa 1, 2, 4, 5, 15, 18, 23 məlumatlarını tam mətn halında çıxar.
                
                Mütləq bu JSON strukturunda cavab ver:
                {
                  "cmr": {"sender": "", "receiver": "", "truck": "", "inv_no": "", "loading": "", "country": ""},
                  "items": [{"hs_code": "10 rəqəmli", "net": 0.0, "gross": 0.0, "price": 0.0, "desc": ""}]
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
                st.success("✅ Analiz hazırdır. Məhsul siyahısını yoxlayın.")
            except Exception as e:
                st.error(f"Xəta baş verdi: {e}")

# --- NƏTİCƏLƏR ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    items = res.get('items', [])
    cmr = res.get('cmr', {})

    # CMR Məlumatları
    with st.expander("🚛 CMR Məlumatlarını Gör", expanded=True):
        c1, c2 = st.columns(2)
        c1.write(f"**Göndərən:** {cmr.get('sender')}")
        c1.write(f"**Yükləmə:** {cmr.get('loading')}")
        c2.write(f"**Alıcı:** {cmr.get('receiver')}")
        c2.write(f"**Maşın:** {cmr.get('truck')}")

    # Mal Hesabatı
    st.divider()
    if items:
        df = pd.DataFrame(items)
        # Sütunları sığortalayırıq
        for col in ['net', 'gross', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # HS Kodlar üzrə qruplaşdırma
        if 'hs_code' in df.columns:
            summary = df.groupby('hs_code').agg({
                'desc': 'first',
                'net': 'sum',
                'gross': 'sum',
                'price': 'sum'
            }).reset_index()
            
            st.write("### 📊 Toplanmış Mal Siyahısı (HS Kod üzrə)")
            st.table(summary)

            # Cəmlər
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Netto", f"{summary['net'].sum():,.2f} kq")
            m2.metric("Toplam Brutto", f"{summary['gross'].sum():,.2f} kq")
            m3.metric("Toplam Qiymət", f"{summary['price'].sum():,.2f}")
    else:
        st.warning("Məhsul tapılmadı.")

else:
    st.info("Hələ ki məlumat yoxdur. Sənəd yükləyib analizi başladın.")