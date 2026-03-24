import streamlit as st

# Saytın Başlığı
st.set_page_config(page_title="Borderpoint", layout="wide")
st.title("🚀 Borderpoint | Bəyannamə Doldurulması")

# Fayl yükləmə bölməsi
uploaded_file = st.file_uploader("XML və ya Sənəd şəklini yükləyin", type=['xml', 'pdf', 'jpg', 'png'])

if uploaded_file:
    # Ekranı iki hissəyə bölürük
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Qrafalar üzrə məlumatlar")
        # XML-dən gələn məlumatları simulyasiya edirik
        qrafa_2 = st.text_input("Qrafa 2: Göndərən", value="Logistics Corp LLC")
        qrafa_31 = st.text_area("Qrafa 31: Malın təsviri", value="Fındıq ləpəsi, 20 ton")
        qrafa_33 = st.text_input("Qrafa 33: XİF MN Kodu", value="0802220000")
        qrafa_35 = st.number_input("Qrafa 35: Brutto çəki (kq)", value=20000)
        
    with col2:
        st.subheader("📄 Bəyannamə Ön Baxış (SAD)")
        # Burada bəyannamənin vizual forması görünəcək
        st.info(f"""
        *BƏYANNAMƏ FORMASI (ÖN BAXIŞ)*
        ---
        *Göndərən:* {qrafa_2}
        *Kod:* {qrafa_33}
        *Çəki:* {qrafa_35} kq
        *Təsvir:* {qrafa_31}
        """)
        
        if st.button("Bəyannaməni Təsdiqlə və İxrac Et"):
            st.success("Bəyannamə uğurla hazırlandı!")
import pandas as pd
from PIL import Image
from openai import OpenAI
import io
import base64
import json
import xml.etree.ElementTree as ET
from pdf2image import convert_from_bytes

# --- API AÇARINI BURAYA YAPIŞDIR ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Smart Broker AI Pro", layout="wide", page_icon="🚢")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def create_qib_xml(data):
    root = ET.Element("ShortDeclaration")
    details = ET.SubElement(root, "DeclarationDetails")
    for key, value in data.items():
        child = ET.SubElement(details, key)
        child.text = str(value)
    return ET.tostring(root, encoding='utf-8')

# --- İnterfeys ---
st.sidebar.title("Borderpoint")
st.sidebar.markdown("---")
st.sidebar.write("✅ PDF və Şəkil dəstəyi")
st.sidebar.write("✅ Multi-sənəd analizi")

st.title("📑 QİB yazılımı (PDF & Image)")

# Fayl yükləmə (Həm PDF, həm də Şəkillər)
uploaded_files = st.file_uploader("Sənədləri seçin (PDF, JPG, PNG)", 
                                  type=["jpg", "png", "jpeg", "pdf"], 
                                  accept_multiple_files=True)

if uploaded_files:
    all_pages = [] # Analiz üçün istifadə olunacaq bütün şəkillər buraya yığılacaq
    
    st.subheader("📸 Yüklənən Sənədlər")
    cols = st.columns(len(uploaded_files))
    
    for i, file in enumerate(uploaded_files):
        if file.type == "application/pdf":
            # PDF-i şəkilə çeviririk (yalnız ilk səhifəsini)
            images = convert_from_bytes(file.read())
            if images:
                all_pages.append(images[0])
                cols[i].image(images[0], caption=f"PDF: {file.name}", use_container_width=True)
        else:
            # Şəkli birbaşa açırıq
            img = Image.open(file)
            all_pages.append(img)
            cols[i].image(img, caption=f"Şəkil: {file.name}", use_container_width=True)

    if st.button("🚀 Bütün Sənədləri Birlikdə Analiz Et"):
        if len(all_pages) > 0:
            with st.spinner('Süni İntellekt bütün sənədlərə baxır...'):
                try:
                    content = [{"type": "text", "text": """
                        Sən peşəkar Azərbaycan gömrük brokerisən. 
                        Təqdim olunan sənədlərdən (İnvoys, CMR, Packing List) Qısa İdxal Bəyannaməsi üçün məlumatları topla.
                        JSON formatında qaytar:
                        {
                            "qrafa_2_gonderen": "...", "qrafa_8_alici": "...",
                            "qrafa_18_masin": "...", "qrafa_22_mebleg": "...",
                            "qrafa_22_valyuta": "...", "qrafa_31_yuk": "...",
                            "qrafa_35_brutto": "...", "qrafa_38_netto": "...",
                            "qrafa_44_inv": "...", "qrafa_44_cmr": "..."
                        }
                    """}]
                    
                    # Bütün səhifələri analizə göndəririk
                    for page in all_pages:
                        b64 = encode_image(page)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": content}],
                        response_format={"type": "json_object"}
                    )
                    
                    res_data = json.loads(response.choices[0].message.content)
                    
                    # Nəticə Cədvəli
                    st.success("✅ Analiz tamamlandı!")
                    df = pd.DataFrame(list(res_data.items()), columns=["Qrafa", "Məlumat"])
                    st.data_editor(df, use_container_width=True, hide_index=True)
                    
                    # XML Yüklə
                    xml_data = create_qib_xml(res_data)
                    st.download_button("Gömrük üçün XML Yüklə", xml_data, "qib_export.xml")

                except Exception as e:
                    st.error(f"Xəta: {e}")