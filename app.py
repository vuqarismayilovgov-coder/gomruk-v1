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
    st.error("API açarı tapılmadı! Streamlit Secrets bölməsində OPENAI_API_KEY-i yoxlayın.")

# --- KÖMƏKÇİ FUNKSİYA ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | E-Customs Ötürücü")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("CMR/İnvoys yükləyin (PDF və ya Şəkil)", 
                                  type=["jpg", "png", "jpeg", "pdf"], 
                                  accept_multiple_files=True)

all_analysis_pages = []

if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            try:
                pdf_images = convert_from_bytes(file.read())
                for idx, page_img in enumerate(pdf_images):
                    all_analysis_pages.append({"img": page_img, "name": f"{file.name} (Səh. {idx+1})"})
            except Exception as e:
                st.error(f"PDF oxunarkən xəta: {e}")
        else:
            img = Image.open(file)
            all_analysis_pages.append({"img": img, "name": file.name})

    st.subheader(f"📸 Yüklənmiş {len(all_analysis_pages)} səhifə")
    
    # --- ANALİZ DÜYMƏSİ ---
    if st.button("🔍 Analiz et və Ötürmə üçün Hazırla"):
        with st.spinner('Məlumatlar qrafalar üzrə qruplaşdırılır...'):
            try:
                prompt_text = """
                Sən sənədləri e-customs (11-formalı bəyannamə) üçün hazırlayan köməkçisən.
                Aşağıdakı qrafaları sənəddən dəqiq tap və JSON formatında qaytar:
                - sender: CMR 1. qrafadakı göndərən adı və ünvanı.
                - receiver: CMR 2. qrafadakı alıcı adı və ünvanı.
                - invoice_info: CMR 5. qrafadakı invoys nömrəsi və tarixi.
                - sender_country: CMR 15. qrafadakı göndərən ölkə.
                - truck_number: Sənədin yuxarı sağında və ya aşağıda tapılan maşın nömrəsi.
                - total_invoice_value: 22. qrafadakı valyuta və məbləğ.
                - cmr_number: Sənədin yuxarı sağındakı nömrə, yoxdursa "N/Z".
                - items: Malların siyahısı (hs_code (10 rəqəmli), description, net_weight, gross_weight).
                
                Nəticəni yalnız JSON olaraq qaytar.
                """
                
                content = [{"type": "text", "text": prompt_text}]
                for page in all_analysis_pages:
                    b64 = encode_image(page["img"])
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": content}],
                    response_format={"type": "json_object"}
                )
                
                # Məlumatı yaddaşa yazırıq
                st.session_state['res_data'] = json.loads(response.choices[0].message.content)
                st.success("✅ Analiz tamamlandı!")

            except Exception as e:
                st.error(f"Analiz zamanı xəta: {e}")

# --- E-CUSTOMS PANELİ (Yalnız analiz bitdikdə görünür) ---
if 'res_data' in st.session_state:
    res_data = st.session_state['res_data']
    g = res_data.get('general', res_data) # Bəzən GPT birbaşa kökü qaytarır
    
    st.divider()
    st.subheader("🚀 E-Customs Sürətli Doldurma Paneli")
    st.info("Xanalardakı məlumatları kopyalayıb e.customs.gov.az portalına yapışdırın.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 🏢 Ümumi Bölmə")
        st.text_input("1. Göndərən (Qrafa 1)", g.get('sender', 'N/A'), key="final_q1")
        st.text_input("2. Alıcı (Qrafa 2)", g.get('receiver', 'N/A'), key="final_q2")
        st.text_input("5. İnvoys No/Tarix (Qrafa 5)", g.get('invoice_info', 'N/A'), key="final_q5")
        st.text_input("18. Maşın Nömrəsi", g.get('truck_number', 'N/A'), key="final_q18")

    with col2:
        st.write("### 💰 Maliyyə və Ölkə")
        st.text_input("22. Valyuta/Dəyər", g.get('total_invoice_value', 'N/A'), key="final_q22")
        st.text_input("15. Göndərən Ölkə", g.get('sender_country', 'N/A'), key="final_q15")
        st.text_input("CMR Nömrəsi", g.get('cmr_number', 'N/Z'), key="final_qcmr")

    st.divider()
    
    st.write("### 📦 Mallar Bölməsi (XİFİ)")
    items = res_data.get('items', [])
    for i, item in enumerate(items):
        with st.expander(f"Mal {i+1}: {item.get('hs_code', 'Kod yoxdur')}"):
            c1, c2, c3 = st.columns(3)
            c1.text_input("XİF MN kodu", item.get('hs_code'), key=f"f_hs_{i}")
            c2.text_input("Netto", item.get('net_weight'), key=f"f_n_{i}")
            c3.text_input("Brutto", item.get('gross_weight'), key=f"f_g_{i}")
            st.text_area("Malın təsviri", item.get('description'), key=f"f_d_{i}")

else:
    if not uploaded_files:
        st.info("Zəhmət olmasa CMR və ya İnvoys sənədlərini yükləyib 'Analiz et' düyməsini sıxın.")