import streamlit as st
import openai
import base64

# Saytın Başlığı
st.set_page_config(page_title="Borderpoint", layout="wide")
st.title("🌐 Borderpoint | Multi-Language Document AI")

# OpenAI API Açarı (Secrets-dən oxunur)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def analyze_with_ai(image_file, lang_prompt):
    # Şəkli kodlaşdırırıq (Base64)
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Sən peşəkar gömrük və loqistika mütəxəssisisən. Sənədləri Rus, İngilis, Türk və Azərbaycan dillərində mükəmməl anlayırsan."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Sənəddən aşağıdakı məlumatları dəqiq çıxar: {lang_prompt}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ],
            }
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

# 1. İnterfeys: Dil və Fayl Seçimi
st.sidebar.header("⚙️ Tənzimləmələr")
target_lang = st.sidebar.selectbox("Nəticə hansı dildə olsun?", ["Azərbaycan", "English", "Русский", "Türkçe"])

uploaded_file = st.file_uploader("Sənədi yükləyin (JPG, PNG, PDF)", type=['jpg', 'png', 'jpeg', 'pdf'])

# Çıxarılacaq məlumatların siyahısı (Sizin tələbinizə uyğun)
data_points = """
1. Brutto çəki (Gross weight)
2. Netto çəki (Net weight)
3. Göndərən (Consignor/Shipper)
4. Qəbul edən (Consignee/Receiver)
5. İnvoys dəyəri və Valyuta (Total Invoice Value)
6. HS Code (XİF MN Kodu - 10 rəqəmli)
"""

if uploaded_file:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.image(uploaded_file, caption="Yüklənən Sənəd", use_container_width=True)
        analyze_btn = st.button("🔍 Sənədi Analiz Et")

    with col2:
        if analyze_btn:
            with st.spinner("Süni İntellekt sənədi oxuyur..."):
                try:
                    result = analyze_with_ai(uploaded_file, data_points)
                    st.subheader(f"📊 Analiz Nəticəsi ({target_lang})")
                    st.success("Məlumatlar uğurla çıxarıldı:")
                    st.write(result)
                    
                    # Nəticəni kopyalamaq üçün bölmə
                    st.text_area("Xanaya köçürmək üçün mətn:", value=result, height=200)
                except Exception as e:
                    st.error(f"Xəta baş verdi: {e}")
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
if uploaded_file:
    # Faylın növünü yoxlayırıq
    file_type = uploaded_file.type
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Əgər yüklənən fayl həqiqətən şəkildirsə, onu göstər
        if "image" in file_type:
            st.image(uploaded_file, caption="Yüklənən Sənəd", use_container_width=True)
        # Əgər PDF-dirsə, məlumat mətni yaz (və ya PDF göstərici əlavə et)
        elif "pdf" in file_type:
            st.info("📄 PDF sənədi yükləndi. Analiz düyməsinə basaraq davam edin.")
        # Əgər XML-dirsə
        elif "xml" in file_type:
            st.info("🔗 XML faylı yükləndi. Məlumatlar emal olunur...")
        else:
            st.warning("Naməlum fayl formatı yükləndi.")
            
        analyze_btn = st.button("🔍 Sənədi Analiz Et")
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
                            "sender": "Göndərən şirkət adı",
                    "receiver": "Qəbul edən şirkət adı",
                    "invoice_value": "İnvoysun cəmi məbləği və valyutası",
                    "gross_weight": "Ümumi brutto çəki (kq)",
                    "net_weight": "Ümumi netto çəki (kq)",
                    "hs_code": "XİF MN kodu (10 rəqəmli)",
                    "description": "Malların qısa təsviri"
                }
                Yalnız JSON formatında cavab ver, əlavə mətn yazma.
                """}]
                
                # Şəkilləri mesaja əlavə edirik
                for img in all_pages:
                    # Şəkli base64-ə çevirmək üçün funksiya lazımdır (əvvəlki kodda olduğu kimi)
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img)}"}})
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": content}],
                    max_tokens=1000
                )
                
                st.subheader("📊 Analiz Nəticəsi")
                st.code(response.choices[0].message.content, language="json")
                
        except Exception as e:
            st.error(f"Xəta baş verdi: {e}")
    else:
        st.warning("Zəhmət olmasa sənədləri yükləyin."
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