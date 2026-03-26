import streamlit as st
import uuid
from datetime import datetime

# 1. Səhifə Tənzimləmələri
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
    }
    .stButton>button:hover {
        border: 2px solid #ffca28;
        color: #ffca28;
    }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        border-left: 5px solid #002b5b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Yaddaş Mexanizmi ---
if 'balance' not in st.session_state:
    st.session_state.balance = 150.0
if 'history' not in st.session_state:
    st.session_state.history = []

# --- Genişləndirilmiş AI Analiz Motoru ---
def deep_ai_analysis(file_name, doc_type):
    """CMR, Invoice, İxrac və Mənşə sənədlərini analiz edən əsas funksiya"""
    cost = 7.0  # Kompleks analiz üçün xidmət haqqı
    
    if st.session_state.balance < cost:
        return False, None

    st.session_state.balance -= cost
    
    # Sənəd tipinə görə fərqli AI nəticələri
    analysis_results = {
        "Invoice": {"detal": "Qiymət və Valyuta yoxlanıldı", "kod": "USD 12,500"},
        "CMR": {"detal": "Daşıyıcı və Avtomobil nömrəsi tapıldı", "kod": "99-AB-000"},
        "İxrac Bəyannaməsi": {"detal": "Çıxış gömrük postu təyin edildi", "kod": "Gömrük-24"},
        "Mənşə Sertifikatı": {"detal": "İstehsalçı ölkə təsdiqləndi", "kod": "Azerbaijan (Form A)"}
    }
    
    res = analysis_results.get(doc_type, {"detal": "Ümumi analiz", "kod": "N/A"})