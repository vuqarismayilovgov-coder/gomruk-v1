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
    st.error("API açarı tapılmadı!")

# --- KÖMƏKÇİ FUNKSİYA ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | E-Customs Avtomatlaşdırma")

uploaded_files = st.file_uploader("Sənədləri yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_analysis_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            pdf_images = convert_from_bytes(file.read())
            for idx, page_img in enumerate(pdf_images):
                all_analysis_pages.append({"img": page_img, "name": f"{file.name}_p{idx+1}"})
        else:
            img = Image.open(file)
            all_analysis_pages.append({"img": img, "name": file.name})

    if st.button("🔍 Analiz et və Skripti Hazırla"):
        with st.spinner('Süni İntellekt işləyir...'):
            try:
                # Prompt mətni (Dırnaqlara xüsusi diqqət yetirildi)
                prompt_text = "Sən gömrük köməkçisisən. Sənəddən sender, receiver, invoice_info, truck_number, total_invoice_value və items (hs_code, net_weight, description) məlumatlarını tap. Yalnız JSON qaytar."
                
                content = [{"type": "text", "text": prompt_text}]
                for page in all_analysis_pages:
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

# --- NƏTİCƏLƏR VƏ JAVASCRIPT SKRİPTİ ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    g = res.get('general', res)

    st.divider()
    st.subheader("⚡ E-Customs Avtomatik Doldurma Skripti")
    
    # Skripti hazırlayırıq
    js_code = f"""
    (function() {{
        const d = {{
            s: "{g.get('sender', '')}",
            r: "{g.get('receiver', '')}",
            i: "{g.get('invoice_info', '')}",
            t: "{g.get('truck_number', '')}",
            v: "{g.get('total_invoice_value', '')}"
        }};
        // Portalın xanalarını tapırıq (Nümunə adlar, lazım olsa dəyişərik)
        document.getElementsByName('qrafa_1')[0].value = d.s;
        document.getElementsByName('qrafa_2')[0].value = d.r;
        document.getElementsByName('qrafa_5')[0].value = d.i;
        document.getElementsByName('qrafa_18')[0].value = d.t;
        alert('Borderpoint: Məlumatlar dolduruldu!');
    }})();
    """.replace('\n', ' ')

    st.code(js_code, language="javascript")
    st.warning("Yuxarıdakı kodu kopyalayın, e-customs-da F12 sıxıb Console bölməsinə yapışdırın.")

    # Vizual panel (Kopyalamaq üçün)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Göndərən", g.get('sender', ''), key="v1")
        st.text_input("Alıcı", g.get('receiver', ''), key="v2")
    with col2:
        st.text_input("Maşın", g.get('truck_number', ''), key="v3")
        st.text_input("İnvoys", g.get('invoice_info', ''), key="v4")