"""
2_🎯_Prediction.py
==================
Halaman Prediction - Risk Profile / Investment Intention Prediction.

Revisi berdasarkan feedback:
- Poin 3: Quick Load Examples + Quick/Advanced Mode toggle
- Poin 4: Intention Strength badge + expanded About + warning low confidence
- Poin 5: Prominent navigation buttons + conditional confidence notice
- Plus: Reset button, ranking table, prediction ID/timestamp
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.helpers import (
    load_model, load_label_encoder, load_test_data,
    load_feature_stats, predict_customer,
    RISK_COLORS, RISK_DESCRIPTIONS, render_risk_badge
)

st.set_page_config(
    page_title="Prediction - Investment Intention",
    page_icon="🎯",
    layout="wide"
)

# ============================================================
# CONSTANTS
# ============================================================

CUSTOMER_TYPES = ['Inactive', 'Legal Entity', 'Mass', 'Premium', 'Professional']
CHANNELS = ['Branch', 'Internet Banking', 'Phone Banking']
SECTORS = ['Basic Materials', 'Communication Services', 'Consumer Cyclical',
           'Consumer Defensive', 'Energy', 'Financial Services',
           'Healthcare', 'Industrials', 'Real Estate', 'Technology',
           'Unknown', 'Utilities']

# Quick Load Examples (dari analisis test set, high confidence per class)
QUICK_EXAMPLES = {
    "🛡️ Investor Pemula (Conservative)": {
        "idx": 793,
        "description": "Profil defensif — modal kecil, transaksi jarang, fokus preservasi modal",
        "expected": "Conservative"
    },
    "📈 Investor Stabil (Income)": {
        "idx": 462,
        "description": "Profil pendapatan — fokus dividen, instrumen low-volatility",
        "expected": "Income"
    },
    "⚖️ Investor Seimbang (Balanced)": {
        "idx": 458,
        "description": "Profil moderat — kombinasi growth & stability",
        "expected": "Balanced"
    },
    "🚀 Investor Agresif (Aggressive)": {
        "idx": 1454,
        "description": "Profil agresif — modal besar, aktif trading, toleransi risiko tinggi",
        "expected": "Aggressive"
    },
}

# Expanded "About" dengan rekomendasi investasi
RISK_DETAILS = {
    'Conservative': {
        'description': 'Profil paling defensif. Prioritas preservasi modal, toleransi risiko rendah.',
        'instruments': '70-80% obligasi/deposito, 15-25% reksa dana pendapatan tetap, 5-10% saham blue chip',
        'tips': 'Hindari trading aktif, fokus jangka panjang (5-10 tahun), prioritaskan instrumen rating AAA'
    },
    'Income': {
        'description': 'Profil pendapatan stabil. Fokus pada dividen dan instrumen low-volatility.',
        'instruments': '50-60% obligasi & deposito, 25-30% saham dividen tinggi, 10-15% reksa dana campuran',
        'tips': 'Pilih saham dengan dividend yield konsisten (>4%), rebalance portofolio setiap 6 bulan'
    },
    'Balanced': {
        'description': 'Profil seimbang. Kombinasi growth dan stability.',
        'instruments': '40% saham (mix blue chip & growth), 35% obligasi, 15% reksa dana, 10% emas/aset alternatif',
        'tips': 'Diversifikasi 3-5 sektor, jangan overconcentrate di 1 saham, review portofolio kuartalan'
    },
    'Aggressive': {
        'description': 'Profil pertumbuhan agresif. Toleransi risiko tinggi untuk return maksimal.',
        'instruments': '70-80% saham (growth & small cap), 10-15% obligasi, 5-10% alternative assets',
        'tips': 'Pakai stop-loss strict (-15% sd -20%), hindari emotional trading, alokasikan max 5% per single stock'
    }
}


def build_onehot(selected_value, all_values, prefix, reference_value):
    result = {}
    for val in all_values:
        if val == reference_value:
            continue
        result[f"{prefix}_{val}"] = 1 if selected_value == val else 0
    return result


def get_intention_strength(confidence):
    """Map confidence ke Intention Strength category."""
    if confidence > 0.70:
        return {
            'label': '💪 STRONG INTENTION',
            'color': '#27ae60',
            'description': 'Model sangat yakin. Pola transaksi konsisten dengan profil yang diprediksi.'
        }
    elif confidence > 0.40:
        return {
            'label': '⚖️ MODERATE INTENTION',
            'color': '#f39c12',
            'description': 'Model cukup yakin. Pola customer ambigu antara 2 profil. Recommend SHAP & KBS check.'
        }
    else:
        return {
            'label': '❓ UNCLEAR INTENTION',
            'color': '#e74c3c',
            'description': 'Model tidak yakin. Pola customer mixed atau outlier. Wajib human review.'
        }


def generate_prediction_id():
    """Generate unique prediction ID dengan timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    short_uuid = str(uuid.uuid4())[:8].upper()
    return f"PRED-{timestamp}-{short_uuid}"


# ============================================================
# HEADER
# ============================================================

st.title("🎯 Prediction – Investment Intention Analysis")
st.markdown("**Prediksi Niat Investasi Investor Retail** dengan Transparansi Penuh (ML + SHAP + KBS Rules)")

# Narasi pengantar — selaras tema Investment Intention & Transparansi
st.markdown("""
<div style="background-color: #f0f7ff; border-left: 4px solid #2E86AB;
            padding: 14px 16px; border-radius: 4px; margin: 12px 0;">
    <span style="color: #000000;">
        Halaman ini memprediksi <strong>Investment Intention</strong> investor (direpresentasikan
        oleh Risk Profile sebagai proxy) berdasarkan pola transaksi nyata. Setiap prediksi
        dilengkapi <strong>Intention Strength</strong> dan dapat ditelusuri transparansinya
        melalui penjelasan <strong>SHAP</strong> (statistik) dan <strong>KBS Rules</strong> (domain knowledge).
    </span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# LOAD RESOURCES
# ============================================================

with st.spinner("Loading model & data..."):
    model = load_model()
    le = load_label_encoder()
    X_test, y_test = load_test_data()
    feature_stats = load_feature_stats()
    label_names = list(le.classes_)

# ============================================================
# RESET BUTTON (Top Right)
# ============================================================

header_col1, header_col2 = st.columns([4, 1])
with header_col2:
    if st.button("🔄 Reset", use_container_width=True, help="Reset semua input dan prediksi"):
        # Clear session state
        for key in ['last_prediction', 'last_features', 'last_features_df',
                    'last_prediction_id', 'last_prediction_time', 'true_label']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ============================================================
# SECTION 1: QUICK LOAD EXAMPLES (NEW)
# ============================================================

st.markdown("---")
st.subheader("⚡ Quick Load Examples")
st.caption("Untuk demo cepat, klik salah satu contoh investor di bawah:")

quick_cols = st.columns(4)
selected_quick_example = None

for idx, (label, info) in enumerate(QUICK_EXAMPLES.items()):
    with quick_cols[idx]:
        color = RISK_COLORS[info['expected']]
        if st.button(label, key=f"quick_{idx}", use_container_width=True):
            selected_quick_example = info['idx']
            st.session_state['quick_example_idx'] = info['idx']
        st.markdown(f"""
        <div style="background-color: {color}10; border-left: 3px solid {color};
                    padding: 8px 12px; border-radius: 4px; margin-top: 4px;
                    font-size: 0.85em; color: #555; min-height: 65px;">
            {info['description']}
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# SECTION 2: INPUT MODE
# ============================================================

st.markdown("---")
st.subheader("📝 Input Customer Data")

input_mode = st.radio(
    "Pilih cara input:",
    options=["Existing Customer (test set)", "Manual Input - Quick Mode", "Manual Input - Advanced Mode"],
    horizontal=True,
    help="Quick Mode: 6 fitur terpenting (Top SHAP). Advanced: semua 33 features."
)

features_dict = {}
true_label_actual = None

# ============================================================
# MODE A: EXISTING CUSTOMER
# ============================================================

if input_mode == "Existing Customer (test set)":
    # Auto-load if Quick Example clicked
    default_idx = st.session_state.get('quick_example_idx', 0)

    col1, col2 = st.columns([1, 2])

    with col1:
        customer_idx = st.number_input(
            f"Customer Index (0 - {len(X_test) - 1})",
            min_value=0, max_value=len(X_test) - 1,
            value=default_idx, step=1,
            help="Index customer di test set. Atau klik Quick Load di atas."
        )
        true_label_actual = label_names[y_test[customer_idx]]
        st.markdown(f"**Customer #{customer_idx}**")
        st.markdown(f"**True Label:** {render_risk_badge(true_label_actual)}",
                    unsafe_allow_html=True)

    with col2:
        filter_label = st.selectbox(
            "🔍 Filter customer by true label:",
            options=["All"] + label_names
        )
        if filter_label != "All":
            target_idx = label_names.index(filter_label)
            matching = np.where(y_test == target_idx)[0]
            if len(matching) > 0:
                st.info(f"💡 {len(matching)} customer dengan label '{filter_label}'. "
                        f"Coba index: {matching[:5].tolist()}")

    features_dict = X_test.iloc[customer_idx].to_dict()

# ============================================================
# MODE B: MANUAL INPUT - QUICK MODE (Top 6 Features)
# ============================================================

elif input_mode == "Manual Input - Quick Mode":
    st.info("💡 **Quick Mode** — Hanya 6 fitur paling berpengaruh (berdasarkan SHAP Top Features). "
            "Cocok untuk demo cepat.")

    # Initialize base with median values
    base_features = {col: feature_stats[col]['median'] for col in X_test.columns}

    st.markdown("### 🔧 Top 6 Important Features")

    qc1, qc2, qc3 = st.columns(3)

    with qc1:
        # #1: total_invested
        total_inv = st.number_input(
            "💰 Total Invested (EUR)",
            min_value=0.0, value=float(base_features.get('total_invested', 5000)),
            step=500.0,
            help="Top feature SHAP — total modal yang sudah diinvestasikan"
        )
        # #2: investmentCapacity
        inv_cap = st.select_slider(
            "📊 Investment Capacity",
            options=[0, 1, 2, 3],
            value=int(base_features.get('investmentCapacity', 1)),
            format_func=lambda x: ['<30K', '30K-80K', '80K-300K', '>300K'][x],
            help="Kategori kapasitas modal"
        )

    with qc2:
        # #3: avg_days_between_transactions
        avg_gap = st.number_input(
            "⏱️ Avg Days Between Transactions",
            min_value=0.0, value=float(base_features.get('avg_days_between_transactions', 30)),
            step=5.0,
            help="Rata-rata jeda hari antar transaksi"
        )
        # #4: total_sold
        total_sold = st.number_input(
            "📉 Total Sold (EUR)",
            min_value=0.0, value=float(base_features.get('total_sold', 3000)),
            step=500.0,
            help="Total nilai jual transaksi"
        )

    with qc3:
        # #5: avg_transaction_value (derives log_avg_value)
        avg_val = st.number_input(
            "💵 Avg Transaction Value (EUR)",
            min_value=0.0, value=float(base_features.get('avg_transaction_value', 1000)),
            step=100.0,
            help="Rata-rata nilai per transaksi"
        )
        # #6: unique_stocks_traded
        n_stocks = st.number_input(
            "🎨 Unique Stocks Traded",
            min_value=1, value=int(base_features.get('unique_stocks_traded', 3)),
            help="Jumlah saham unik yang pernah ditransaksikan"
        )

    # Build features_dict with overrides
    features_dict = dict(base_features)
    features_dict['total_invested'] = total_inv
    features_dict['investmentCapacity'] = inv_cap
    features_dict['avg_days_between_transactions'] = avg_gap
    features_dict['total_sold'] = total_sold
    features_dict['avg_transaction_value'] = avg_val
    features_dict['log_avg_value'] = float(np.log1p(avg_val))
    features_dict['unique_stocks_traded'] = n_stocks

    # Auto-compute related
    features_dict['sell_to_buy_value_ratio'] = total_sold / max(total_inv, 1)

    st.caption("ℹ️ Fitur lain (channel, sector, customer type) menggunakan median dataset training.")

# ============================================================
# MODE C: MANUAL INPUT - ADVANCED MODE (Full 33 Features)
# ============================================================

else:  # Advanced Mode
    st.info("💡 **Advanced Mode** — Akses semua 33 fitur dengan kategorisasi tab. "
            "Untuk analisis what-if mendalam.")

    init_col1, init_col2 = st.columns(2)
    with init_col1:
        start_from = st.selectbox(
            "Mulai dari:",
            options=["Default (median)", "Copy dari existing customer"]
        )
    if start_from == "Copy dari existing customer":
        with init_col2:
            base_idx = st.number_input("Base customer index:",
                                min_value=0, max_value=len(X_test)-1, value=0)
            base_features = X_test.iloc[base_idx].to_dict()
            true_label_actual = label_names[y_test[base_idx]]
    else:
        base_features = {col: feature_stats[col]['median'] for col in X_test.columns}

    def get_base(col, default=0):
        return base_features.get(col, default)

    st.markdown("### 🔧 Feature Inputs (All 33)")

    with st.expander("👤 Customer Profile", expanded=True):
        pc1, pc2 = st.columns(2)
        with pc1:
            inv_cap = st.select_slider(
                "Investment Capacity",
                options=[0, 1, 2, 3],
                value=int(get_base('investmentCapacity', 1)),
                format_func=lambda x: ['<30K EUR', '30K-80K', '80K-300K', '>300K EUR'][x]
            )
            features_dict['investmentCapacity'] = inv_cap
            has_q = st.checkbox("Has Questionnaire",
                                value=bool(get_base('has_questionnaire', 1)))
            features_dict['has_questionnaire'] = int(has_q)

        with pc2:
            curr_type = 'Inactive'
            for ct in CUSTOMER_TYPES[1:]:
                if get_base(f'customerType_{ct}', 0) == 1:
                    curr_type = ct
                    break
            cust_type = st.selectbox("Customer Type", options=CUSTOMER_TYPES,
                                    index=CUSTOMER_TYPES.index(curr_type))
            features_dict.update(build_onehot(cust_type, CUSTOMER_TYPES,
                                    'customerType', 'Inactive'))

    with st.expander("📊 Trading Behavior", expanded=True):
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            buy_count = st.number_input("Buy Count", min_value=0,
                                        value=int(get_base('buy_count', 3)))
            sell_count = st.number_input("Sell Count", min_value=0,
                                        value=int(get_base('sell_count', 2)))
            features_dict['buy_count'] = buy_count
            features_dict['sell_count'] = sell_count
            features_dict['total_transactions'] = buy_count + sell_count
            features_dict['buy_ratio'] = buy_count / max(buy_count + sell_count, 1)
        with bc2:
            avg_val = st.number_input("Avg Transaction Value (EUR)", min_value=0.0,
                                      value=float(get_base('avg_transaction_value', 1000)),
                                      step=100.0)
            features_dict['avg_transaction_value'] = avg_val
            features_dict['log_avg_value'] = float(np.log1p(avg_val))
            total_inv = st.number_input("Total Invested (EUR)", min_value=0.0,
                                        value=float(get_base('total_invested', 5000)),
                                        step=500.0)
            features_dict['total_invested'] = total_inv
        with bc3:
            total_sold = st.number_input("Total Sold (EUR)", min_value=0.0,
                                         value=float(get_base('total_sold', 3000)),
                                         step=500.0)
            features_dict['total_sold'] = total_sold
            features_dict['sell_to_buy_value_ratio'] = total_sold / max(total_inv, 1)

    with st.expander("🎨 Portfolio Diversification", expanded=False):
        port1, port2 = st.columns(2)
        with port1:
            features_dict['unique_stocks_traded'] = st.number_input(
                "Unique Stocks Traded", min_value=1,
                value=int(get_base('unique_stocks_traded', 3)))
            features_dict['unique_sectors_traded'] = st.number_input(
                "Unique Sectors Traded", min_value=1,
                value=int(get_base('unique_sectors_traded', 2)))
        with port2:
            curr_sector = 'Basic Materials'
            for s in SECTORS[1:]:
                if get_base(f'dominant_sector_{s}', 0) == 1:
                    curr_sector = s
                    break
            dom_sector = st.selectbox("Dominant Sector", options=SECTORS,
                                    index=SECTORS.index(curr_sector))
            features_dict.update(build_onehot(dom_sector, SECTORS,
                                        'dominant_sector', 'Basic Materials'))

    with st.expander("📡 Channel & Temporal", expanded=False):
        ch1, ch2 = st.columns(2)
        with ch1:
            features_dict['digital_ratio'] = st.slider(
                "Digital Ratio (% Internet Banking)",
                min_value=0.0, max_value=1.0,
                value=float(get_base('digital_ratio', 0.5)), step=0.05)
            curr_ch = 'Branch'
            for ch in CHANNELS[1:]:
                if get_base(f'preferred_channel_{ch}', 0) == 1:
                    curr_ch = ch
                    break
            pref_ch = st.selectbox("Preferred Channel", options=CHANNELS,
                                   index=CHANNELS.index(curr_ch))
            features_dict.update(build_onehot(pref_ch, CHANNELS,
                                              'preferred_channel', 'Branch'))
        with ch2:
            features_dict['investment_period_days'] = st.number_input(
                "Investment Period (days)", min_value=0,
                value=int(get_base('investment_period_days', 365)))
            features_dict['avg_days_between_transactions'] = st.number_input(
                "Avg Days Between Transactions", min_value=0.0,
                value=float(get_base('avg_days_between_transactions', 30.0)))

# ============================================================
# PREDICT BUTTON
# ============================================================

st.markdown("---")
predict_col1, predict_col2 = st.columns([3, 1])
with predict_col1:
    predict_btn = st.button("🚀 Predict Risk Profile", type="primary", use_container_width=True)

should_predict = predict_btn or (input_mode == "Existing Customer (test set)" and features_dict)

if should_predict and features_dict:
    ordered_features = {col: features_dict.get(col, 0) for col in X_test.columns}
    features_df = pd.DataFrame([ordered_features])[X_test.columns]

    with st.spinner("Predicting..."):
        result = predict_customer(features_df, model=model, label_encoder=le)

    # Generate prediction ID & timestamp
    pred_id = generate_prediction_id()
    pred_time = datetime.now().strftime('%d %b %Y, %H:%M:%S')

    # Save to session state
    st.session_state['last_prediction'] = result
    st.session_state['last_features'] = ordered_features
    st.session_state['last_features_df'] = features_df
    st.session_state['last_prediction_id'] = pred_id
    st.session_state['last_prediction_time'] = pred_time
    st.session_state['true_label'] = true_label_actual

    # ============================================================
    # SECTION 3: RESULTS — Enhanced
    # ============================================================

    st.markdown("---")
    st.subheader("📋 Prediction Results")

    # Prediction metadata (ID + timestamp)
    st.caption(f"🆔 **Prediction ID:** `{pred_id}` | 🕐 **Generated:** {pred_time}")

    pred_label = result['predicted_label']
    confidence = result['confidence']
    color = RISK_COLORS[pred_label]
    strength = get_intention_strength(confidence)

    res_col1, res_col2 = st.columns([1, 2])

    with res_col1:
        # Main prediction card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color}30 0%, {color}10 100%);
                    border: 3px solid {color}; border-radius: 12px;
                    padding: 24px; text-align: center;">
            <div style="color: #555; font-size: 13px; margin-bottom: 6px;">PREDICTED RISK PROFILE</div>
            <div style="color: {color}; font-size: 36px; font-weight: bold;">{pred_label}</div>
            <div style="color: #666; font-size: 18px; margin-top: 6px;">
                Confidence: <strong>{confidence:.1%}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Intention Strength badge (NEW)
        st.markdown(f"""
        <div style="background-color: {strength['color']}20; border-left: 4px solid {strength['color']};
                    padding: 12px 14px; border-radius: 6px; margin-top: 12px;">
            <div style="color: {strength['color']}; font-weight: bold; font-size: 14px;">
                {strength['label']}
            </div>
            <div style="color: #555; font-size: 0.85em; margin-top: 4px;">
                {strength['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Ground truth comparison if available
        if true_label_actual:
            is_correct = (pred_label == true_label_actual)
            result_status = '✅ CORRECT' if is_correct else '❌ INCORRECT'
            st.markdown(
                f"**Ground Truth:** {render_risk_badge(true_label_actual)}  \n"
                f"**Status:** {result_status}",
                unsafe_allow_html=True
            )

    with res_col2:
        proba_data = sorted(result['probabilities'].items(), key=lambda x: x[1])
        fig, ax = plt.subplots(figsize=(6, 3.5))
        classes_sorted = [x[0] for x in proba_data]
        probas_sorted = [x[1] for x in proba_data]
        bars = ax.barh(classes_sorted, probas_sorted,
                    color=[RISK_COLORS[n] for n in classes_sorted])
        for bar, prob in zip(bars, probas_sorted):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{prob:.1%}', va='center', fontweight='bold')
        ax.set_xlim(0, max(probas_sorted) * 1.2)
        ax.set_xlabel('Probability')
        ax.set_title('Prediction Confidence per Class', fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()

        st.markdown("**Probability Distribution:**")
        st.pyplot(fig, use_container_width=True)
        plt.close()

        st.markdown("**📊 Class Ranking:**")
        ranking_data = []
        for rank, (cls, prob) in enumerate(sorted(result['probabilities'].items(),
                            key=lambda x: x[1], reverse=True), 1):
            medal = ['🥇', '🥈', '🥉', '4️⃣'][rank - 1]
            ranking_data.append({
                'Rank': f"{medal} #{rank}",
                'Class': cls,
                'Probability': f"{prob:.2%}",
                'Status': '⭐ Predicted' if cls == pred_label else '—'
            })
        st.dataframe(pd.DataFrame(ranking_data), use_container_width=True, hide_index=True)

    # ============================================================
    # LOW CONFIDENCE WARNING (Conditional)
    # ============================================================

    if confidence < 0.70:
        st.warning(f"""
        ⚠️ **Confidence di bawah 70% ({confidence:.1%})** — Disarankan untuk:
        1. Memeriksa penjelasan **SHAP** untuk lihat fitur mana yang berkontribusi
        2. Cross-check dengan **KBS Rules** untuk validasi domain expert
        3. Pertimbangkan **human review** oleh financial advisor

        Confidence rendah biasanya menandakan profil customer yang ambigu atau outlier.
        """)

    # ============================================================
    # EXPANDED "ABOUT [PROFILE]" — Karakteristik + Rekomendasi + Tips
    # ============================================================

    st.markdown("---")
    st.subheader(f"📖 About {pred_label} Profile")

    detail = RISK_DETAILS[pred_label]

    about_col1, about_col2, about_col3 = st.columns(3)

    with about_col1:
        st.markdown(f"""
        <div style="background-color: {color}10; border-top: 4px solid {color};
                    padding: 16px; border-radius: 6px; min-height: 180px;">
            <strong style="color: {color}; font-size: 1.05em;">📌 Karakteristik</strong>
            <p style="margin-top: 8px; font-size: 0.92em; color: #333; line-height: 1.5;">
                {detail['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with about_col2:
        st.markdown(f"""
        <div style="background-color: {color}10; border-top: 4px solid {color};
                    padding: 16px; border-radius: 6px; min-height: 180px;">
            <strong style="color: {color}; font-size: 1.05em;">💼 Rekomendasi Instrumen</strong>
            <p style="margin-top: 8px; font-size: 0.92em; color: #333; line-height: 1.5;">
                {detail['instruments']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with about_col3:
        st.markdown(f"""
        <div style="background-color: {color}10; border-top: 4px solid {color};
                    padding: 16px; border-radius: 6px; min-height: 180px;">
            <strong style="color: {color}; font-size: 1.05em;">💡 Behavioral Tips</strong>
            <p style="margin-top: 8px; font-size: 0.92em; color: #333; line-height: 1.5;">
                {detail['tips']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.caption("⚠️ Rekomendasi di atas bersifat umum dan simulasi. "
            "Keputusan investasi akhir harus berkonsultasi dengan penasihat keuangan profesional. ")

    # ============================================================
    # SECTION 5: PROMINENT NAVIGATION BUTTONS
    # ============================================================

    st.markdown("---")
    st.subheader("🔍 Lihat Penjelasan Lengkap")

    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3498db20 0%, #3498db05 100%);
                    border: 2px solid #3498db; border-radius: 10px; padding: 20px;
                    text-align: center; min-height: 130px;">
            <div style="font-size: 2em;">🔍</div>
            <div style="color: #3498db; font-weight: bold; font-size: 1.1em; margin: 6px 0;">
                Lihat Penjelasan SHAP
            </div>
            <div style="color: #555; font-size: 0.9em;">
                Statistical layer — apa kontribusi setiap fitur ke prediksi
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Use page_link if available (Streamlit 1.32+)
        try:
            st.page_link("pages/3_🔍_SHAP_Explanation.py",
                        label="Buka SHAP Explanation →",
                        use_container_width=True)
        except Exception:
            st.caption("👉 Klik **🔍 SHAP Explanation** di sidebar")

    with nav_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #9b59b620 0%, #9b59b605 100%);
                    border: 2px solid #9b59b6; border-radius: 10px; padding: 20px;
                    text-align: center; min-height: 130px;">
            <div style="font-size: 2em;">⚖️</div>
            <div style="color: #9b59b6; font-weight: bold; font-size: 1.1em; margin: 6px 0;">
                Lihat KBS Rules
            </div>
            <div style="color: #555; font-size: 0.9em;">
                Domain knowledge layer — 15 rules berbasis literatur akademis
            </div>
        </div>
        """, unsafe_allow_html=True)
        try:
            st.page_link("pages/4_⚖️_KBS_Rules.py",
                         label="Buka KBS Rules →",
                         use_container_width=True)
        except Exception:
            st.caption("👉 Klik **⚖️ KBS Rules** di sidebar")

# ============================================================
# SIDEBAR — Last Prediction Summary
# ============================================================

if 'last_prediction' in st.session_state:
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📋 Last Prediction")
        last = st.session_state['last_prediction']
        color = RISK_COLORS[last['predicted_label']]

        st.markdown(f"""
        <div style="background-color: {color}20; border-left: 3px solid {color};
                    padding: 10px; border-radius: 4px;">
            <strong style="color: {color};">{last['predicted_label']}</strong><br>
            <small>Confidence: {last['confidence']:.1%}</small>
        </div>
        """, unsafe_allow_html=True)

        if 'last_prediction_id' in st.session_state:
            st.caption(f"🆔 `{st.session_state['last_prediction_id']}`")
            st.caption(f"🕐 {st.session_state['last_prediction_time']}")

        st.caption("Tersimpan untuk SHAP & KBS pages.")