"""
4_⚖️_KBS_Rules.py
=================
Halaman KBS Rules - Domain Knowledge Layer dari DSS.
Versi: matplotlib (original).
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.helpers import (
    load_model, load_label_encoder, get_kbs_function,
    RISK_COLORS, render_risk_badge
)

st.set_page_config(
    page_title="KBS Rules - Transparent Investment",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Knowledge-Based System Rules")
st.markdown("**Domain Knowledge Layer** — 15 rules berbasis literatur akademis "
            "(Modern Portfolio Theory, Behavioral Finance, MiFID II).")

# Guard
if 'last_features_df' not in st.session_state:
    st.warning("⚠️ Belum ada prediksi. Silakan ke halaman **Prediction** dulu.")
    st.stop()

# Load
with st.spinner("Loading KBS engine..."):
    apply_kbs_rules, get_rules_by_category = get_kbs_function()
    model = load_model()
    le = load_label_encoder()
    label_names = list(le.classes_)

last_features_df = st.session_state['last_features_df']
last_pred = st.session_state['last_prediction']
features_series = last_features_df.iloc[0]
pred_label = last_pred['predicted_label']
pred_color = RISK_COLORS[pred_label]

st.markdown(f"""
<div style="background-color: {pred_color}20; border-left: 4px solid {pred_color};
            padding: 16px; border-radius: 4px; margin: 16px 0;">
    <strong>ML Prediksi:</strong>
    <span style="color: {pred_color}; font-weight: bold; font-size: 1.2em;">{pred_label}</span>
    <span style="color: #666;"> (Confidence: {last_pred['confidence']:.1%})</span>
</div>
""", unsafe_allow_html=True)

# Apply rules
triggered_rules = apply_kbs_rules(features_series)
total_rules = 15
triggered_count = len(triggered_rules)

# ============================================================
# SUMMARY
# ============================================================

st.markdown("---")
st.subheader(f"📋 Rules Triggered: {triggered_count} dari {total_rules}")

prog_col1, prog_col2, prog_col3 = st.columns([1, 3, 1])
with prog_col2:
    st.progress(triggered_count / total_rules)
    st.caption(f"**{triggered_count / total_rules:.0%}** dari total rules berlaku untuk customer ini")

# ============================================================
# RULES BY CATEGORY
# ============================================================

st.markdown("---")
st.subheader("📚 Detailed Analysis by Category")

CATEGORY_COLORS = {
    'Capacity Assessment': '#3498db',
    'Trading Behavior': '#e74c3c',
    'Portfolio Diversification': '#9b59b6',
    'Temporal Pattern': '#f39c12',
    'Channel Preference': '#1abc9c',
    'Customer Segment': '#34495e'
}

CATEGORY_ICONS = {
    'Capacity Assessment': '💰',
    'Trading Behavior': '📊',
    'Portfolio Diversification': '🎨',
    'Temporal Pattern': '⏱️',
    'Channel Preference': '📡',
    'Customer Segment': '👥'
}

CATEGORY_REFERENCES = {
    'Capacity Assessment': 'MiFID II Article 25 & Modern Portfolio Theory',
    'Trading Behavior': 'Behavioral Finance (Shefrin & Statman, Kahneman & Tversky)',
    'Portfolio Diversification': 'Modern Portfolio Theory (Markowitz, 1952)',
    'Temporal Pattern': 'Lifecycle Investment Theory',
    'Channel Preference': 'Diffusion of Innovation Theory (Rogers, 2003)',
    'Customer Segment': 'MiFID II Client Categorization'
}

ALL_CATEGORIES = list(CATEGORY_COLORS.keys())
rules_by_cat = get_rules_by_category(triggered_rules)

for category in ALL_CATEGORIES:
    rules_in_cat = rules_by_cat.get(category, [])
    color = CATEGORY_COLORS[category]
    icon = CATEGORY_ICONS[category]
    ref = CATEGORY_REFERENCES[category]
    n_triggered = len(rules_in_cat)

    st.markdown(f"""
    <div style="background-color: {color}15; border-left: 5px solid {color};
                padding: 12px 16px; border-radius: 4px; margin: 20px 0 10px 0;">
        <span style="font-size: 1.3em;">{icon}</span>
        <strong style="color: {color}; font-size: 1.15em; margin-left: 8px;">{category}</strong>
        <span style="background-color: {color}; color: white; padding: 2px 10px;
                     border-radius: 10px; font-size: 0.85em; margin-left: 12px;">
            {n_triggered} triggered
        </span>
        <div style="color: #666; font-size: 0.85em; margin-top: 4px; font-style: italic;">
            Teoritis: {ref}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not rules_in_cat:
        st.caption(f"_Tidak ada rule yang ter-trigger di kategori {category}._")
        continue

    for rule in rules_in_cat:
        st.markdown(f"""
        <div style="background-color: white; border: 1px solid #e0e0e0;
                    border-left: 3px solid {color}; padding: 14px 16px;
                    border-radius: 4px; margin: 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: {color};">{rule['rule_id']}</strong>
                <span style="color: #999; font-size: 0.8em;">Ref: {rule['reference']}</span>
            </div>
            <div style="margin-top: 8px; color: #333;">
                <strong>🔍 Finding:</strong> {rule['finding']}
            </div>
            <div style="margin-top: 4px; color: #555;">
                <strong>💡 Implication:</strong> {rule['implication']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# CONSISTENCY ANALYSIS
# ============================================================

st.markdown("---")
st.subheader("🔬 KBS-ML Consistency Analysis")

imp_signals = {n: 0 for n in label_names}
for rule in triggered_rules:
    impl = rule['implication'].lower()
    for n in label_names:
        if n.lower() in impl:
            imp_signals[n] += 1

analysis_col1, analysis_col2 = st.columns([2, 1])

with analysis_col1:
    if sum(imp_signals.values()) > 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        classes = list(imp_signals.keys())
        counts = list(imp_signals.values())
        colors_bar = [RISK_COLORS[c] for c in classes]
        bars = ax.barh(classes, counts, color=colors_bar)
        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                    str(count), va='center', fontweight='bold')
        if pred_label in classes:
            idx = classes.index(pred_label)
            bars[idx].set_edgecolor('black')
            bars[idx].set_linewidth(3)
        ax.set_xlabel('Number of KBS Rules Pointing to This Class')
        ax.set_title('KBS Rules Implication Distribution', fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("Tidak ada rule yang spesifik mention risk class tertentu.")

with analysis_col2:
    st.markdown("**🔍 Consistency Check:**")
    if sum(imp_signals.values()) > 0:
        kbs_dominant = max(imp_signals, key=imp_signals.get)
        is_consistent = (kbs_dominant == pred_label)
        if is_consistent:
            st.success(f"""
            ✅ **KONSISTEN**

            ML predict: **{pred_label}**
            KBS dominant: **{kbs_dominant}**

            ML dan KBS sepakat — prediksi reliable.
            """)
        else:
            st.warning(f"""
            ⚠️ **POTENTIAL CONFLICT**

            ML predict: **{pred_label}**
            KBS suggest: **{kbs_dominant}**

            Perlu human review.
            """)

    st.info("💡 **Mengapa Penting?** Jika ML dan KBS sepakat → high confidence. "
            "Jika conflict → flag untuk advisor review.")

# ============================================================
# ALL RULES REFERENCE
# ============================================================

st.markdown("---")
with st.expander("📚 Lihat Semua 15 Rules (Reference)"):
    st.markdown("""
    ### Daftar Lengkap 15 Rules dalam 5 Kategori

    **Kategori 1: Capacity Assessment (4 rules)** — *MiFID II Article 25*
    - R1.1: Investment capacity rendah (<30K) → Conservative/Income
    - R1.2: Investment capacity tinggi (>300K) → Aggressive
    - R1.3: Investment capacity menengah (30K-300K) → Balanced/Income
    - R1.4: Tanpa questionnaire → Risk profile tidak reliable

    **Kategori 2: Trading Behavior (4 rules)** — *Behavioral Finance*
    - R2.1: Buy ratio tinggi (>0.65) → Accumulator (Aggressive/Balanced)
    - R2.2: Buy ratio rendah (<0.40) → Profit-taker (Income/Conservative)
    - R2.3: Net seller (sell/buy > 1.5) → Divestasi pattern
    - R2.4: Total invested tinggi (>18.853 EUR) → High exposure

    **Kategori 3: Portfolio Diversification (3 rules)** — *Modern Portfolio Theory*
    - R3.1: Diversified (≥5 stocks) → Mature risk management
    - R3.2: Concentrated (1 stock) → High idiosyncratic risk
    - R3.3: Multi-sector (≥3 sectors) → Cross-sectoral diversification

    **Kategori 4: Temporal Pattern (2 rules)** — *Lifecycle Investment Theory*
    - R4.1: Long-term investor (>1.583 hari) → Consistent
    - R4.2: High-frequency trader (gap <39.7 hari) → Active trader

    **Kategori 5: Channel & Segment (2 rules)** — *Diffusion of Innovation Theory*
    - R5.1: Digital ratio tinggi (>75%) → Tech-savvy
    - R5.2: Premium customer → High net worth

    ### Sumber Threshold

    Semua threshold di-derive dari **statistik dataset training** (Q25/Q75),
    bukan asumsi arbitrary. Detail di `reports/kbs_rules_documentation.md`.
    """)

st.markdown("---")
st.success(f"✅ **KBS Analysis Complete** — {triggered_count} rules ter-trigger untuk customer ini. "
           f"Kombinasi **SHAP + KBS** = Hybrid Transparency Layer (signature proyek ini).")
