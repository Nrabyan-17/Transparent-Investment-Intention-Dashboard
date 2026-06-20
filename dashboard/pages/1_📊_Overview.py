"""
1_📊_Overview.py
================
Halaman Overview - Transparency Algorithm for Investment Intentions.

Reframed berdasarkan revisi:
- Risk Level sebagai proxy Investment Intention (revealed preference)
- KPI metrics di header (4 cols)
- Section "Why Transparency Matters"
- Intention Strength framework dari confidence score
- Layout balanced, complete content

Penulis: Naufal Rizki Abyan (23082010235)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.helpers import (
    load_metadata, load_train_data, load_test_data,
    load_label_encoder, load_model,
    RISK_COLORS, RISK_DESCRIPTIONS
)

st.set_page_config(
    page_title="Overview - Transparency Algorithm for Investment Intentions",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# HEADER — Reframed dengan judul yang lebih kuat
# ============================================================

st.title("📊 Overview – Transparency Algorithm for Investment Intentions")
st.markdown("**Explainable Decision Support System untuk Prediksi Niat Investasi Investor Retail**")

# Narasi proxy
st.markdown("""
<div style="background-color: #EAF3FF; border-left: 4px solid #2E86AB;
            padding: 16px; border-radius: 4px; margin: 16px 0;">
    <strong style="color: #000000;">📌 Catatan Konseptual:</strong>
    <span style="color: #000000;">
        Sistem ini memprediksi <strong>Risk Level</strong> sebagai <strong>proxy untuk Investment Intention</strong>
        (Behavioral Finance — Shefrin & Statman, 1985). Risk Level customer di dataset FAR-Trans merupakan
        <em>revealed preference</em> dari pola transaksi nyata, yang dianggap proxy paling reliable untuk
        future investment intention dibanding stated preference (questionnaire).
    </span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================

with st.spinner("Loading data..."):
    metadata = load_metadata()
    X_train, y_train = load_train_data()
    X_test, y_test = load_test_data()
    le = load_label_encoder()
    label_names = list(le.classes_)
    best_model_name = metadata['best_model']
    best_model_obj = load_model()

# Compute aggregates
y_combined = np.concatenate([y_train, y_test])
total = len(y_combined)
metrics_df = pd.DataFrame(metadata['metrics_all']).set_index('Model')
best_acc = metrics_df.loc[best_model_name, 'Test Accuracy']
best_f1 = metrics_df.loc[best_model_name, 'F1-Score (macro)']

# ============================================================
# SECTION 1: KPI METRICS — 4 kolom st.metric
# ============================================================

st.markdown("---")
st.subheader("🎯 Key Performance Indicators")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        label="Total Customers (Samples)",
        value=f"{total:,}",
        help="Total customer trading saham dengan label valid (training + test set)"
    )

with kpi2:
    st.metric(
        label="Best Model & Accuracy",
        value=f"{best_model_name}",
        delta=f"Acc: {best_acc:.2%}",
        help=f"Model terbaik berdasarkan F1-Score macro: {best_f1:.4f}"
    )

with kpi3:
    st.metric(
        label="Total Features",
        value=f"{X_train.shape[1]}",
        delta="33 features (after engineering)",
        help="Setelah feature engineering & encoding dari 4 file CSV FAR-Trans"
    )

with kpi4:
    st.metric(
        label="Explainability Status",
        value="✅ Active",
        delta="SHAP + KBS Rules",
        help="Statistical (SHAP) + Domain Knowledge (15 KBS Rules) terimplementasi"
    )

# ============================================================
# SECTION 2: WHY TRANSPARENCY MATTERS
# ============================================================

st.markdown("---")
st.subheader("💡 Why Transparency Matters")

trans_col1, trans_col2 = st.columns([3, 2])

with trans_col1:
    st.markdown("""
    **Transparansi adalah core value dari sistem ini.** Dalam konteks investasi retail, transparansi
    bukan sekadar "nice-to-have" — melainkan **prasyarat regulatori** (MiFID II Article 25, POJK 22/2023)
    dan **driver utama kepercayaan investor** (Behavioral Finance literature).

    Sistem ini mengintegrasikan **dua layer transparansi** untuk memberikan justifikasi keputusan yang
    dapat diaudit dan dipertanggungjawabkan:
    """)

    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 14px; border-radius: 6px;
                border-left: 3px solid #52B788; margin: 8px 0;">
        <strong style="color: #000000;">🔍 Statistical Layer (SHAP)</strong><br>
        <span style="color: #000000;">
            Menjelaskan <em>kontribusi matematis</em> setiap fitur ke prediksi via Shapley values
            (Lundberg & Lee, 2017). Konsisten dengan 3 properti: local accuracy, missingness, consistency.
        </span>
    </div>

    <div style="background-color: #f8f9fa; padding: 14px; border-radius: 6px;
                border-left: 3px solid #F4A261; margin: 8px 0;">
        <strong style="color: #000000;">⚖️ Domain Knowledge Layer (KBS Rules)</strong><br>
        <span style="color: #000000;">
            Memberikan <em>natural language explanation</em> dengan 15 rules berbasis literatur akademis
        (Modern Portfolio Theory, Behavioral Finance, MiFID II). Setiap rule punya referensi yang jelas.
        </span>
    </div>
    """, unsafe_allow_html=True)

with trans_col2:
    st.markdown("**🎯 Manfaat untuk Stakeholder:**")
    st.markdown("""
    <div style="background-color: #ffffff; border: 1px solid #e0e0e0;
                padding: 16px; border-radius: 6px;">
        <strong style="color: #000000;">👤 Untuk Investor:</strong><br>
        <span style="color: #555;">Memahami <em>kenapa</em> diklasifikasikan ke profil
        tertentu → meningkatkan trust & investment intention</span>
        <br><br>
        <strong style="color: #000000;">🏦 Untuk Bank/LK:</strong><br>
        <span style="color: #555;">Justifikasi keputusan profiling yang dapat diaudit
        → compliance MiFID II / POJK 22/2023</span>
        <br><br>
        <strong style="color: #000000;">👨‍💼 Untuk Regulator (OJK):</strong><br>
        <span style="color: #555;">Audit trail yang jelas → reduce regulatory risk</span>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECTION 3: INTENTION STRENGTH FRAMEWORK (elemen C)
# ============================================================

st.markdown("---")
st.subheader("📏 Intention Strength Framework")

st.markdown("""
Sistem ini memprediksi Risk Profile nasabah sebagai proxy Investment Intention. Selain itu, sistem juga mengukur kekuatan (strength) dari prediksi tersebut berdasarkan confidence score model.
""")

strength_col1, strength_col2, strength_col3 = st.columns(3)

with strength_col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                color: white; padding: 16px; border-radius: 8px; min-height: 140px;">
        <div style="font-size: 1.4em; font-weight: bold;">💪 STRONG INTENTION</div>
        <div style="font-size: 0.85em; opacity: 0.9; margin-top: 4px;">
            Confidence: <strong>> 70%</strong>
        </div>
        <div style="font-size: 0.85em; margin-top: 8px;">
            Model sangat yakin. Pola transaksi customer
            sangat konsisten dengan profil yang diprediksi.
            <em>Decision-ready.</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

with strength_col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f39c12 0%, #f4a261 100%);
                color: white; padding: 16px; border-radius: 8px; min-height: 140px;">
        <div style="font-size: 1.4em; font-weight: bold;">⚖️ MODERATE INTENTION</div>
        <div style="font-size: 0.85em; opacity: 0.9; margin-top: 4px;">
            Confidence: <strong>40% – 70%</strong>
        </div>
        <div style="font-size: 0.85em; margin-top: 8px;">
            Model cukup yakin. Pola customer ambigu antara
            2 profil. <em>Recommend SHAP & KBS check</em>
            sebelum keputusan.
        </div>
    </div>
    """, unsafe_allow_html=True)

with strength_col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e74c3c 0%, #ec7063 100%);
                color: white; padding: 16px; border-radius: 8px; min-height: 140px;">
        <div style="font-size: 1.4em; font-weight: bold;">❓ UNCLEAR INTENTION</div>
        <div style="font-size: 0.85em; opacity: 0.9; margin-top: 4px;">
            Confidence: <strong>< 40%</strong>
        </div>
        <div style="font-size: 0.85em; margin-top: 8px;">
            Model tidak yakin. Pola customer mixed atau
            outlier. <em>Wajib human review</em> oleh
            financial advisor.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECTION 4: DISTRIBUSI TARGET (Reframed)
# ============================================================

st.markdown("---")
st.subheader("🎯 Distribusi Risk Profile (Proxy Investment Intention)")

counts = {label_names[i]: int((y_combined == i).sum()) for i in range(len(label_names))}

dist_col1, dist_col2 = st.columns([2, 1])

with dist_col1:
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = [RISK_COLORS[name] for name in counts.keys()]
    wedges, texts, autotexts = ax.pie(
        counts.values(), labels=counts.keys(),
        autopct='%1.1f%%', colors=colors, startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    for at in autotexts:
        at.set_color('white')
        at.set_fontweight('bold')
    ax.set_title('Distribusi 4 Investment Intention Categories', fontsize=14, fontweight='bold')
    st.pyplot(fig)
    plt.close()

with dist_col2:
    st.markdown("**📋 Distribusi Detail:**")
    for name, count in counts.items():
        pct = count / total * 100
        color = RISK_COLORS[name]
        st.markdown(f"""
        <div style="background-color: {color}20; border-left: 4px solid {color};
                    padding: 10px; border-radius: 4px; margin: 6px 0;">
            <strong style="color: {color};">{name}</strong><br>
            <span style="font-size: 1.3em; font-weight: bold;">{count:,}</span>
            <span style="color: #666;"> ({pct:.1f}%)</span>
        </div>
        """, unsafe_allow_html=True)

# Class imbalance explanation - improved
imbalance_ratio = max(counts.values()) / min(counts.values())
majority_class = max(counts, key=counts.get)
minority_class = min(counts, key=counts.get)

st.markdown(f"""
<div style="background-color: #fff8e1; border-left: 4px solid #ff9800;
            padding: 14px; border-radius: 4px; margin: 14px 0;">
    <strong>⚠️ Class Imbalance Handling</strong><br>
    <span style="color: #555;">
        Ratio: <strong>{imbalance_ratio:.2f}:1</strong>
        (Majority: <strong>{majority_class}</strong> {counts[majority_class]:,} samples,
        Minority: <strong>{minority_class}</strong> {counts[minority_class]:,} samples).
        <br><br>
        <strong>Strategi penanganan:</strong> Class imbalance moderate (ratio < 5:1) ditangani dengan
        <code>class_weight='balanced'</code> di model training. Pendekatan ini memberi <em>higher weight</em>
        untuk minority class saat optimization, tanpa perlu oversampling (SMOTE) yang dapat menyebabkan
        overfitting pada pattern sintetis.
    </span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SECTION 5: MODEL PERFORMANCE SUMMARY (Compact)
# ============================================================

st.markdown("---")
st.subheader("🏆 Model Performance Summary")

st.markdown(f"""
**Best Model:** <span style="background-color: #27ae6020; color: #27ae60;
padding: 4px 12px; border-radius: 12px; font-weight: bold;">{best_model_name}</span>
""", unsafe_allow_html=True)

perf_col1, perf_col2 = st.columns([3, 2])

with perf_col1:
    # Highlight top performance metrics
    fig, ax = plt.subplots(figsize=(10, 4))
    metrics_to_plot = ['Test Accuracy', 'F1-Score (macro)']
    x = np.arange(len(metrics_to_plot))
    width = 0.25
    colors_models = ['#3498db', '#2ecc71', '#e74c3c']

    for i, model_name in enumerate(metrics_df.index):
        values = [metrics_df.loc[model_name, m] for m in metrics_to_plot]
        bars = ax.bar(x + i * width, values, width, label=model_name,
                    color=colors_models[i], alpha=0.85)
        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', fontsize=9, fontweight='bold')

    ax.set_ylabel('Score')
    ax.set_title('Top Models: Accuracy vs F1-Score (Macro)', fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics_to_plot)
    ax.legend(loc='lower right')
    ax.set_ylim(0, max([metrics_df[m].max() for m in metrics_to_plot]) * 1.15)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with perf_col2:
    st.markdown("**🎯 Best Model Highlights:**")
    
    # Get all metrics for best model
    best_metrics = metrics_df.loc[best_model_name]
    
    st.markdown(f"""
    <div style="background-color: #ffffff; border: 1px solid #e0e0e0;
                padding: 16px; border-radius: 8px;">
        <div style="margin: 6px 0;">
            <span style="color: #555;">Test Accuracy:</span>
            <strong style="float: right; color: #27ae60;">{best_metrics['Test Accuracy']:.4f}</strong>
        </div>
        <div style="margin: 6px 0;">
            <span style="color: #555;">F1-Score (macro):</span>
            <strong style="float: right; color: #27ae60;">{best_metrics['F1-Score (macro)']:.4f}</strong>
        </div>
        <div style="margin: 6px 0;">
            <span style="color: #555;">Precision (macro):</span>
            <strong style="float: right; color: #27ae60;">{best_metrics['Precision (macro)']:.4f}</strong>
        </div>
        <div style="margin: 6px 0;">
            <span style="color: #555;">Recall (macro):</span>
            <strong style="float: right; color: #27ae60;">{best_metrics['Recall (macro)']:.4f}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("📌 Lihat halaman lain untuk analisis mendalam per prediksi.")

# ============================================================
# SECTION 6: TOP FEATURES PREVIEW (Compact)
# ============================================================

st.markdown("---")
st.subheader("🔝 Top 5 Most Important Features (Global Importance)")

if hasattr(best_model_obj, 'feature_importances_'):
    feat_importance = pd.Series(
        best_model_obj.feature_importances_,
        index=X_train.columns
    ).sort_values(ascending=False).head(5)

    feat_col1, feat_col2 = st.columns([3, 2])

    with feat_col1:
        fig, ax = plt.subplots(figsize=(10, 4))
        colors_grad = plt.cm.viridis(np.linspace(0.3, 0.9, len(feat_importance)))
        bars = ax.barh(range(len(feat_importance)), feat_importance.values[::-1], color=colors_grad)
        for bar, val in zip(bars, feat_importance.values[::-1]):
            ax.text(val + 0.001, bar.get_y() + bar.get_height()/2,
                    f'{val:.4f}', va='center', fontsize=10, fontweight='bold')
        ax.set_yticks(range(len(feat_importance)))
        ax.set_yticklabels(feat_importance.index.tolist()[::-1])
        ax.set_xlabel('Feature Importance')
        ax.set_title(f'Top 5 Features ({best_model_name})', fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with feat_col2:
        st.markdown("**💼 Business Interpretation:**")
        top_5 = feat_importance.head(5)
        for i, (feat, val) in enumerate(top_5.items(), 1):
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 8px 12px;
                        border-radius: 4px; margin: 4px 0; font-size: 0.9em;">
                <strong>#{i}.</strong> <code>{feat}</code>
                <span style="float: right; color: #888;">{val:.4f}</span>
            </div>
            """, unsafe_allow_html=True)

        st.caption("💡 Detail SHAP-based explanation tersedia di halaman **🔍 SHAP Explanation**.")

# ============================================================
# SECTION 7: RISK LEVEL DESCRIPTIONS (Reframed)
# ============================================================

st.markdown("---")
st.subheader("📖 4 Investment Intention Categories (Risk Profiles)")

risk_cols = st.columns(4)
for idx, (name, desc) in enumerate(RISK_DESCRIPTIONS.items()):
    with risk_cols[idx]:
        color = RISK_COLORS[name]
        st.markdown(f"""
        <div style="background-color: {color}15; border-top: 4px solid {color};
                    padding: 16px; border-radius: 4px; min-height: 160px;">
            <strong style="color: {color}; font-size: 1.1em;">{name}</strong>
            <p style="margin-top: 8px; font-size: 0.88em; color: #444;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# SECTION 8: KEY BUSINESS INSIGHTS
# ============================================================

st.markdown("---")
st.subheader("💼 Key Business Insights")

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    st.markdown("""
    <div style="background-color: #e8f5e9; padding: 16px; border-radius: 8px;
                border-left: 4px solid #4caf50;">
        <strong style="color: #2e7d32;">📈 Insight 1: Capacity is King</strong>
        <p style="color: #555; margin-top: 6px; font-size: 0.92em;">
            <code>investmentCapacity</code> dan <code>total_invested</code> adalah top predictors —
            sejalan dengan MPT (Markowitz, 1952) yang menyatakan kapasitas modal sebagai
            constraint utama dalam portfolio allocation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #fff8e1; padding: 16px; border-radius: 8px;
                border-left: 4px solid #ff9800; margin-top: 12px;">
        <strong style="color: #f57c00;">⚖️ Insight 2: Behavioral Patterns Matter</strong>
        <p style="color: #555; margin-top: 6px; font-size: 0.92em;">
            <code>buy_ratio</code> dan <code>avg_days_between_transactions</code> menunjukkan
            <em>disposition effect</em> (Shefrin & Statman, 1985) — investor cenderung
            hold winner dan sell loser, yang dapat diidentifikasi dari pola transaksi.
        </p>
    </div>
    """, unsafe_allow_html=True)

with insights_col2:
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 16px; border-radius: 8px;
                border-left: 4px solid #2196f3;">
        <strong style="color: #1565c0;">🎨 Insight 3: Diversification Signals</strong>
        <p style="color: #555; margin-top: 6px; font-size: 0.92em;">
            <code>unique_stocks_traded</code> dan <code>unique_sectors_traded</code>
            adalah indikator kuat profil Balanced/Aggressive — sesuai prinsip diversifikasi MPT.
            Investor diversified menunjukkan sophistication yang lebih tinggi.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #fce4ec; padding: 16px; border-radius: 8px;
                border-left: 4px solid #e91e63; margin-top: 12px;">
        <strong style="color: #ad1457;">🔍 Insight 4: Hybrid Transparency Works</strong>
        <p style="color: #555; margin-top: 6px; font-size: 0.92em;">
            Kombinasi SHAP (statistical) + KBS Rules (domain) memberikan
            <em>validation cross-check</em> — bila keduanya konsisten = high confidence prediction;
            bila conflict = flag untuk human review (signature kontribusi proyek ini).
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# FOOTER — Metadata: data source, framework, references
# ============================================================

st.markdown("---")

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("""
    **📦 Data Source**
    <div style="font-size: 0.85em; color: #555;">
        <strong>FAR-Trans Dataset</strong><br>
        Sanz-Cruzado et al. (2024)<br>
        Multi-asset financial transactions
    </div>
    """, unsafe_allow_html=True)

with footer_col2:
    st.markdown("""
    **🔧 Framework**
    <div style="font-size: 0.85em; color: #555;">
        <strong>CRISP-DM</strong> (Chapman et al., 2000)<br>
        <strong>DSS Framework</strong> (Sprague & Carlson, 1982)<br>
        <strong>XAI</strong> (Lundberg & Lee, 2017)
    </div>
    """, unsafe_allow_html=True)

with footer_col3:
    st.markdown("""
    **🎯 Project Objective**
    <div style="font-size: 0.85em; color: #555;">
        Membangun <strong>Transparent DSS</strong> untuk
        prediksi Investment Intention investor retail
        dengan dual-layer explainability.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("**Transparent Investment Intention Analysis** | Naufal Rizki Abyan (23082010235) | "
    "Universitas Pembangunan Nasional 'Veteran' Jawa Timur | Magang Riset 2026")