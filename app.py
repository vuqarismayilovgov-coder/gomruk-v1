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

# --- API AÇARI ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Streamlit Secrets-i yoxlayın.")

# --- KÖMƏKÇİ FUNKSİYA ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | İxrac Bəyannaməsi Analitiki")

uploaded_files = st.file_uploader("Sənədləri yükləyin (PDF/JPG)", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            pdf_images = convert_from_bytes(file.read())
            for idx, img in enumerate(pdf_images):
                all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 İxrac Sənədlərini Analiz Et"):
        with st.spinner('Mallar XİF MN kodlarına görə qruplaşdırılır...'):
            try:
                # Prompt-u malların toplanması üçün gücləndirdik
                prompt = """
                Sən peşəkar gömrük brokerisən. Sənəddən aşağıdakıları JSON formatında çıxar:
                1. Ümumi məlumatlar: sender, receiver, invoice_info, truck_number, total_value, currency.
                2. Mallar (items): Hər bir malın 'hs_code' (10 rəqəm), 'net_weight', 'gross_weight', 'price', 'description'.
                
                ÇOX VACİB: Eyni HS koduna malik olan malları ayrı-ayrı obyektlər kimi siyahıya sal.
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
                st.success("✅ Analiz hazırdır!")
            except Exception as e:
                st.error(f"Xəta: {e}")

# --- ANALİZ NƏTİCƏLƏRİ VƏ HESABLAMALAR ---
if 'res_data' in st.session_state:
    data = st.session_state['res_data']
    items = data.get('items', [])
    
    # Pandas ilə məlumatları emal edirik (Toplama funksiyası)
    df = pd.DataFrame(items)
    
    if not df.empty:
        # Rəqəmləri təmizləyirik (vergülləri nöqtəyə çeviririk ki, riyazi hesablama getsin)
        for col in ['net_weight', 'gross_weight', 'price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # HS Koda görə qruplaşdırma və Toplama
        summary_df = df.groupby('hs_code').agg({
            'net_weight': 'sum',
            'gross_weight': 'sum',
            'price': 'sum',
            'description': 'first' # İlk təsviri saxla
        }).reset_index()

        st.divider()
        st.subheader("📊 XİF MN üzrə Toplam Hesabat (İxrac üçün)")
        st.dataframe(summary_df, use_container_width=True)

        # --- E-CUSTOMS ÜÇÜN MASTER KOD ---
        st.subheader("⚡ Portala Ötürmə Skripti (Birinci HS kod üzrə)")
        
        # İlk malın cəmlərini götürürük
        first_hs = summary_df.iloc[0] if not summary_df.empty else {}
        
        js_code = f"""
        (function() {{
            const d = {{
                h: "{first_hs.get('hs_code', '')}",
                n: "{first_hs.get('net_weight', '0')}",
                b: "{first_hs.get('gross_weight', '0')}",
                p: "{first_hs.get('price', '0')}"
            }};
            // Portalda müvafiq xanaları tapıb cəmləri yazırıq
            document.querySelector('[id*="HS_CODE"]').value = d.h;
            document.querySelector('[id*="NET_WEIGHT"]').value = d.n;
            document.querySelector('[id*="GROSS_WEIGHT"]').value = d.b;
            document.querySelector('[id*="TOTAL_PRICE"]').value = d.p;
            
            alert('Borderpoint: İlk mal qrupunun cəmləri dolduruldu!');
        }})();
        """.replace('\n', ' ')
        
        st.code(js_code, language="javascript")
        
        # Ümumi Məlumatlar
        st.write("### 🏢 Ümumi Məlumatlar")
        st.json(data.get('general', data))

else:
    st.info("Zəhmət olmasa sənədləri yükləyin.")