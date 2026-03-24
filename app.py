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
    st.error("API açarı tapılmadı! Streamlit Secrets bölməsini yoxlayın.")

# --- KÖMƏKÇİ FUNKSİYA ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | E-Customs Avtomatlaşdırma")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("CMR və ya İnvoys yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_analysis_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            try:
                pdf_images = convert_from_bytes(file.read())
                for idx, page_img in enumerate(pdf_images):
                    all_analysis_pages.append({"img": page_img, "name": f"{file.name}_p{idx+1}"})
            except Exception as e:
                st.error(f"PDF xətası: {e}")
        else:
            img = Image.open(file)
            all_analysis_pages.append({"img": img, "name": file.name})

    # --- ANALİZ DÜYMƏSİ ---
    if st.button("🔍 Analiz et və Skripti Hazırla"):
        with st.spinner('Süni İntellekt sənədləri oxuyur...'):
            try:
                # Prompt tək sətirdə yazıldı ki, dırnaq xətası (unterminated string) olmasın
                prompt_text = "Sən peşəkar gömrük brokerisən. Sənəddən bu məlumatları tap və JSON qaytar: sender (1. qrafa), receiver (2. qrafa), invoice_info (5. qrafa), truck_number (18. qrafa), total_invoice_value (22. qrafa), cmr_number (N/Z), items (hs_code, description, net_weight, gross_weight)."
                
                content = [{"type": "text", "text": prompt_text}]
                for page in all_analysis_pages:
                    b64 = encode_image(page["img"])
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": content}],
                    response_format={"type": "json_object"}
                )
                
                # Nəticəni yaddaşa yazırıq
                st.session_state['res_data'] = json.loads(response.choices[0].message.content)
                st.success("✅ Analiz tamamlandı!")
            except Exception as e:
                st.error(f"Analiz xətası: {e}")

# --- NƏTİCƏLƏR VƏ AVTOMATİK DOLDURMA SKRİPTİ ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    g = res.get('general', res) # Bəzən GPT birbaşa kökü qaytarır

    st.divider()
    st.header("🚀 E-Customs Sürətli Doldurma Paneli")
    
    # 1. Vizual Panel (Kopyalamaq üçün)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("1. Göndərən", g.get('sender', ''), key="v_q1")
        st.text_input("2. Alıcı", g.get('receiver', ''), key="v_q2")
        st.text_input("5. İnvoys No/Tarix", g.get('invoice_info', ''), key="v_q5")
    with col2:
        st.text_input("18. Maşın Nömrəsi", g.get('truck_number', ''), key="v_q18")
        st.text_input("22. Valyuta/Dəyər", g.get('total_invoice_value', ''), key="v_q22")
        st.text_input("CMR No", g.get('cmr_number', 'N/Z'), key="v_qcmr")

    # 2. AVTOMATİK DOLDURMA SKRİPTİ (JavaScript)
    st.subheader("⚡ Birbaşa Portala Ötürmə (Skript)")
    
    js_script = f"""
    (function() {{
        const data = {{
            s: "{g.get('sender', '')}",
            r: "{g.get('receiver', '')}",
            i: "{g.get('invoice_info', '')}",
            t: "{g.get('truck_number', '')}",
            v: "{g.get('total_invoice_value', '')}"
        }};
        
        // E-customs portalındakı qrafaları tapıb doldururuq
        const fields = {{
            'qrafa_1': data.s,
            'qrafa_2': data.r,
            'qrafa_5': data.i,
            'qrafa_18': data.t
        }};

        for (let [name, val] of Object.entries(fields)) {{
            let el = document.getElementsByName(name)[0] || document.getElementById(name);
            if (el) el.value = val;
        }}
        
        alert('Borderpoint: Məlumatlar dolduruldu! Lütfən yoxlayın.');
    }})();
    """.replace('\n', ' ')
    
    st.info("Aşağıdakı kodu kopyalayın, e-customs səhifəsində F12 sıxıb 'Console' bölməsinə yapışdırın.")
    st.code(js_script, language="javascript")

    # 3. Mallar Bölməsi
    st.write("### 📦 Mallar Siyahısı")
    for i, item in enumerate(res.get('items', [])):
        with st.expander(f"Mal {i+1}: {item.get('hs_code', 'N/A')}"):
            st.write(f"**Kod:** {item.get('hs_code')}")
            st.write(f"**Netto:** {item.get('net_weight')}")
            st.write(f"**Təsvir:** {item.get('description')}")