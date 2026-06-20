"""
3_🔍_SHAP_Explanation.py
========================
Halaman SHAP - Explainability Layer untuk Investment Intention Prediction.

Revisi berdasarkan PDF:
- Judul + konteks Investment Intention
- Waterfall Plot (standard SHAP)
- Top Insights dengan business interpretation (bukan hanya angka)
- Layout dengan tabs
- Bahasa sederhana untuk investor retail
- Tombol navigasi atas & bawah (Kembali ke Prediction + New Prediction)
- Intention Strength badge di context
- Top 10 (bukan 15)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.helpers import (
    load_model, load_label_encoder, load_shap_explainer,
    load_shap_precomputed, load_test_data,
    get_shap_explanation, RISK_COLORS
)

st.set_page_config(
    page_title="SHAP Explanation - Investment Intention",
    page_icon="🔍",
    layout="wide"
)

# ============================================================
# BUSINESS INTERPRETATION DICTIONARY untuk Top Features
# (Untuk PDF revisi point: "Top Insights lebih bernilai")
# ============================================================

FEATURE_BUSINESS_MEANING = {
    'total_invested': {
        'plain': 'Total modal yang sudah diinvestasikan customer',
        'investor_view': 'Modal besar → indikasi profil agresif (toleransi risiko tinggi)',
        'theory': 'Modern Portfolio Theory (Markowitz, 1952) — modal sebagai constraint utama'
    },
    'investmentCapacity': {
        'plain': 'Kategori kapasitas modal customer (<30K hingga >300K EUR)',
        'investor_view': 'Capacity tinggi → bisa afford risk lebih, profil cenderung Aggressive',
        'theory': 'MiFID II Article 25 — suitability assessment'
    },
    'avg_days_between_transactions': {
        'plain': 'Rata-rata jeda hari antar transaksi (frekuensi trading)',
        'investor_view': 'Jeda pendek = active trader (Aggressive), jeda panjang = passive (Conservative)',
        'theory': 'Behavioral Finance — trading frequency sebagai signal risk appetite'
    },
    'total_sold': {
        'plain': 'Total nilai jual semua transaksi customer',
        'investor_view': 'Total sold tinggi vs invested → divestasi/profit-taking pattern',
        'theory': 'Disposition Effect (Shefrin & Statman, 1985)'
    },
    'log_avg_value': {
        'plain': 'Log-transformed rata-rata nilai transaksi (untuk normalisasi)',
        'investor_view': 'Nilai transaksi besar → confidence tinggi di market, profil agresif',
        'theory': 'Behavioral Finance — transaction size sebagai signal commitment'
    },
    'avg_transaction_value': {
        'plain': 'Rata-rata nilai per transaksi customer',
        'investor_view': 'Size transaksi besar → toleransi risiko lebih tinggi per single decision',
        'theory': 'Behavioral Finance — transaction sizing'
    },
    'buy_count': {
        'plain': 'Total jumlah transaksi beli',
        'investor_view': 'Buy count tinggi → akumulator pattern (Aggressive)',
        'theory': 'Disposition Effect — accumulator vs profit-taker behavior'
    },
    'sell_count': {
        'plain': 'Total jumlah transaksi jual',
        'investor_view': 'Sell count tinggi → profit-taker atau panic-seller pattern',
        'theory': 'Disposition Effect (Shefrin & Statman, 1985)'
    },
    'buy_ratio': {
        'plain': 'Rasio transaksi beli vs total transaksi (0-1)',
        'investor_view': 'Buy ratio >0.65 → strong accumulator, <0.40 → strong divestor',
        'theory': 'Behavioral Finance — accumulator vs divestor pattern'
    },
    'unique_stocks_traded': {
        'plain': 'Jumlah saham unik yang pernah ditransaksikan',
        'investor_view': 'Banyak saham → diversified portfolio (Balanced/Aggressive)',
        'theory': 'Modern Portfolio Theory — diversification principle'
    },
    'unique_sectors_traded': {
        'plain': 'Jumlah sektor unik yang pernah ditransaksikan',
        'investor_view': 'Multi-sektor → mature investor dengan cross-sector diversification',
        'theory': 'Modern Portfolio Theory — sector diversification'
    },
    'investment_period_days': {
        'plain': 'Total durasi investasi customer (hari)',
        'investor_view': 'Period panjang → long-term investor (Conservative/Balanced)',
        'theory': 'Lifecycle Investment Theory'
    },
    'sell_to_buy_value_ratio': {
        'plain': 'Rasio total sold vs total bought',
        'investor_view': 'Ratio >1 = net seller, <1 = net buyer (accumulator)',
        'theory': 'Behavioral Finance — net position analysis'
    },
    'digital_ratio': {
        'plain': 'Persentase transaksi via Internet Banking',
        'investor_view': 'Digital tinggi → tech-savvy customer, biasanya active trader',
        'theory': 'Diffusion of Innovation Theory (Rogers, 2003)'
    },
    'total_transactions': {
        'plain': 'Total semua transaksi (buy + sell)',
        'investor_view': 'Volume transaksi tinggi → high-engagement customer',
        'theory': 'Behavioral Finance — engagement level'
    },
    'has_questionnaire': {
        'plain': 'Apakah customer mengisi risk questionnaire (0/1)',
        'investor_view': 'Tidak ada questionnaire → profile less reliable, perlu human review',
        'theory': 'MiFID II — suitability assessment requirement'
    },
}


def get_business_interpretation(feature_name):
    """Ambil interpretasi business untuk feature. Default kalau tidak ada di dict."""
    if feature_name in FEATURE_BUSINESS_MEANING:
        return FEATURE_BUSINESS_MEANING[feature_name]
    # Default untuk one-hot encoded
    if feature_name.startswith('customerType_'):
        cat = feature_name.replace('customerType_', '')
        return {
            'plain': f'Customer adalah tipe: {cat}',
            'investor_view': f'Tipe {cat} menunjukkan segmen profil tertentu',
            'theory': 'MiFID II Client Categorization'
        }
    if feature_name.startswith('dominant_sector_'):
        sec = feature_name.replace('dominant_sector_', '')
        return {
            'plain': f'Sektor dominan: {sec}',
            'investor_view': f'Konsentrasi di sektor {sec} menunjukkan preferensi industry',
            'theory': 'Modern Portfolio Theory — sector exposure'
        }
    if feature_name.startswith('preferred_channel_'):
        ch = feature_name.replace('preferred_channel_', '')
        return {
            'plain': f'Channel preferensi: {ch}',
            'investor_view': f'Pilihan channel {ch} menunjukkan preferensi interaksi',
            'theory': 'Diffusion of Innovation Theory'
        }
    return {
        'plain': feature_name,
        'investor_view': 'Fitur ini berkontribusi ke prediksi',
        'theory': '—'
    }


def get_intention_strength(confidence):
    """Map confidence ke Intention Strength."""
    if confidence > 0.70:
        return {'label': '💪 STRONG INTENTION', 'color': '#27ae60'}
    elif confidence > 0.40:
        return {'label': '⚖️ MODERATE INTENTION', 'color': '#f39c12'}
    else:
        return {'label': '❓ UNCLEAR INTENTION', 'color': '#e74c3c'}


# ============================================================
# HEADER — PRIORITAS TINGGI #1: Judul + konteks Investment Intention
# ============================================================

st.title("🔍 SHAP Explanation – Transparansi Prediksi Pilihan Investasi")
st.markdown("**Lapisan Statistik:** Penjelasan matematis kontribusi setiap fitur terhadap prediksi Pilihan Investasi (Investment Intention)")

# Narasi pengantar (konsisten Page 1 & 2)
st.markdown("""
<div style="background-color: #f0f7ff; border-left: 4px solid #2E86AB;
            padding: 14px 16px; border-radius: 4px; margin: 12px 0;">
    <span style="color: #000000;">
        Halaman ini menjelaskan <strong>mengapa</strong> model memprediksi Pilihan Investasi tertentu
        untuk nasabah ini menggunakan <strong>SHAP (Shapley values)</strong> dari teori permainan kooperatif (Lundberg & Lee, 2017).
        Setiap fitur dianalisis kontribusinya — apakah <em>mendukung</em> (positif) atau <em>menentang</em> (negatif) prediksi.
    </span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TOP NAVIGATION BAR (PRIORITAS RENDAH #6)
# ============================================================

top_nav_col1, top_nav_col2, top_nav_col3 = st.columns([1, 2, 1])
with top_nav_col1:
    try:
        st.page_link("pages/2_🎯_Prediction.py", label="← Kembali ke Prediksi",
                    use_container_width=True)
    except Exception:
        if st.button("← Kembali ke Prediksi", use_container_width=True, key="back_top"):
            st.info("Buka halaman Prediksi dari sidebar.")

with top_nav_col3:
    try:
        st.page_link("pages/4_⚖️_KBS_Rules.py", label="Lihat Aturan KBS →",
                    use_container_width=True)
    except Exception:
        if st.button("Lihat Aturan KBS →", use_container_width=True, key="kbs_top"):
            st.info("Buka halaman Aturan KBS dari sidebar.")

st.markdown("---")

# ============================================================
# GUARD: Belum ada prediksi
# ============================================================

if 'last_features_df' not in st.session_state:
    st.warning("⚠️ Belum ada prediksi. Silakan lakukan prediksi terlebih dahulu di halaman **🎯 Prediction**.")
    st.stop()

# ============================================================
# LOAD RESOURCES
# ============================================================

with st.spinner("Loading SHAP explainer..."):
    model = load_model()
    le = load_label_encoder()
    X_test, y_test = load_test_data()
    label_names = list(le.classes_)

    try:
        explainer = load_shap_explainer()
        precomputed = load_shap_precomputed()
        is_real_shap = (hasattr(explainer, 'model') or
                        'TreeExplainer' in type(explainer).__name__)
    except Exception:
        explainer = None
        precomputed = None
        is_real_shap = False

# ============================================================
# FALLBACK kalau SHAP belum di-generate
# ============================================================

if not is_real_shap:
    st.error("""
    ⚠️ **SHAP Explainer belum di-generate!**

    Harap jalankan `04_explainability.ipynb` terlebih dahulu untuk generate:
    - `models/shap_explainer.pkl`
    - `models/shap_values_test.npz`

    Setelah selesai, restart dashboard dan buka halaman ini kembali.
    """)
    st.subheader("📊 Feature Importance (RF built-in, fallback)")
    feat_imp = pd.Series(model.feature_importances_,
                    index=X_test.columns).sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors_g = plt.cm.viridis(np.linspace(0.3, 0.9, len(feat_imp)))
    ax.barh(range(len(feat_imp)), feat_imp.values[::-1], color=colors_g)
    ax.set_yticks(range(len(feat_imp)))
    ax.set_yticklabels(feat_imp.index[::-1])
    ax.set_xlabel('Feature Importance')
    ax.set_title('Top 10 Features (RF built-in, bukan SHAP)', fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()
    st.stop()

# ============================================================
# PREDICTION CONTEXT — dengan Intention Strength
# ============================================================

last_features_df = st.session_state['last_features_df']
last_pred = st.session_state['last_prediction']
pred_label = last_pred['predicted_label']
confidence = last_pred['confidence']
pred_color = RISK_COLORS[pred_label]
strength = get_intention_strength(confidence)

st.subheader("📋 Prediction Context")

ctx_col1, ctx_col2, ctx_col3 = st.columns([2, 1, 1])

with ctx_col1:
    st.markdown(f"""
    <div style="background-color: {pred_color}20; border-left: 4px solid {pred_color};
                padding: 14px 16px; border-radius: 4px;">
        <div style="color: #000000; font-size: 12px;">PREDICTED INVESTMENT INTENTION</div>
        <div style="color: {pred_color}; font-weight: bold; font-size: 1.5em;">{pred_label}</div>
        <div style="color: #000000; font-size: 0.9em; margin-top: 4px;">
            Confidence: <strong>{confidence:.1%}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with ctx_col2:
    st.markdown(f"""
    <div style="background-color: {strength['color']}20; border-left: 4px solid {strength['color']};
                padding: 14px 16px; border-radius: 4px;">
        <div style="color: #000000; font-size: 12px;">INTENTION STRENGTH</div>
        <div style="color: {strength['color']}; font-weight: bold; font-size: 1.0em; margin-top: 4px;">
            {strength['label']}
        </div>
    </div>
    """, unsafe_allow_html=True)

with ctx_col3:
    if 'last_prediction_id' in st.session_state:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #95a5a6;
                    padding: 14px 16px; border-radius: 4px;">
            <div style="color: #000000; font-size: 12px;">PREDICTION ID</div>
            <div style="color: #000000; font-size: 0.85em; margin-top: 4px; font-family: monospace;">
                {st.session_state['last_prediction_id']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# COMPUTE SHAP VALUES
# ============================================================

with st.spinner("Computing SHAP values..."):
    shap_result = get_shap_explanation(last_features_df, model=model, explainer=explainer)

# ============================================================
# PRIORITAS MENENGAH #4: LAYOUT DENGAN TABS
# ============================================================

st.markdown("---")
st.subheader("📊 SHAP Explanation – Investment Intention Transparency")

tab1, tab2, tab3, tab4 = st.tabs([
    "🌍 Kepentingan Global",
    "👤 Penjelasan Lokal",
    "💧 Diagram Waterfall",
    "📖 Panduan Interpretasi"
])

# ============================================================
# TAB 1: GLOBAL FEATURE IMPORTANCE (Top 10, bigger chart)
# ============================================================

with tab1:
    st.markdown("**Fitur paling berpengaruh secara keseluruhan** (mean |SHAP| across test samples)")

    # Quick explanation positif/negatif (PDF: "tambahkan penjelasan singkat arti positif/negatif")
    st.markdown("""
    <div style="background-color: #fff8e1; border-left: 3px solid #ff9800;
                padding: 10px 14px; border-radius: 4px; margin: 8px 0; font-size: 0.9em;">
        <span style="color: #000000;">
            <strong>📌 Cara baca SHAP:</strong>
            <span style="color: #27ae60;">SHAP positif</span> = fitur mendorong prediksi ke kelas tertentu.
            <span style="color: #e74c3c;">SHAP negatif</span> = fitur menahan prediksi dari kelas tersebut.
            <strong>Nilai absolut |SHAP|</strong> = seberapa besar pengaruhnya (tidak peduli arah).
        </span>
    </div>
    """, unsafe_allow_html=True)

    shap_values_3d = precomputed['shap_values_3d']
    global_importance = np.abs(shap_values_3d).mean(axis=0).mean(axis=-1)
    feat_imp_series = pd.Series(global_importance, index=X_test.columns).sort_values(ascending=False)

    # Top 10 dengan chart lebih besar (PDF: "perbesar ukuran")
    top_10 = feat_imp_series.head(10)
    fig, ax = plt.subplots(figsize=(12, 7))  # Lebih besar dari 10x7 ke 12x7
    colors_grad = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_10)))
    bars = ax.barh(range(len(top_10)), top_10.values[::-1], color=colors_grad)
    for bar, val in zip(bars, top_10.values[::-1]):
        ax.text(val + 0.001, bar.get_y() + bar.get_height()/2,
                f'{val:.4f}', va='center', fontsize=11, fontweight='bold')
    ax.set_yticks(range(len(top_10)))
    ax.set_yticklabels(top_10.index.tolist()[::-1], fontsize=12)
    ax.set_xlabel('Mean |SHAP value|', fontsize=12)
    ax.set_title('Top 10 Features by SHAP Importance (Global)', fontweight='bold', fontsize=14)
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()

    # Keterangan di bawah chart
    st.markdown("""
    <div style="text-align: center; margin-top: 6px; margin-bottom: 12px;
                padding: 8px 14px; background-color: #f5f5f5; border-radius: 6px;
                border: 1px solid #e0e0e0;">
        <span style="color: #555; font-size: 0.88em;">
            ℹ️ Semakin tinggi nilai <strong>Mean |SHAP|</strong>, semakin besar pengaruh
            fitur tersebut terhadap prediksi secara keseluruhan.
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # PRIORITAS TINGGI #3: Top Insights dengan business interpretation
    # ============================================================

    st.markdown("---")
    st.markdown("### 🎯 Top 5 Insights — Business Interpretation")
    st.caption("Bukan hanya angka — penjelasan bisnis dengan referensi teori akademis.")

    top_5 = feat_imp_series.head(5)
    for i, (feat, val) in enumerate(top_5.items(), 1):
        biz = get_business_interpretation(feat)
        rank_colors = ['#3498db', '#52B788', '#F4A261', '#9b59b6', '#1abc9c']
        color = rank_colors[i-1]

        st.markdown(f"""<div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-left: 4px solid {color}; padding: 16px 20px; border-radius: 6px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
<div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; margin-bottom: 12px;">
<div style="display: flex; align-items: center; gap: 10px;">
<span style="background-color: {color}; color: white; padding: 3px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em;">#{i} TOP FEATURE</span>
<code style="color: #000000; font-size: 1.0em;">{feat}</code>
</div>
<div style="color: #000000; font-weight: bold; font-size: 0.95em; background-color: #f5f5f5; padding: 3px 10px; border-radius: 8px;">Mean |SHAP|: {val:.4f}</div>
</div>
<div style="margin-bottom: 10px;">
<div style="color: {color}; font-weight: bold; font-size: 0.82em; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
📝 Apa Artinya
</div>
<div style="color: #000000; font-size: 0.92em; padding-left: 4px;">
{biz['plain']}
</div>
</div>
<div style="margin-bottom: 10px;">
<div style="color: {color}; font-weight: bold; font-size: 0.82em; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
💼 Implikasi untuk Investor
</div>
<div style="color: #000000; font-size: 0.92em; padding-left: 4px;">
{biz['investor_view']}
</div>
</div>
<div>
<div style="color: #888; font-weight: bold; font-size: 0.80em; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
📚 Dasar Teori
</div>
<div style="color: #555; font-size: 0.88em; font-style: italic; padding-left: 4px;">
{biz['theory']}
</div>
</div>
</div>""", unsafe_allow_html=True)


# ============================================================
# TAB 2: LOCAL EXPLANATION — chart dengan warna jelas
# ============================================================

with tab2:
    st.write("") # Whitespace
    st.markdown(f"**Penjelasan spesifik:** Mengapa model memprediksi `{pred_label}` dengan tingkat kepercayaan **{confidence:.1%}**?")
    st.write("") # Whitespace

    # Warning untuk low confidence
    if confidence < 0.70:
        st.warning(f"⚠️ **Kepercayaan Rendah ({confidence:.1%})** — Perhatikan kontribusi hijau (mendukung) vs merah (menentang). "
                   f"Jika terdapat banyak konflik, pertimbangkan untuk memeriksa tab KBS Rules untuk validasi tambahan.")

    st.markdown(f"**🔝 10 Fitur Teratas yang Berkontribusi pada Prediksi '{pred_label}'**")
    top_feats = shap_result['top_features']
    plot_data = pd.DataFrame(top_feats[:10]).sort_values('shap_value')

    # Chart dengan warna sangat jelas hijau/merah
    fig, ax = plt.subplots(figsize=(12, 6))
    colors_bar = ['#27ae60' if v > 0 else '#e74c3c' for v in plot_data['shap_value']]
    bars = ax.barh(plot_data['feature'], plot_data['shap_value'], color=colors_bar,
                   edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, plot_data['shap_value']):
        ax.text(
            bar.get_width() + (0.001 if val > 0 else -0.001),
            bar.get_y() + bar.get_height()/2,
            f'{val:+.4f}', va='center',
            ha='left' if val > 0 else 'right',
            fontsize=10, fontweight='bold'
        )
    ax.axvline(x=0, color='black', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.set_xlabel('Nilai SHAP (dampak terhadap prediksi)', fontsize=11)
    ax.set_title(f'SHAP Lokal: Kontribusi Fitur untuk Nasabah Ini', fontweight='bold', fontsize=13)
    ax.grid(axis='x', alpha=0.3)
    # Legend yang jelas dan dinamis
    legend = ax.legend(handles=[
        Patch(facecolor='#27ae60', edgecolor='white', label=f'🟢 Mendukung prediksi {pred_label}'),
        Patch(facecolor='#e74c3c', edgecolor='white', label=f'🔴 Menentang prediksi {pred_label}')
    ], loc='lower right', fontsize=10, framealpha=0.95)
    legend.get_frame().set_edgecolor('#ccc')
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()

    # Keterangan di bawah chart
    st.markdown(f"""
    <div style="text-align: center; margin-top: 6px; margin-bottom: 24px;
                padding: 8px 14px; background-color: #f5f5f5; border-radius: 6px;
                border: 1px solid #e0e0e0;">
        <span style="color: #555; font-size: 0.88em;">
            ℹ️ Semakin ke kanan (nilai SHAP positif) = semakin <strong>mendorong</strong> prediksi ke kelas <strong>{pred_label}</strong>.
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.write("") # Whitespace
    st.markdown("**📊 Nilai Fitur, Dampak & Interpretasi:**")

    # Tabel lebih lengkap dengan 4 kolom + business meaning
    table_data = []
    for f in top_feats[:10]:
        biz = get_business_interpretation(f['feature'])
        emoji = "🟢 ↑" if f['shap_value'] > 0 else "🔴 ↓"
        table_data.append({
            'Arah': emoji,
            'Fitur': f['feature'],
            'Nilai': f"{f['value']:.2f}",
            'SHAP': f"{f['shap_value']:+.4f}",
            'Interpretasi': biz['plain'][:100] + ('...' if len(biz['plain']) > 100 else '')
        })
    df_local = pd.DataFrame(table_data)
    st.dataframe(df_local, use_container_width=True, hide_index=True)

    st.write("") # Whitespace
    st.info("""
    **Cara membaca tabel:**
    - **🟢 ↑ Hijau** = Fitur **mendukung / meningkatkan** peluang prediksi `{}`
    - **🔴 ↓ Merah** = Fitur **menentang / menurunkan** peluang prediksi `{}`
    - Nilai SHAP yang semakin besar menunjukkan pengaruh kontribusi yang semakin kuat.
    """.format(pred_label, pred_label))


# ============================================================
# TAB 3: WATERFALL PLOT — PRIORITAS TINGGI #2
# ============================================================

with tab3:
    st.markdown("**💧 Waterfall Plot** — Visualisasi cara setiap fitur 'membangun' prediksi dari base value")

    st.markdown("""
    <div style="background-color: #e8f5e9; border-left: 4px solid #4caf50;
                padding: 12px 16px; border-radius: 4px; margin: 12px 0; font-size: 0.92em;">
        <span style="color: #000000;">
            <strong>📖 Waterfall plot</strong> adalah representasi SHAP <strong>standard terbaik</strong>
            untuk local explanation. Bar memulai dari <em>base value</em> (rata-rata prediksi model),
            lalu setiap fitur menambah (hijau) atau mengurangi (merah) sampai mencapai prediksi final.
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Compute waterfall data
    expected_value = shap_result['expected_value']
    top_feats_wf = shap_result['top_features'][:10]  # Top 10 features

    # Buat waterfall manual dengan matplotlib
    fig, ax = plt.subplots(figsize=(12, 7))

    # Sort by absolute SHAP (paling impactful di atas)
    sorted_feats = sorted(top_feats_wf, key=lambda x: abs(x['shap_value']), reverse=True)
    
    # Labels untuk y-axis (bottom to top)
    labels = ['BASE VALUE\n(Expected)'] + \
             [f"{f['feature']}\n(val={f['value']:.2f})" for f in sorted_feats] + \
             ['PREDICTION\n(Final)']

    # Build cumulative values
    cumulative = expected_value
    positions = []
    widths = []
    colors = []
    starts = []

    # Base bar
    positions.append(0)
    widths.append(expected_value)
    colors.append('#95a5a6')
    starts.append(0)

    # Feature bars
    cum = expected_value
    for i, feat in enumerate(sorted_feats):
        sv = feat['shap_value']
        positions.append(i + 1)
        widths.append(abs(sv))
        colors.append('#27ae60' if sv > 0 else '#e74c3c')
        if sv > 0:
            starts.append(cum)
        else:
            starts.append(cum + sv)  # negative bar starts before cum
        cum += sv

    # Final prediction bar
    positions.append(len(sorted_feats) + 1)
    widths.append(cum)
    colors.append('#3498db')
    starts.append(0)

    # Plot horizontal bars
    for pos, start, width, color in zip(positions, starts, widths, colors):
        ax.barh(pos, width, left=start, color=color, edgecolor='white', linewidth=1.5)

    # Tambahkan value labels di setiap bar
    # Base value
    ax.text(expected_value + 0.005, 0, f'{expected_value:.3f}',
            va='center', fontsize=10, fontweight='bold', color='#000')

    # Feature bars
    cum = expected_value
    for i, feat in enumerate(sorted_feats):
        sv = feat['shap_value']
        text_x = cum + sv/2 if sv > 0 else cum + sv/2
        sign = '+' if sv > 0 else ''
        ax.text(text_x, i + 1, f'{sign}{sv:.3f}',
                va='center', ha='center', fontsize=9, fontweight='bold',
                color='white' if abs(sv) > 0.01 else '#000')
        cum += sv

    # Final prediction
    ax.text(cum + 0.005, len(sorted_feats) + 1, f'{cum:.3f}',
            va='center', fontsize=10, fontweight='bold', color='#000')

    # Connecting dashed lines untuk visual flow
    cum = expected_value
    for i, feat in enumerate(sorted_feats):
        sv = feat['shap_value']
        next_cum = cum + sv
        # Connect end of current to start of next
        ax.plot([cum, cum], [i + 0.4, i + 1 + 0.4 if sv > 0 else i + 0.4],
                'k--', alpha=0.3, linewidth=0.8)
        cum = next_cum

    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('Cumulative SHAP Value Contribution', fontsize=11)
    ax.set_title(f'Waterfall: How Features Build Up to "{pred_label}" Prediction',
                 fontweight='bold', fontsize=13)
    ax.grid(axis='x', alpha=0.3)
    ax.axvline(x=expected_value, color='gray', linewidth=0.6, linestyle=':', alpha=0.7)

    # Legend
    legend = ax.legend(handles=[
        Patch(facecolor='#95a5a6', label='Base Value (Expected)'),
        Patch(facecolor='#27ae60', label='Positive Contribution (+)'),
        Patch(facecolor='#e74c3c', label='Negative Contribution (−)'),
        Patch(facecolor='#3498db', label='Final Prediction'),
    ], loc='lower right', fontsize=10, framealpha=0.95)
    legend.get_frame().set_edgecolor('#ccc')

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()

    # Cara baca waterfall
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 14px 18px; border-radius: 6px;
                margin: 12px 0; border: 1px solid #e0e0e0;">
        <strong style="color: #000000;">📊 Cara membaca waterfall plot:</strong>
        <ol style="color: #000000; font-size: 0.92em; margin-top: 8px;">
            <li><strong>BASE VALUE</strong> (abu-abu, paling bawah) = rata-rata prediksi model
                untuk semua customer. Ini titik awal sebelum melihat customer ini.</li>
            <li><strong>Bar hijau</strong> ke kanan = fitur menambah probability ke prediksi ini.</li>
            <li><strong>Bar merah</strong> ke kiri = fitur mengurangi probability dari prediksi ini.</li>
            <li><strong>PREDICTION</strong> (biru, paling atas) = hasil akhir prediksi model.</li>
        </ol>
        <p style="color: #000000; font-size: 0.88em; margin-top: 8px; font-style: italic;">
            Math: <code>Base Value + Σ(SHAP values) = Final Prediction</code> — properti
            <em>local accuracy</em> dari SHAP (Lundberg & Lee, 2017).
        </p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# TAB 4: INTERPRETATION GUIDE (expandable accordion)
# ============================================================

with tab4:
    st.write("") # Whitespace
    st.markdown("**📚 Panduan Lengkap Memahami SHAP dan Cara Membacanya**")
    st.write("") # Whitespace

    with st.expander("🤔 Apa itu SHAP Value? (Untuk Pemula)", expanded=False):
        st.markdown("""
        **SHAP** adalah singkatan dari **SHapley Additive exPlanations** — sebuah metode yang diadaptasi dari teori permainan kooperatif (Shapley, 1953; Lundberg & Lee, 2017) untuk menjelaskan hasil prediksi model machine learning.

        **Konsep Dasar:**
        Bayangkan model machine learning sebagai sebuah tim sepak bola. Setiap fitur data (seperti total investasi atau frekuensi transaksi) adalah pemain dalam tim tersebut. SHAP mengukur kontribusi rata-rata dari masing-masing "pemain" (fitur) dalam memenangkan pertandingan (menghasilkan nilai prediksi final), secara adil dan konsisten menurut dasar matematis.

        **Manfaat bagi Investor Retail:**
        Sistem AI ini tidak bersifat seperti kotak hitam (*black box*) yang misterius. SHAP menjelaskan secara transparan dan terperinci **mengapa** model mengkategorikan profil investasi Anda ke tingkat tertentu.
        """)

    with st.expander("📊 Cara Membaca Grafik SHAP", expanded=False):
        st.markdown("""
        **Grafik Kepentingan Global (Global Importance - Tab 1):**
        - **Sumbu Y (Vertikal):** Nama fitur.
        - **Sumbu X (Horizontal):** Rata-rata nilai SHAP absolut (|SHAP|) dari seluruh sampel data pengujian.
        - Semakin panjang grafik batang, semakin besar pengaruh umum fitur tersebut terhadap prediksi model secara keseluruhan.

        **Grafik Penjelasan Lokal (Local Explanation - Tab 2):**
        - **Bar Hijau ke Kanan:** Fitur yang **mendukung / meningkatkan** peluang nasabah dikategorikan ke dalam kelas prediksi tersebut.
        - **Bar Merah ke Kiri:** Fitur yang **menentang / menghambat** model untuk memilih kelas prediksi tersebut.
        - Panjang bar mencerminkan seberapa kuat kontribusi fitur tersebut pada nasabah ini.

        **Diagram Waterfall (Tab 3):**
        - Visualisasi dimulai dari *Base Value* (nilai rata-rata prediksi sebelum melihat data nasabah).
        - Setiap bar fitur menambahkan (hijau) atau mengurangi (merah) kontribusi secara akumulatif.
        - Hasil akhir penjumlahan di bagian atas menunjukkan probabilitas prediksi final.
        """)

    with st.expander("💼 Penjelasan untuk Investor (Bahasa Sederhana)", expanded=False):
        st.markdown("""
        Sistem kecerdasan buatan (AI) ini menentukan profil risiko investasi Anda bukan secara acak, melainkan berdasarkan akumulasi dari faktor-faktor nyata.

        **Sebagai Ilustrasi:**
        Jika model memprediksi profil risiko Anda sebagai **Balanced (Seimbang)**, sistem akan menguraikan kontribusinya secara logis:
        - "Total modal yang diinvestasikan sudah cukup besar" ➔ Memberikan kontribusi positif terhadap profil Balanced.
        - "Jeda hari antar transaksi yang teratur" ➔ Memberikan kontribusi positif tambahan.
        - "Jumlah sektor saham unik yang ditransaksikan bervariasi" ➔ Mendukung diversifikasi portofolio Balanced.

        **Manfaat Utama untuk Anda:**
        1. **Transparansi:** Anda mengetahui dengan pasti landasan logis di balik klasifikasi profil Anda.
        2. **Kepercayaan:** Anda dapat memverifikasi kesesuaian antara fakta keuangan Anda dengan kesimpulan model.
        3. **Aksi Nyata:** Jika kesimpulan model dirasa kurang sesuai, Anda dapat berdiskusi lebih dalam dengan penasihat keuangan berdasarkan poin-poin kontribusi fitur yang spesifik ini.
        """)

    with st.expander("🎓 Properti Matematis SHAP", expanded=False):
        st.markdown("""
        Metode SHAP merupakan satu-satunya metode atribusi fitur yang memenuhi tiga properti teoritis utama (Lundberg & Lee, 2017):

        1. **Akurasi Lokal (*Local Accuracy*):** Jumlah kontribusi nilai SHAP dari seluruh fitur ditambah dengan nilai harapan baseline (*expected value*) akan menghasilkan nilai prediksi yang presisi secara matematis.
        2. **Ketiadaan (*Missingness*):** Fitur yang tidak memiliki nilai atau kontribusi dalam pengamatan akan mendapatkan nilai SHAP tepat nol (0).
        3. **Konsistensi (*Consistency*):** Jika model berubah sedemikian rupa sehingga kontribusi suatu fitur meningkat, nilai atribusi SHAP untuk fitur tersebut dijamin tidak akan menurun.

        Kombinasi ketiga properti ini yang membuat SHAP defensif dan tepercaya secara akademis dibandingkan metode XAI lainnya.
        """)

    with st.expander("📚 Referensi Akademis", expanded=False):
        st.markdown("""
        **Primary Reference:**
        - Lundberg, S. M., & Lee, S. I. (2017). *A Unified Approach to Interpreting
          Model Predictions*. **NeurIPS 2017**.

        **Foundational:**
        - Shapley, L. S. (1953). *A Value for n-Person Games*. RAND Corporation.
        - Štrumbelj, E., & Kononenko, I. (2014). *Explaining Prediction Models and
          Individual Predictions with Feature Contributions*. Knowledge and Information Systems.

        **Applications in Finance:**
        - Bussmann, N., et al. (2020). *Explainable AI in Fintech Risk Management*.
          Frontiers in AI.
        """)


# ============================================================
# BOTTOM NAVIGATION BAR
# ============================================================

st.markdown("---")

# Inject CSS khusus untuk membuat tombol navigasi bawah menonjol
st.markdown("""
<style>
    /* Styling khusus untuk page link di navigasi bawah agar sangat menonjol */
    .bot-nav-container div[data-testid="column"] div[data-testid="stPageLink"] a {
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1.02em !important;
        text-decoration: none !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
        height: 52px !important;
        min-height: 52px !important;
    }
    
    /* Fallback untuk standard buttons jika st.page_link error */
    .bot-nav-container div[data-testid="column"] button {
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1.02em !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        height: 52px !important;
        width: 100% !important;
    }
    
    /* Hover effect */
    .bot-nav-container div[data-testid="column"] div[data-testid="stPageLink"] a:hover,
    .bot-nav-container div[data-testid="column"] button:hover {
        transform: translateY(-3px) !important;
        filter: brightness(1.08) !important;
        color: white !important;
        text-decoration: none !important;
    }

    /* Column 1: Kembali ke Prediction - Soft gray-blue background */
    .bot-nav-container div[data-testid="column"]:nth-of-type(1) div[data-testid="stPageLink"] a,
    .bot-nav-container div[data-testid="column"]:nth-of-type(1) button {
        background: linear-gradient(135deg, #7f8c8d 0%, #95a5a6 100%) !important;
        box-shadow: 0 4px 15px rgba(127, 140, 141, 0.25) !important;
    }
    .bot-nav-container div[data-testid="column"]:nth-of-type(1) div[data-testid="stPageLink"] a:hover,
    .bot-nav-container div[data-testid="column"]:nth-of-type(1) button:hover {
        box-shadow: 0 6px 20px rgba(127, 140, 141, 0.35) !important;
    }

    /* Column 2: New Prediction - Green gradient background */
    .bot-nav-container div[data-testid="column"]:nth-of-type(2) div[data-testid="stPageLink"] a,
    .bot-nav-container div[data-testid="column"]:nth-of-type(2) button {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%) !important;
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3) !important;
    }
    .bot-nav-container div[data-testid="column"]:nth-of-type(2) div[data-testid="stPageLink"] a:hover,
    .bot-nav-container div[data-testid="column"]:nth-of-type(2) button:hover {
        box-shadow: 0 6px 20px rgba(39, 174, 96, 0.45) !important;
    }

    /* Column 3: Lanjut ke KBS Rules - Blue-teal gradient background */
    .bot-nav-container div[data-testid="column"]:nth-of-type(3) div[data-testid="stPageLink"] a,
    .bot-nav-container div[data-testid="column"]:nth-of-type(3) button {
        background: linear-gradient(135deg, #2E86AB 0%, #1abc9c 100%) !important;
        box-shadow: 0 4px 15px rgba(46, 134, 171, 0.3) !important;
    }
    .bot-nav-container div[data-testid="column"]:nth-of-type(3) div[data-testid="stPageLink"] a:hover,
    .bot-nav-container div[data-testid="column"]:nth-of-type(3) button:hover {
        box-shadow: 0 6px 20px rgba(46, 134, 171, 0.45) !important;
    }
</style>
""", unsafe_allow_html=True)

# Bungkus dalam container agar CSS dapat menargetkan secara spesifik
st.markdown('<div class="bot-nav-container">', unsafe_allow_html=True)

bot_nav_col1, bot_nav_col2, bot_nav_col3 = st.columns([1, 1, 1])

with bot_nav_col1:
    try:
        st.page_link("pages/2_🎯_Prediction.py", label="← Kembali ke Prediction",
                     use_container_width=True)
    except Exception:
        if st.button("← Kembali ke Prediction", use_container_width=True, key="back_bot"):
            st.info("Buka halaman Prediction dari sidebar.")

with bot_nav_col2:
    try:
        st.page_link("pages/2_🎯_Prediction.py", label="🚀 New Prediction",
                     use_container_width=True)
    except Exception:
        if st.button("🚀 New Prediction", use_container_width=True, key="new_pred"):
            st.info("Buka halaman Prediction dari sidebar untuk prediksi baru.")

with bot_nav_col3:
    try:
        st.page_link("pages/4_⚖️_KBS_Rules.py", label="Lanjut ke KBS Rules →",
                     use_container_width=True)
    except Exception:
        if st.button("Lanjut ke KBS Rules →", use_container_width=True, key="kbs_bot"):
            st.info("Buka halaman KBS Rules dari sidebar.")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("**SHAP Explainer** | Statistical Layer dari Transparent Investment Intention System | "
           "Powered by Shapley Values Theory (Lundberg & Lee, 2017)")
st.markdown("""
<div style="text-align: center; margin-top: 10px; opacity: 0.7;">
    <p style="color: #7f8c8d; font-size: 0.82em; font-style: italic; margin-bottom: 20px;">
        ⚠️ <strong>Disclaimer:</strong> Penjelasan SHAP bersifat statistik dan bersifat pendukung. 
        Keputusan investasi tetap harus mempertimbangkan faktor dan analisis profesional lainnya.
    </p>
</div>
""", unsafe_allow_html=True)