import streamlit as st
import uuid
from datetime import datetime

# 1. Səhifə Konfiqurasiyası
st.set_page_config(
    page_title="Borderpoint AI Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- CSS Dizayn ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #002b5b;
        color: white;
        font-weight: bold;
    }
    .main {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State (Məlumat bazası simulyasiyası) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 50.0
if 'history' not in st.session_state:
    st.session_state.history = []

# --- Funksiyalar ---
def process_declaration(doc_name):
    cost = 5.0
    if st.session_state.balance >= cost:
        st.session_state.balance -= cost
        new_decl = {
            "id": str(uuid.uuid4())[:8],
            "sənəd": doc_name,
            "tarix": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "Təsdiqləndi",
            "xif_u": "8517.12.00.00"
        }
        st.session_state.history.insert(0, new_decl)
        return True, new_decl
    return False, None

# --- İNTERFEYS (UI) ---

# Yan Panel
with st.sidebar:
    st.title("🛡️ Borderpoint")
    st.subheader("Broker Paneli")
    st.write("---")
    st.write(f"**VÖEN:** 1234567891")
    st.metric("Cari Balans", f"{st.session_state.balance} AZN")
    
    st.write("---")
    amount = st.number_input("Mədaxil (AZN)", min_value=1, value=10)
    if st.button("Balansı Artır"):
        st.session_state.balance += amount
        st.success(f"{amount} AZN yükləndi!")
        st.rerun()

# Əsas Hissə
st.header("Gömrük Bəyannamələrinin Avtomatlaşdırılması")

left_col, right_col = st.columns([2, 1])

with left_col:
    st.info("Sənədi bura yükləyin, AI dərhal analiz edib bəyannaməni hazırlasın.")
    uploaded_file = st.file_uploader("Sənədi seçin (PDF, JPG, PNG)", type=['pdf', 'png', 'jpg', 'jpeg'])