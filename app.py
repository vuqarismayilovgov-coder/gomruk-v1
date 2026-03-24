import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI
import io
import base64
import json

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

st.title("📑 Borderpoint | E-Customs Ötürücü")

uploaded_files = st.file_uploader("CMR/İnvoys yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

if uploaded_files:
    # (Əvvəlki kodda olan fayl oxuma hissəsi bura daxildir...)
    all_pages = [] # Şəkilləri bura yığırıq
    
    if st.button("🔍 Analiz et və Ötürmə üçün Hazırla"):
        with st.spinner('Məlumatlar qrafalar üzrə qruplaşdırılır...'):
            # Prompt-u e-customs qrafalarına uyğunlaşdırırıq
            prompt_text = """
            Sən sənədləri e-customs (11-formalı bəyannamə) üçün hazırlayan köməkçisən.
            Aşağıdakı qrafaları dəqiq tap:
            - Qrafa 1 (Göndərən): Ad və ünvan
            - Qrafa 2 (Alıcı): Ad və ünvan
            - Qrafa 5 (İnvoys): No və Tarix
            - Qrafa 15 (Göndərən ölkə): Ölkə adı
            - Qrafa 17 (Təyinat): Azərbaycan
            - Qrafa 18 (Maşın No): Yuxarı və ya aşağıda tapılan nömrə
            - Qrafa 22 (Valyuta/Dəyər): Məbləğ və Valyuta
            - Mallar (XİF MN): 10 rəqəmli kod, Netto, Brutto
            
            JSON formatında qaytar.
            """
            # (OpenAI API çağırışı hissəsi...)
            # Tutaq ki, res_data artıq bizdədir:
            
            st.success("✅ Məlumatlar hazırdır! İndi e-customs pəncərəsini açın.")
            
            st.divider()
            
            # --- E-CUSTOMS ÖTÜRMƏ PANELİ ---
            st.subheader("🚀 E-Customs Sürətli Doldurma Paneli")
            st.warning("Hər bir xananın yanındakı 'Copy' düyməsini sıxın və portalda müvafiq yerə yapışdırın (Ctrl+V).")

            g = res_data['general']
            
            # Qrafalar üzrə qruplaşdırma
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 🏢 Ümumi Bölmə")
                st.text_input("1. Göndərən (Qrafa 1)", g.get('sender', 'N/A'), key="q1")
                st.text_input("2. Alıcı (Qrafa 2)", g.get('receiver', 'N/A'), key="q2")
                st.text_input("5. İnvoys No/Tarix (Qrafa 5)", g.get('invoice_info', 'N/A'), key="q5")
                st.text_input("18. Maşın Nömrəsi", g.get('truck_number', 'N/A'), key="q18")

            with col2:
                st.write("### 💰 Maliyyə və Ölkə")
                st.text_input("22. Valyuta/Dəyər", g.get('total_invoice_value', 'N/A'), key="q22")
                st.text_input("15. Göndərən Ölkə", g.get('sender_country', 'N/A'), key="q15")
                st.text_input("CMR Nömrəsi", g.get('cmr_number', 'N/Z'), key="qcmr")

            st.divider()
            
            # --- MALLAR BÖLMƏSİ (TOPLU) ---
            st.write("### 📦 Mallar Bölməsi (XİFİ)")
            for i, item in enumerate(res_data['items']):
                with st.expander(f"Mal {i+1}: {item.get('hs_code')}"):
                    c1, c2, c3 = st.columns(3)
                    c1.text_input(f"XİF MN kodu ({i+1})", item.get('hs_code'), key=f"hs_{i}")
                    c2.text_input(f"Netto ({i+1})", item.get('net_weight'), key=f"net_{i}")
                    c3.text_input(f"Brutto ({i+1})", item.get('gross_weight'), key=f"gr_{i}")
                    st.text_area(f"Malın təsviri ({i+1})", item.get('description'), key=f"desc_{i}")