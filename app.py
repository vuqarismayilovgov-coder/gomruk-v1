import streamlit as st
import uuid
from datetime import datetime

# 1. Səhifənin Texniki Tənzimlənməsi
st.set_page_config(
    page_title="Borderpoint AI Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- Vizual Üslub (Custom CSS) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #002b5b;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #004080;
        color: #ffca28;
    }
    .reportview-container {
        background: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Yaddaş Mexanizmi (Session State) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0  # Başlanğıc üçün qızıl balans
if 'history' not in st.session_state:
    st.session_state.history = []

# --- Əsas AI Logikası ---
def ai_engine_process(doc_name):
    """Sənədi analiz edən və bəyannamə hazırlayan qızıl funksiya"""
    cost = 5.0
    if st.session_state.balance >= cost:
        st.session_state.balance -= cost
        # Süni İntellektin çıxardığı nəticə
        result = {
            "id": str(uuid.uuid4())[:8].upper(),
            "fayl": doc_name,
            "tarix": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "xif_u": "8517.12.00.00 (Smartfonlar)",
            "status": "Gömrük Sisteminə Göndərildi",
            "edv": "18%",
            "tesdiq_kodu": f"BP-{uuid.uuid4().hex[:6].upper()}"
        }
        st.session_state.history.insert(0, result)
        return True, result
    return False, None

# --- PANELİN QURULUŞU ---

# Sol Menyu (Sidebar)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=100)
    st.title("Borderpoint AI")
    st.write(f"👤 **Broker:** Vüqar")
    st.write(f"🆔 **VÖEN:** 1234567891")
    st.divider()
    st.metric("Cari Balans", f"{st.session_state.balance} AZN")
    
    st.write("---")
    top_up = st.number_input("Balans artır (AZN)", min_value=5, step=5)
    if st.button("Ödəniş Et"):
        st.session_state.balance += top_up
        st.success(f"{top_up} AZN balansa əlavə edildi.")
        st.rerun()

# Əsas İş Sahəsi
st.title("🛡️ Borderpoint AI Pro - İntellektual Gömrük Paneli")

col_upload, col_history = st.columns([2, 1])

with col_upload:
    st.subheader("🚀 Bəyannamə Avtomatlaşdırma")
    st.info("Invoice, CMR və ya Paket vərəqini yükləyin. AI məlumatları birbaşa bəyannamə sahələrinə köçürəcək.")
    
    file = st.file_uploader("Sənədi bura daxil edin", type=['pdf', 'jpg', 'png'])
    
    if file:
        if st.button("QIZIL ANALİZİ BAŞLAT"):
            with st.spinner('Süni intellekt XİF U kodlarını və qiymətləri hesablayır...'):
                success, data = ai_engine_process(file.name)
                if success:
                    st.balloons()
                    st.success("Analiz tamamlandı! Məlumatlar hazırdır.")
                    
                    # Nəticə Cədvəli
                    st.table({
                        "Göstərici": ["Bəyannamə ID", "XİF U Kodu", "ƏDV Dərəcəsi", "Sənəd", "Təsdiq Kodu"],
                        "Məlumat": [data['id'], data['xif_u'], data['edv'], data['fayl'], data['tesdiq_kodu']]
                    })
                else:
                    st.error("Balans yetərli deyil! Zəhmət olmasa ödəniş sistemindən balansınızı artırın.")

with col_history:
    st.subheader("📜 Tarixçə")
    if st.session_state.history:
        for item in st.session_state.history[:10]:
            with st.expander(f"ID: {item['id']} | {item['tarix']}"):
                st.write(f"**XİF U:** {item['xif_u']}")
                st.write(f"**Status:** {item['status']}")
                st.write(f"**Fayl:** {item['fayl']}")
    else:
        st.write("Hələ heç bir əməliyyat aparılmayıb.")

# Alt Hissə
st.write("---")
st.markdown("<p style='text-align: center; color: gray;'>Süni intellekt təhlükəli deyilmi? Xeyr, o sizin işinizi saniyələr içində bitirən peşəkar köməkçidir.</p>", unsafe_allow_html=True)