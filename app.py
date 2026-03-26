import streamlit as st
import uuid
from datetime import datetime

# 1. Səhifə Ayarları
st.set_page_config(
    page_title="Borderpoint AI Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- CSS Stil Dizaynı ---
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
        border: 2px solid #ffca28;
        color: #ffca28;
    }
    .status-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        border-left: 6px solid #002b5b;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Məlumat Yaddaşı ---
if 'balance' not in st.session_state:
    st.session_state.balance = 200.0
if 'history' not in st.session_state:
    st.session_state.history = []

# --- AI Analiz Motoru ---
def run_ai_analysis(file_name, doc_type):
    cost = 10.0  # Hər analiz üçün xidmət haqqı
    if st.session_state.balance >= cost:
        st.session_state.balance -= cost
        
        # Sənəd növlərinə görə simulyasiya edilən AI datası
        results = {
            "Invoice": {"info": "Qiymət: 15,200 EUR", "extra": "Satıcı: Global Export GmbH"},
            "CMR": {"info": "Maşın: 99-ZY-123", "extra": "Yük: Sənaye avadanlığı"},
            "İxrac Bəyannaməsi": {"info": "Kod: 100010", "extra": "Post: Şıxlı"},
            "Mənşə Sertifikatı": {"info": "Növ: Form A", "extra": "Ölkə: Almaniya"}
        }
        
        data = results.get(doc_type, {"info": "Analiz uğurlu", "extra": "Məlumat tapıldı"})
        
        entry = {
            "id": f"BP-{uuid.uuid4().hex[:6].upper()}",
            "fayl": file_name,
            "növ": doc_type,
            "tarix": datetime.now().strftime("%H:%M | %d.%m.%Y"),
            "detal": data["info"],
            "əlavə": data["extra"]
        }
        st.session_state.history.insert(0, entry)
        return True, entry
    return False, None

# --- İNTERFEYS QURULUŞU ---

# Sol Panel (Sidebar)
with st.sidebar:
    st.header("🛡️ Borderpoint")
    st.write("---")
    st.markdown(f"**İstifadəçi:** Vüqar (Broker)")
    st.markdown(f"**VÖEN:** 1234567891")
    st.metric("Cari Balans", f"{st.session_state.balance} AZN")
    
    st.write("---")
    top_up = st.number_input("Balansı artır", min_value=10, step=10)
    if st.button("Ödəniş Sistemi ilə Yüklə"):
        st.session_state.balance += top_up
        st.rerun()
    
    st.write("---")
    st.caption("Süni intellekt təhlükəli deyilmi? Xeyr, o sizin sənədlərinizi saniyələr içində emal edir.")

# Əsas Panel
st.title("🛡️ Borderpoint AI Pro: İntellektual Gömrük Paneli")

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📝 Sənədin Təyinatı və Analizi")
    
    # Sənəd Növü Seçimi
    doc_choice = st.selectbox(
        "Analiz ediləcək sənədi seçin:",
        ["Invoice", "CMR", "İxrac Bəyannaməsi", "Mənşə Sertifikatı"]
    )
    
    # Fayl yükləmə
    file = st.file_uploader(f"{doc_choice} yükləyin (PDF, JPG, PNG)", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if file:
        if st.button(f"{doc_choice} Analizini Başlat"):
            with st.spinner("AI sənədi skan edir..."):
                ok, result_data = run_ai_analysis(file.name, doc_choice)
                if ok:
                    st.balloons()
                    st.success(f"Analiz Tamamlandı! (ID: {result_data['id']})")
                    
                    # Nəticə Kartı
                    st.markdown(f"""
                    <div class="status-card">
                        <h4>✅ {result_data['növ']} Məlumatları</h4>
                        <p><b>Əsas:</b> {result_data['detal']}</p>
                        <p><b>Əlavə:</b> {result_data['əlavə']}</p>
                        <p><b>Tarix:</b> {result_data['tarix']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Balans yetərli deyil! Zəhmət olmasa VÖEN hesabınızı artırın.")

with c2:
    st.subheader("📜 Son Əməliyyatlar")
    if st.session_state.history:
        for item in st.session_state.history[:10]:
            with st.expander(f"{item['id']} | {item['növ']}"):
                st.write(f"📁 {item['fayl']}")
                st.write(f"📅 {item['tarix']}")
                st.write(f"🔍 {item['detal']}")
    else:
        st.info("Hələ ki, arxivdə məlumat yoxdur.")

st.divider()
st.caption("© 2026 Borderpoint AI Pro - Bütün hüquqlar qorunur.")