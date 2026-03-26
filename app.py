import streamlit as st
import uuid
from datetime import datetime

# 1. Səhifə Konfiqurasiyası (Dizayn ayarları)
st.set_page_config(
    page_title="Borderpoint AI Pro",
    page_icon="🛡️",
    layout="wide"
)

# --- CSS ilə Dizaynı Gözəlləşdirək (Tünd Göy Teması) ---
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #002b5b;
        color: white;
    }
    .st-emotion-cache-1cvq2ua {
        background-color: #002b5b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State (Məlumatları yadda saxlamaq üçün) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 50.0  # Başlanğıc balans
if 'history' not in st.session_state:
    st.session_state.history = []

# --- Əsas Funksionallıq ---
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

# Sol Panel (Sidebar)
with st.sidebar:
    st.title("🛡️ Borderpoint")
    st.write(