import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI
import io
import base64
import json
import xml.etree.ElementTree as ET
from pdf2image import convert_from_bytes

# --- SƏHİFƏ AYARLARI ---
st.set_page_config(page_title="Borderpoint AI Pro", layout="wide", page_icon="🚢")

# --- API AÇARI (Streamlit Secrets-dən oxunur) ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Zəhmət olmasa Secrets bölməsində OPENAI_API_KEY-i yoxlayın.")

# --- KÖMƏKÇİ FUNKSİYALAR ---
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

# --- SİDEBAR (TƏNZİMLƏMƏLƏR) ---
st.sidebar.title("🚀 Borderpoint")
st.sidebar.markdown("---")
target_lang = st.sidebar.selectbox("Analiz nəticəsinin dili:", ["Azərbaycan", "English", "Русский", "Türkçe"])
st.sidebar.write("✅ PDF & Şəkil Dəstəyi")
st.sidebar.write("✅ Multi-sənəd Analizi")
st.sidebar.write("✅ Avtomatik XML İxracı")

st.title("📑 Borderpoint | Ağıllı Bəyannamə Analizatoru")
st.info("İnvoys, CMR və ya Packing List sənədlərini yükləyin. Sistem real məlumatları avtomatik çıxaracaq.")

# --- FAYL YÜKLƏMƏ (Çoxlu fayl qəbul edir) ---
uploaded_files = st.file_uploader("Sənədləri seçin (PDF, JPG, PNG)", 
                                  type=["jpg", "png", "jpeg", "pdf"], 
                                  accept_multiple_files=True)

if uploaded_files:
    all_pages = []
    st.subheader("📸 Yüklənən Sənədlər")
    # Yüklənən faylları yan-yana göstərmək üçün sütunlar
    cols = st.columns(len(uploaded_files) if len(uploaded_files) > 0 else 1)
    
    for i, file in enumerate(uploaded_files):
        try:
            if file.type == "application/pdf":
                # PDF-i şəkilə çeviririk
                images = convert_from_bytes(file.read())
                if images:
                    all_pages.append(images[0])
                    cols[i].image(images[0], caption=f"PDF: {file.name}", use_container_width=True)
            else:
                img = Image.open(file)
                all_pages.append(img)
                cols[i].image(img, caption=f"Şəkil: {file.name}", use_container_width=True)
        except Exception as e:
            st.error(f"Fayl oxunarkən xəta: {file.name}")

    # --- ANALİZ DÜYMƏSİ ---
    if st.button("🔍 Bütün Sənədləri Birlikdə Analiz Et"):
        if len(all_pages) > 0:
            with st.spinner(f'Süni İntellekt sənədləri {target_lang} dilində analiz edir...'):
                try:
                    # AI üçün təlimat (Prompt)
                    prompt_text = f"""
                        Sən peşəkar Azərbaycan gömrük brokerisən. 
                        Təqdim olunan sənədlərdən (İnvoys, CMR, Packing List) Qısa İdxal Bəyannaməsi üçün məlumatları topla.
                        Məlumatları Rus, İngilis, Türk və ya Azərbaycan dilində olan sənədlərdən oxu.
                        
                        JSON formatında bu açarlarla qaytar:
                        {{
                            "sender": "Göndərən şirkət adı",
                            "receiver": "Qəbul edən şirkət adı",
                            "invoice_value": "İnvoysun cəmi məbləği və valyutası",
                            "gross_weight": "Ümumi brutto çəki (kq)",
                            "net_weight": "Ümumi netto çəki (kq)",
                            "hs_code": "XİF MN kodu (10 rəqəmli)",
                            "description": "Malların qısa təsviri"
                        }}
                        Nəticəni yalnız JSON formatında və {target_lang} dilində ver. Əlavə mətn yazma.
                    """
                    
                    content = [{"type": "text", "text": prompt_text}]
                    
                    # Bütün şəkilləri analizə əlavə edirik
                    for page in all_pages:
                        b64 = encode_image(page)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                    # OpenAI Sorğusu
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": content}],
                        response_format={"type": "json_object"}
                    )
                    
                    res_data = json.loads(response.choices[0].message.content)
                    
                    # --- NƏTİCƏLƏRİN GÖSTƏRİLMƏSİ ---
                    st.success("✅ Analiz uğurla tamamlandı!")
                    
                    col_res1, col_res2 = st.columns([2, 1])
                    
                    with col_res1:
                        st.subheader("📊 Analiz Nəticəsi (Cədvəl)")
                        df = pd.DataFrame(list(res_data.items()), columns=["Qrafa / Sahə", "Məlumat"])
                        # İstifadəçi cədvəl üzərində düzəliş edə bilər
                        st.data_editor(df, use_container_width=True, hide_index=True)
                    
                    with col_res2:
                        st.subheader("💾 İxrac")
                        # XML faylı yaradılır
                        xml_data = create_qib_xml(res_data)
                        st.download_button(
                            label="📥 Gömrük üçün XML Yüklə",
                            data=xml_data,
                            file_name="borderpoint_export.xml",
                            mime="application/xml"
                        )
                        st.json(res_data)

                except Exception as e:
                    st.error(f"Süni intellekt xətası: {e}")
        else:
            st.warning("Zəhmət olmasa əvvəlcə sənəd yükləyin.")