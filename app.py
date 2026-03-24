import streamlit as st
import pandas as pd
from PIL import Image
from openai import OpenAI
import io
import base64
import json
from pdf2image import convert_from_bytes
import re

# --- SƏHİFƏ AYARLARI ---
st.set_page_config(page_title="Borderpoint AI Pro", layout="wide", page_icon="🚢")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API açarı tapılmadı! Zəhmət olmasa Streamlit Secrets-də 'OPENAI_API_KEY' əlavə edin.")

def encode_image(image):
    buffered = io.BytesIO()
    # Keyfiyyəti maksimum edirik ki, xırda rəqəmlər aydın görünsün
    image.save(buffered, format="JPEG", quality=100)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

st.title("📑 Borderpoint | CMR & İnvoys Master")
st.caption("Bütün qrafalar üzrə nöqtə atışı analiz və dəqiq HS kod hesablama.")

uploaded_files = st.file_uploader("Sənədləri (CMR, İnvoys) yükləyin", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

all_pages = []
if uploaded_files:
    for file in uploaded_files:
        if file.type == "application/pdf":
            try:
                pdf_images = convert_from_bytes(file.read())
                for idx, img in enumerate(pdf_images):
                    all_pages.append({"img": img, "name": f"{file.name}_p{idx+1}"})
            except:
                st.error(f"{file.name} PDF oxunarkən xəta.")
        else:
            all_pages.append({"img": Image.open(file), "name": file.name})

    if st.button("🚀 Detallı Analizi Başlat", use_container_width=True):
        if not all_pages:
            st.warning("Zəhmət olmasa sənəd yükləyin.")
        else:
            with st.spinner('Border sənin üçün santimetr-santimetr analiz edir...'):
                try:
                    # Sənin verdiyin nümunələr əsasında hazırlanmış MAXİMAL DƏQİQ PROMPT
                    prompt = """
                    Sən peşəkar gömrük brokerisən. Sənədləri (CMR və İnvoys) dərindən analiz et.
                    
                    1. CMR QRAFALARI ÜÇÜN QAYDA:
                       Aşağıdakı qrafaları mütləq nöqtə atışı tap:
                       - sender (Qrafa 1): Ad və tam ünvan
                       - receiver (Qrafa 2): Ad və tam ünvan
                       - loading_place (Qrafa 4): Yüklənmə yeri
                       - cmr_date (Qrafa 4): Yüklənmə tarixi
                       - documents (Qrafa 5): Əlavə sənədlər (İnvoys No, Tarix)
                       - truck_no (Qrafa 18): Maşın nömrəsi (və ya qoşqu)
                       - sender_country (Qrafa 15): Göndərən ölkə kodu (məs. TR)
                    
                    2. HS KODLAR, ÇƏKİ VƏ QİYMƏT ÜÇÜN QAYDA (ÇOX VACİB):
                       Sənəd image_7.png, image_8.png, image_9.png nümunələrinə bənzəyir.
                       - Cədvəldə "GTIP" və ya "G.T.İ.P." sütununu tap.
                       - DİQQƏT: HS kodları iki sətirdə yazılıb (məs. '6106,90' və '90,00,00'). Onları birləşdirərək vahid 10 rəqəmli kod et (məs. '6106909000').
                       - "BRÜT KG", "NET KG" və "KAL.FİYAT" sütunlarını tap. Rəqəmləri tam dəqiqliyi ilə götür. Vergülləri nöqtəyə çevir.
                    
                    JSON strukturunu mütləq gözlə:
                    {
                      "cmr": {"sender": "", "receiver": "", "truck": "", "inv_info": "", "loading": "", "country": "", "date": ""},
                      "items": [{"hs_code": "10 rəqəm", "net": 0.0, "gross": 0.0, "price": 0.0, "desc": "məhsul adı"}]
                    }
                    items siyahısına hər mal sətirini daxil et.
                    """
                    
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
                    st.success("✅ Border işini tamamladı!")
                except Exception as e:
                    st.error(f"Analiz zamanı xəta: {e}")

# --- NƏTİCƏLƏR PANELİ ---
if 'res_data' in st.session_state:
    res = st.session_state['res_data']
    cmr = res.get('cmr', {})
    items = res.get('items', [])

    st.header("🚛 CMR Məlumatları (Bəyannamə Qrafaları)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**1. Göndərən:**\n\n{cmr.get('sender', 'Tapılmadı')}")
        st.success(f"**4. Yükləmə Yeri / Tarix:**\n\n{cmr.get('loading', 'Tapılmadı')} / {cmr.get('date', 'N/A')}")
        st.info(f"**15. Ölkə:** {cmr.get('country', 'N/A')}")

    with col2:
        st.info(f"**2. Alıcı:**\n\n{cmr.get('receiver', 'Tapılmadı')}")
        st.warning(f"**18. Maşın No:**\n\n{cmr.get('truck', 'N/A')}")
        st.info(f"**5. Əlavə Sənədlər:**\n\n{cmr.get('inv_info', 'Tapılmadı')}")

    st.divider()
    
    # MALLAR VƏ HS KOD HESABLAMALARI
    if items:
        st.header("📊 Mal Hesabatı (XİF MN üzrə Toplanmış)")
        df = pd.DataFrame(items)
        
        # Sütun adlarını standartlaşdırırıq
        name_map = {'hs_code': 'hs_code', 'net_weight': 'net', 'gross_weight': 'gross', 'price': 'price', 'description': 'desc'}
        df = df.rename(columns=name_map)

        # Məcburi sütunları yoxlayırıq
        for col in ['hs_code', 'net', 'gross', 'price', 'desc']:
            if col not in df.columns:
                df[col] = 0 if col != 'desc' and col != 'hs_code' else "N/A"

        # Rəqəmləri təmizləyirik (yalnız rəqəm və nöqtə)
        for col in ['net', 'gross', 'price']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        # Eyni HS kodları mütləq cəmləyirik
        summary = df.groupby('hs_code').agg({
            'desc': 'first',
            'net': 'sum',
            'gross': 'sum',
            'price': 'sum'
        }).reset_index()

        st.table(summary)

        # Yekun Cəmlər (Metric kartları)
        st.subheader("💰 Yekun Hesablar")
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Netto", f"{summary['net'].sum():,.2f} kq")
        m2.metric("Toplam Brutto", f"{summary['gross_weight'].sum():,.2f} kq" if 'gross_weight' in summary.columns else f"{summary['gross'].sum():,.2f} kq")
        m3.metric("Toplam Qiymət", f"{summary['price'].sum():,.2f}")
    else:
        st.warning("İnvoysda heç bir mal məlumatı tapılmadı.")

    #⚡ MASTER JS KODU (Portala ötürmək üçün)
    st.divider()
    st.subheader("⚡ E-Customs Master Doldurma Kodu")
    js_code = f"""
    (function() {{
        const d = {{
            s: "{cmr.get('sender', '')[:50]}",
            r: "{cmr.get('receiver', '')[:50]}",
            t: "{cmr.get('truck', '')}",
            i: "{cmr.get('inv_info', '')}"
        }};
        document.querySelector('[id*="CONSIGNOR"]').value = d.s;
        document.querySelector('[id*="CONSIGNEE"]').value = d.r;
        document.querySelector('[id*="TRANSPORT_REG"]').value = d.t;
        document.querySelector('[id*="INVOICE_NUMBER"]').value = d.i;
        alert('Border: Məlumatlar hazırdır!');
    }})();
    """.replace('\n', ' ')
    st.code(js_code, language="javascript")
else:
    st.info("Sənəd gözləyirəm, Border...")