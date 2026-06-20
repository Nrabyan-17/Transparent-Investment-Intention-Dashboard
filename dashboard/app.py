"""
app.py
======
Main entry point untuk Transparent Investment Intention Dashboard.

Run:
    streamlit run dashboard/app.py

Penulis: Naufal Rizki Abyan (23082010235)
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="Transparent Investment Intention Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        background: linear-gradient(90deg, #2E86AB 0%, #E63946 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subheader {
        color: #666;
        font-size: 1.1em;
        margin-top: 0;
    }
    .info-box {
        background-color: #f0f7ff;
        border-left: 4px solid #2E86AB;
        padding: 16px;
        border-radius: 4px;
        margin: 16px 0;
    }
    .stat-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .stat-number {
        font-size: 2em;
        font-weight: bold;
        color: #2c3e50;
    }
    .stat-label {
        font-size: 0.9em;
        color: #666;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📊 Transparent Investment Intention</div>',
            unsafe_allow_html=True)
st.markdown('<div class="subheader">Decision Support System dengan Explainable AI + Knowledge-Based Rules</div>',
            unsafe_allow_html=True)

st.markdown("---")

# Intro
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### 🎯 Tentang Sistem Ini

    Sistem ini memprediksi **risk profile investor** berdasarkan perilaku transaksi saham,
    dengan fokus pada **transparansi keputusan**. Sistem mengintegrasikan tiga layer:

    **1. Machine Learning Layer** — Random Forest classifier dengan F1-macro ~0.43

    **2. Statistical Explanation Layer (SHAP)** — Menjelaskan kontribusi setiap fitur
    secara matematis (Shapley values dari game theory)

    **3. Domain Knowledge Layer (KBS)** — 15 rules berbasis literatur akademis
    (Modern Portfolio Theory, Behavioral Finance, MiFID II) untuk natural language explanation

    Kombinasi 3 layer ini menghasilkan **transparency yang superior** dibanding
    pendekatan single-method.
    """)

with col2:
    st.markdown("### 📚 Referensi Akademis")
    st.info("""
    **Theoretical Foundation:**
    - Markowitz (1952) - MPT
    - Shefrin & Statman (1985) - Disposition Effect
    - Kahneman & Tversky (1979) - Prospect Theory
    - Lundberg & Lee (2017) - SHAP
    - MiFID II Article 25
    """)

# Stats
st.markdown("---")
st.markdown("### 📈 Statistik Sistem")

s1, s2, s3, s4 = st.columns(4)

with s1:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-number">13,611</div>
        <div class="stat-label">Total Customer</div>
    </div>
    """, unsafe_allow_html=True)

with s2:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-number">345K+</div>
        <div class="stat-label">Transaksi Saham</div>
    </div>
    """, unsafe_allow_html=True)

with s3:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-number">33</div>
        <div class="stat-label">Features ML</div>
    </div>
    """, unsafe_allow_html=True)

with s4:
    st.markdown("""
    <div class="stat-box">
        <div class="stat-number">15</div>
        <div class="stat-label">KBS Rules</div>
    </div>
    """, unsafe_allow_html=True)

# Navigation
st.markdown("---")
st.markdown("### 🗺️ Navigasi Dashboard")

nav1, nav2 = st.columns(2)

with nav1:
    st.markdown("""
    **📊 1. Overview**
    > Eksplorasi dataset, distribusi target variable, dan performance model

    **🎯 2. Prediction**
    > Prediksi risk profile untuk customer existing atau input manual
    """)

with nav2:
    st.markdown("""
    **🔍 3. SHAP Explanation**
    > Statistical explainability dengan SHAP values (global & local)

    **⚖️ 4. KBS Rules**
    > 15 rules berbasis domain knowledge dengan referensi akademis
    """)

st.info("💡 **Gunakan sidebar di sebelah kiri** untuk navigasi antar halaman.")

# DSS framework
st.markdown("---")
with st.expander("ℹ️ Tentang Decision Support System Framework"):
    st.markdown("""
    Dashboard ini mengikuti **DSS framework** dari Sprague & Carlson (1982)
    yang terdiri dari 3 subsystem:

    | Subsystem | Implementasi |
    |-----------|--------------|
    | **Data Subsystem** | Halaman Overview - menampilkan dataset statistics |
    | **Model Subsystem** | ML Model + SHAP + KBS Rules |
    | **Dialog/UI Subsystem** | Streamlit interface (this dashboard) |

    **Karakteristik DSS yang dipenuhi:**
    - ✅ Mendukung **semi-structured decisions** (risk profiling)
    - ✅ Memberikan **what-if analysis** (override manual features)
    - ✅ Menyediakan **multiple explanation modalities** (SHAP + KBS)
    - ✅ **User-friendly** untuk decision maker non-teknis
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9em; margin-top: 30px;'>
    <b>Transparent Investment Intention Analysis</b><br>
    Naufal Rizki Abyan (23082010235) | Universitas Pembangunan Nasional "Veteran" Jawa Timur<br>
    Magang Riset 2026
</div>
""", unsafe_allow_html=True)