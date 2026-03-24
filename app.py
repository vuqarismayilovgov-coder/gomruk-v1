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

# --- API AÇARI ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Secrets bölməsində OPENAI_API_KEY-i yoxlayın.")

# --- KÖMƏKÇİ FUNKSİYALAR ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def create_qib_xml(general_data, items_data):
    root = ET.Element("ShortDeclaration")
    gen_details = ET.SubElement(root, "GeneralDetails")
    for key, value in general_data.items():
        child = ET.SubElement(gen_details, key)
        child.text = str(value)
    
    items_node = ET.SubElement(root, "Items")
    for item in items_data:
        item_node = ET.SubElement(items_node, "Item")
        for k, v in item.items():
            child = ET.SubElement(item_node, k)
            child.text = str(v)
    return ET.tostring(root, encoding='utf-8')

# --- SİDEBAR ---
st.sidebar.title("🚀 Borderpoint")
target_lang = st.sidebar.selectbox("Analiz dili:", ["Azərbaycan", "English", "Русский", "Türkçe"])
st.sidebar.info("Sistem Maşın nömrəsi, CMR və HS kodlar üzrə detallı analiz aparır.")

st.title("📑 Borderpoint | Detallı Gömrük Analizi")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("Sənədləri yükləyin (PDF və ya Şəkillər)", 
                                  type=["jpg", "png", "jpeg", "pdf"], 
                                  accept_multiple_files=True)

all_analysis_pages = []

if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            pdf_images = convert_from_bytes(file.read())
            for idx, page_img in enumerate(pdf_images):
                all_analysis_pages.append({"img": page_img, "name": f"{file.name} (Səh. {idx+1})"})
        else:
            img = Image.open(file)
            all_analysis_pages.append({"img": img, "name": file.name})

    st.subheader(f"📸 Yüklənmiş {len(all_analysis_pages)} vərəq/səhifə")
    grid_cols = st.columns(6)
    for i, page_data in enumerate(all_analysis_pages):
        with grid_cols[i % 6]:
            st.image(page_data["img"], caption=page_data["name"], use_container_width=True)

    # --- ANALİZ PROSESİ ---
    if st.button("🔍 Sənədləri Tam Analiz Et"):
        with st.spinner('Süni İntellekt CMR, Maşın və HS kodları analiz edir...'):
            try:
                prompt_text = f"""
                Sən peşəkar gömrük brokerisən. Sənədlərdəki (İnvoys, CMR, Packing List) bütün məlumatları oxu.
                
                Səndən tələb olunanlar:
                1. Ümumi məlumatları (General) tap: Göndərən, Alan, Maşın nömrəsi, CMR tarixi, CMR nömrəsi, Toplam İnvoys Dəyəri və Toplam Brutto çəki.
                2. Malları HS Kodlarına (XİF MN) görə TAM DƏQİQ qruplaşdır.
                3. Hər bir fərqli HS kodu üçün ayrıca Netto və Brutto çəkiləri müəyyən et.
                
                JSON formatında bu strukturda qaytar:
                {{
                    "general": {{
                        "sender": "Göndərən",
                        "receiver": "Qəbul edən",
                        "truck_number": "Maşın nömrəsi",
                        "cmr_number": "CMR nömrəsi",
                        "cmr_date": "CMR tarixi",
                        "total_invoice": "Ümumi İnvoys Dəyəri",
                        "total_gross_weight": "Toplam Brutto Çəki (kq)"
                    }},
                    "items": [
                        {{
                            "hs_code": "10 rəqəmli kod",
                            "description": "Məhsulun adı",
                            "net_weight": "Netto çəki (kq)",
                            "gross_weight": "Brutto çəki (kq)"
                        }}
                    ]
                }}
                Nəticəni yalnız JSON formatında və {target_lang} dilində qaytar.
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
                
                res_data = json.loads(response.choices[0].message.content)
                
                # --- NƏTİCƏLƏR ---
                st.success("✅ Analiz tamamlandı!")
                
                # Ümumi Məlumatlar Paneli
                st.subheader("🏢 Ümumi Məlumatlar")
                g = res_data['general']
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.write(f"*🚛 Maşın:* {g.get('truck_number', 'N/A')}")
                    st.write(f"*📄 CMR No:* {g.get('cmr_number', 'N/A')}")
                    st.write(f"*📅 Tarix:* {g.get('cmr_date', 'N/A')}")
                with col_g2:
                    st.write(f"*🏢 Göndərən:* {g.get('sender', 'N/A')}")
                    st.write(f"*💰 İnvoys:* {g.get('total_invoice', 'N/A')}")
                    st.write(f"*⚖️ Toplam Brutto:* {g.get('total_gross_weight', 'N/A')}")

                # HS Kod Üzrə Cədvəl
                st.subheader("📦 Malların HS Kod Üzrə Bölgüsü")
                items_df = pd.DataFrame(res_data['items'])
                items_df.columns = ["HS Kod", "Malın Təsviri", "Netto (kq)", "Brutto (kq)"]
                st.data_editor(items_df, use_container_width=True, hide_index=True)

                # --- BƏYANNAMƏ ÖN BAXIŞ (VİZUAL) ---
                st.divider()
                st.subheader("📄 Bəyannamə (SAD) İlkin Baxış")
                
                for idx, row in items_df.iterrows():
                    st.markdown(f"""
                    <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 5px; background-color: #fcfcfc;">
                        <span style="color: blue;"><b>Maddə {idx+1}:</b></span> 
                        <b>Kod:</b> {row['HS Kod']} | 
                        <b>Təsvir:</b> {row['Malın Təsviri']} | 
                        <b>Netto:</b> <span style="color: green;">{row['Netto (kq)']} kq</span> | 
                        <b>Brutto:</b> <span style="color: red;">{row['Brutto (kq)']} kq</span>
                    </div>
                    """, unsafe_allow_html=True)

                # XML İxrac
                xml_out = create_qib_xml(res_data['general'], res_data['items'])
                st.download_button("📥 Detallı XML İxrac Et", xml_out, "borderpoint_final.xml")

            except Exception as e:
                st.error(f"Sistem xətası: {e}")
else:
    st.info("Zəhmət olmasa sənədləri yükləyin.")