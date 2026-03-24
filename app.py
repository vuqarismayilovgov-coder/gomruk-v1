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
    root 
[07:27, 2026-03-24] nomrem: import streamlit as st
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

def create_qib_xml(data):
    root = ET.Element("ShortDeclaration")
    details = ET.SubElement(root, "DeclarationDetails")
    for key, value in data.items():
        child = ET.SubElement(details, key)
        child.text = str(value)
    return ET.tostring(root, encoding='utf-8')

# --- SİDEBAR ---
st.sidebar.title("🚀 Borderpoint")
target_lang = st.sidebar.selectbox("Analiz dili:", ["Azərbaycan", "English", "Русский", "Türkçe"])
st.sidebar.info("Hər bir vərəq (PDF/Şəkil) süni intellekt tərəfindən tək-tək analiz olunur.")

st.title("📑 Borderpoint | Genişləndirilmiş Sənəd Analizi")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("Sənədləri yükləyin (Çoxsəhifəli PDF və ya Şəkillər)", 
                                  type=["jpg", "png", "jpeg", "pdf"], 
                                  accept_multiple_files=True)

all_analysis_pages = []

if uploaded_files:
    st.subheader("📸 Yüklənən Sənədlərin İlkin Baxışı")
    
    # Bütün yüklənən sənədləri vərəq-vərəq ayırırıq
    for file in uploaded_files:
        if file.type == "application/pdf":
            # PDF-in BÜTÜN vərəqlərini şəkilə çeviririk
            pdf_images = convert_from_bytes(file.read())
            for idx, page_img in enumerate(pdf_images):
                all_analysis_pages.append({"img": page_img, "name": f"{file.name} (Səhifə {idx+1})"})
        else:
            img = Image.open(file)
            all_analysis_pages.append({"img": img, "name": file.name})

    # Vərəqləri ekranda göstəririk
    grid_cols = st.columns(4)
    for i, page_data in enumerate(all_analysis_pages):
        with grid_cols[i % 4]:
            st.image(page_data["img"], caption=page_data["name"], use_container_width=True)

    # --- ANALİZ PROSESİ ---
    if st.button("🔍 Bütün Vərəqləri Analiz Et və Bəyannaməni Hazırla"):
        with st.spinner('Süni İntellekt hər bir vərəqi detallı oxuyur...'):
            try:
                # AI Təlimatı
                prompt_text = f"""
                    Sən peşəkar Azərbaycan gömrük brokerisən. 
                    Sənə təqdim olunan bütün şəkilləri (vərəqləri) tək-tək araşdır. 
                    Bu vərəqlərdən (İnvoys, CMR, Packing List) məlumatları topla və vahid bir Qısa İdxal Bəyannaməsi üçün birləşdir.
                    
                    Çıxarılacaq məlumatlar:
                    - sender (Göndərən), receiver (Qəbul edən), invoice_value (İnvoys məbləği/Valyuta),
                    - gross_weight (Brutto), net_weight (Netto), hs_code (XİF MN - 10 rəqəm), description (Təsvir).
                    
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
                
                # --- VİZUAL BƏYANNAMƏ ÖN BAXIŞ ---
                st.success("✅ Analiz tamamlandı! Bəyannamə ilkin baxış forması aşağıdadır:")
                
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    st.subheader("📝 Məlumat Redaktəsi")
                    # İstifadəçi cədvəldə düzəliş edə bilər
                    df = pd.DataFrame(list(res_data.items()), columns=["Sahə", "Dəyər"])
                    edited_df = st.data_editor(df, use_container_width=True, hide_index=True)
                    # Düzəliş edilmiş məlumatları geri JSON-a çeviririk
                    final_data = dict(edited_df.values)

                with col_right:
                    st.subheader("📄 Bəyannamə İlkin Baxış")
                    # Gömrük bəyannaməsinə bənzər vizual blok
                    st.markdown(f"""
                    <div style="border: 2px solid #2e7d32; padding: 15px; border-radius: 10px; background-color: #f1f8e9; color: #1b5e20;">
                        <h4>Bəyannamə Forması (SAD)</h4>
                        <p><b>2. Göndərən:</b> {final_data.get('sender', '')}</p>
                        <p><b>8. Alan:</b> {final_data.get('receiver', '')}</p>
                        <hr>
                        <p><b>22. Valyuta və Məbləğ:</b> {final_data.get('invoice_value', '')}</p>
                        <p><b>31. Malın təsviri:</b> {final_data.get('description', '')}</p>
                        <p><b>33. XİF MN Kodu:</b> {final_data.get('hs_code', '')}</p>
                        <p><b>35. Brutto çəki:</b> {final_data.get('gross_weight', '')} kq</p>
                        <p><b>38. Netto çəki:</b> {final_data.get('net_weight', '')} kq</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # XML Yükləmə Düyməsi
                    xml_out = create_qib_xml(final_data)
                    st.download_button("📥 Gömrük üçün XML İxrac Et", xml_out, "borderpoint_final.xml")

            except Exception as e:
                st.error(f"Sistem xətası: {e}")
else:
    st.info("Zəhmət olmasa sənədləri (PDF və ya Şəkil) yükləyin.")
[07:32, 2026-03-24] nomrem: import streamlit as st
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
st.sidebar.info("Sistem HS kodları üzrə netto/brutto çəkiləri ayıraraq hesablayır.")

st.title("📑 Borderpoint | HS Kod Üzrə Detallı Analiz")

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
    if st.button("🔍 Sənədləri Analiz Et (HS Kod Üzrə Qruplaşdır)"):
        with st.spinner('Süni İntellekt HS kodları üzrə çəkiləri hesablayır...'):
            try:
                prompt_text = f"""
                Sən peşəkar gömrük brokerisən. Sənədlərdəki bütün məhsulları HS Kodlarına (XİF MN) görə qruplaşdır.
                Hər bir fərqli HS kodu üçün ayrıca Netto və Brutto çəkiləri tap və ya hesabla.
                
                JSON formatında bu strukturda qaytar:
                {{
                    "general": {{
                        "sender": "Göndərən",
                        "receiver": "Qəbul edən",
                        "invoice_total": "Ümumi İnvoys Dəyəri və Valyuta"
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
                st.success("✅ Detallı analiz tamamlandı!")
                
                # Ümumi Məlumatlar
                st.subheader("🏢 Ümumi Məlumatlar")
                st.json(res_data['general'])

                # HS Kod Üzrə Cədvəl
                st.subheader("📦 Malların HS Kod Üzrə Bölgüsü")
                items_df = pd.DataFrame(res_data['items'])
                # Sütun adlarını düzəldirik
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
                st.download_button("📥 Detallı XML İxrac Et", xml_out, "borderpoint_detailed.xml")

            except Exception as e:
                st.error(f"Sistem xətası: {e}")
else:
    st.info("Sənədləri yükləyin ki, HS kod üzrə hesablamanı görəsiniz.")