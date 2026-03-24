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

# --- API ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Streamlit Secrets hissəsini yoxlayın.")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=100)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | Tam Sənəd Analitiki")
st.info("İnvoys (8001), CMR (2015) və Mənşə (7000) kodları ilə 44-cü qrafa sistemi.")

# --- FAYL YÜKLƏMƏ ---
uploaded_files = st.file_uploader("Sənədləri (İnvoys, CMR, Mənşə) yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            try:
                pdf_images = convert_from_bytes(file.read())
                for idx, img in enumerate(pdf_images):
                    all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
            except Exception as e:
                st.error(f"PDF xətası: {e}")
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🔍 Sənədləri Dərindən Analiz Et", use_container_width=True):
        if not all_pages:
            st.warning("Zəhmət olmasa sənəd yükləyin.")
        else:
            with st.spinner('Border 44-cü qrafa kodlarını təyin edir...'):
                try:
                    prompt = """Sən gömrük brokerisən. JSON qaytar:
                    {
                      "invoice_data": {"no": "", "date": "", "total": 0.0, "cur": ""},
                      "cmr_data": {"sender": "", "receiver": "", "truck_no": ""},
                      "box_44": [{"code": "8001", "name": "INVOICE", "ref": ""}, {"code": "2015", "name": "CMR", "ref": ""}, {"code": "7000", "name": "ORIGIN", "ref": ""}],
                      "items": [{"hs_code": "10 rəqəm", "net": 0.0, "gross": 0.0, "price": 0.0, "desc": ""}]
                    }
                    GTİP kodlarını birləşdir. Rəqəmlərdən vergülləri sil."""
                    
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
                    st.success("✅ Analiz tamamlandı!")
                except Exception as e:
                    st.error(f"Xəta: {e}")

# --- ANALİZ NƏTİCƏLƏRİ ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    inv = res.get('invoice_data', {})
    cmr = res.get('cmr_data', {})
    box44 = res.get('box_44', [])
    items = res.get('items', [])

    # 1. MİLYYƏ
    st.header("💰 İnvoys və Maliyyə")
    ci1, ci2, ci3, ci4 = st.columns(4)
    ci1.metric("İnvoys No", inv.get('no', 'N/A'))
    ci2.metric("Tarix", inv.get('date', 'N/A'))
    ci3.metric("Məbləğ", f"{inv.get('total', 0):,.2f}")
    ci4.metric("Valyuta", inv.get('cur', 'USD'))

    # 2. CMR
    st.divider()
    st.header("🚛 Nəqliyyat (CMR)")
    cc1, cc2, cc3 = st.columns(3)
    cc1.write(f"**Göndərən:** {cmr.get('sender', 'N/A')}")
    cc2.write(f"**Alıcı:** {cmr.get('receiver', 'N/A')}")
    cc3.write(f"**Maşın No:** {cmr.get('truck_no', 'N/A')}")

    # 3. 44-cü QRAFA
    st.divider()
    st.header("📋 44-cü Qrafa: Sənəd Kodları")
    if box44:
        st.table(pd.DataFrame(box44))

    # 4. MALLAR
    st.divider()
    if items:
        df = pd.DataFrame(items)