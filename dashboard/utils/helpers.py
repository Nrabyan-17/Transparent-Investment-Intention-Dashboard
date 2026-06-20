"""
helpers.py
==========
Utility functions untuk dashboard.

Modul ini berisi:
- Loading model, encoder, dan data (dengan @st.cache_resource)
- SHAP explainer loading
- KBS rules wrapper
- Common UI helpers
- Custom CSS untuk glassmorphism look
- Plotly chart factories (interaktif & cantik)

Penulis: Naufal Rizki Abyan (23082010235)
"""

import sys
import json
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# PATH SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / 'models'
DATA_DIR = PROJECT_ROOT / 'data' / 'processed'
REPORT_DIR = PROJECT_ROOT / 'reports'

sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# COLOR PALETTE
# ============================================================

COLORS = {
    'primary': '#2E86AB',
    'secondary': '#1abc9c',
    'success': '#52B788',
    'warning': '#F4A261',
    'danger': '#E63946',
    'info': '#3498db',
    'bg_light': '#f5f7fa',
    'text_dark': '#2c3e50',
    'text_muted': '#7f8c8d',
}

RISK_COLORS = {
    'Conservative': '#2E86AB',
    'Income': '#52B788',
    'Balanced': '#F4A261',
    'Aggressive': '#E63946'
}

RISK_DESCRIPTIONS = {
    'Conservative': 'Profil paling defensif. Prioritas preservasi modal, toleransi risiko rendah.',
    'Income': 'Profil pendapatan stabil. Fokus pada dividen dan instrumen low-volatility.',
    'Balanced': 'Profil seimbang. Kombinasi growth dan stability.',
    'Aggressive': 'Profil pertumbuhan agresif. Toleransi risiko tinggi untuk return maksimal.'
}


# ============================================================
# CUSTOM CSS — GLASSMORPHISM STYLE
# ============================================================

def inject_custom_css():
    """Inject custom CSS untuk glassmorphism look. Call di awal setiap page."""
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #e8ecf2 0%, #f5f7fa 50%, #e0e7ee 100%);
            background-attachment: fixed;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }
        
        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        section[data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }
        
        h1, h2, h3 {
            color: #2c3e50;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-weight: 700;
        }
        
        h1 {
            font-size: 2.2em;
            background: linear-gradient(90deg, #2E86AB 0%, #1abc9c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.3em;
        }
        
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.5);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(31, 38, 135, 0.15);
        }
        
        [data-testid="stMetricLabel"] {
            color: #7f8c8d;
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        [data-testid="stMetricValue"] {
            color: #2E86AB;
            font-weight: 700;
            font-size: 1.8em;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #2E86AB 0%, #1abc9c 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 24px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(46, 134, 171, 0.3);
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(46, 134, 171, 0.4);
        }
        
        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            margin: 8px 0;
        }
        
        [data-baseweb="tab-list"] {
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 4px;
            gap: 4px;
        }
        
        [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px;
            color: #2c3e50;
            font-weight: 500;
        }
        
        [data-baseweb="tab"][aria-selected="true"] {
            background: rgba(46, 134, 171, 0.1);
            color: #2E86AB;
        }
        
        [data-testid="stDataFrame"] {
            background: rgba(255, 255, 255, 0.6);
            border-radius: 12px;
            padding: 8px;
            border: 1px solid rgba(255, 255, 255, 0.4);
        }
        
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {
            background: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        
        [data-testid="stAlert"] {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border-left: 4px solid #2E86AB;
        }
        
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(46, 134, 171, 0.3), transparent);
            margin: 24px 0;
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #2E86AB 0%, #1abc9c 100%);
        }
    </style>
    """, unsafe_allow_html=True)


def glass_card(content, padding="20px", margin="10px 0"):
    return f"""
    <div style="
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: {padding};
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.08);
        margin: {margin};
    ">
        {content}
    </div>
    """


def section_header(title, subtitle=None, icon=""):
    subtitle_html = f'<div style="color: #7f8c8d; font-size: 0.95em; margin-top: 4px;">{subtitle}</div>' if subtitle else ''
    return f"""
    <div style="margin: 24px 0 16px 0;">
        <h2 style="color: #2c3e50; font-weight: 700; margin: 0; font-size: 1.5em;">{icon} {title}</h2>
        {subtitle_html}
    </div>
    """


# ============================================================
# CACHED LOADERS
# ============================================================

@st.cache_resource
def load_model():
    return joblib.load(MODEL_DIR / 'best_model.pkl')


@st.cache_resource
def load_label_encoder():
    return joblib.load(MODEL_DIR / 'label_encoder.pkl')


@st.cache_resource
def load_shap_explainer():
    return joblib.load(MODEL_DIR / 'shap_explainer.pkl')


@st.cache_data
def load_metadata():
    with open(MODEL_DIR / 'model_metadata.json') as f:
        return json.load(f)


@st.cache_data
def load_test_data():
    X_test = pd.read_csv(DATA_DIR / 'X_test.csv')
    y_test = pd.read_csv(DATA_DIR / 'y_test.csv').values.ravel()
    return X_test, y_test


@st.cache_data
def load_train_data():
    X_train = pd.read_csv(DATA_DIR / 'X_train.csv')
    y_train = pd.read_csv(DATA_DIR / 'y_train.csv').values.ravel()
    return X_train, y_train


@st.cache_data
def load_shap_precomputed():
    data = np.load(MODEL_DIR / 'shap_values_test.npz')
    return {
        'shap_values_3d': data['shap_values_3d'],
        'sample_indices': data['sample_indices'],
        'expected_value': data['expected_value']
    }


@st.cache_data
def load_feature_stats():
    X_train, _ = load_train_data()
    stats = {}
    for col in X_train.columns:
        stats[col] = {
            'median': float(X_train[col].median()),
            'mean': float(X_train[col].mean()),
            'min': float(X_train[col].min()),
            'max': float(X_train[col].max()),
            'q25': float(X_train[col].quantile(0.25)),
            'q75': float(X_train[col].quantile(0.75)),
        }
    return stats


@st.cache_resource
def get_kbs_function():
    from src.kbs.rules import apply_kbs_rules, get_rules_by_category
    return apply_kbs_rules, get_rules_by_category


# ============================================================
# PREDICTION & EXPLANATION
# ============================================================

def predict_customer(features_dict_or_series, model=None, label_encoder=None):
    if model is None:
        model = load_model()
    if label_encoder is None:
        label_encoder = load_label_encoder()
    
    if isinstance(features_dict_or_series, dict):
        df = pd.DataFrame([features_dict_or_series])
    elif isinstance(features_dict_or_series, pd.Series):
        df = features_dict_or_series.to_frame().T
    else:
        df = features_dict_or_series
    
    pred_idx = int(model.predict(df)[0])
    proba = model.predict_proba(df)[0]
    label_names = list(label_encoder.classes_)
    
    return {
        'predicted_label': label_names[pred_idx],
        'predicted_idx': pred_idx,
        'probabilities': {label_names[i]: float(proba[i]) for i in range(len(label_names))},
        'confidence': float(proba[pred_idx])
    }


def get_shap_explanation(features_df, model=None, explainer=None):
    if model is None:
        model = load_model()
    if explainer is None:
        explainer = load_shap_explainer()
    
    pred_idx = int(model.predict(features_df)[0])
    shap_values = explainer.shap_values(features_df)
    
    if isinstance(shap_values, list):
        sv_for_pred = shap_values[pred_idx][0]
        expected_val = explainer.expected_value[pred_idx] if hasattr(explainer.expected_value, '__len__') else explainer.expected_value
    else:
        sv_for_pred = shap_values[0, :, pred_idx]
        expected_val = explainer.expected_value[pred_idx] if hasattr(explainer.expected_value, '__len__') else explainer.expected_value
    
    feature_names = features_df.columns.tolist()
    sv_abs = np.abs(sv_for_pred)
    top_idx = np.argsort(sv_abs)[::-1][:10]
    
    top_features = []
    for i in top_idx:
        top_features.append({
            'feature': feature_names[i],
            'value': float(features_df.iloc[0, i]),
            'shap_value': float(sv_for_pred[i]),
            'direction': '↑' if sv_for_pred[i] > 0 else '↓'
        })
    
    return {
        'shap_values': sv_for_pred,
        'expected_value': float(expected_val),
        'predicted_idx': pred_idx,
        'top_features': top_features,
        'feature_names': feature_names
    }


# ============================================================
# PLOTLY CHART FACTORIES
# ============================================================

def plotly_layout_defaults():
    return dict(
        plot_bgcolor='rgba(255,255,255,0)',
        paper_bgcolor='rgba(255,255,255,0)',
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
                  color='#2c3e50', size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="sans-serif"),
    )


def plot_donut_distribution(data_dict, title="Distribution"):
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    colors_list = [RISK_COLORS.get(l, '#888') for l in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.6,
        marker=dict(colors=colors_list, line=dict(color='white', width=3)),
        textfont=dict(size=14, color='white', family='sans-serif'),
        textposition='outside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>',
    )])
    
    fig.update_layout(
        **plotly_layout_defaults(),
        title=dict(text=title, font=dict(size=16, color='#2c3e50', family='sans-serif')),
        showlegend=False,
        annotations=[dict(
            text=f'<b>{sum(values):,}</b><br><span style="font-size:12px;color:#7f8c8d">Total</span>',
            x=0.5, y=0.5, font=dict(size=18, color='#2c3e50'),
            showarrow=False
        )],
        height=400,
    )
    return fig


def plot_horizontal_bar(data_series, title="Top Features", show_values=True):
    x = data_series.values
    y = data_series.index.tolist()
    min_v, max_v = float(min(x)), float(max(x))
    rng = max_v - min_v + 1e-10
    colors_gradient = [
        f'rgba(46, 134, 171, {0.3 + 0.7 * (v - min_v) / rng})'
        for v in x
    ]
    fig = go.Figure(go.Bar(
        x=x, y=y, orientation='h',
        marker=dict(color=colors_gradient, line=dict(color='white', width=1)),
        text=[f'{v:.4f}' for v in x] if show_values else None,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Value: %{x:.4f}<extra></extra>',
    ))
    fig.update_layout(
        **plotly_layout_defaults(),
        title=dict(text=title, font=dict(size=15, color='#2c3e50')),
        xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False),
        yaxis=dict(showgrid=False, automargin=True),
        height=max(300, len(data_series) * 35),
    )
    return fig


def plot_probability_bars(probabilities_dict, title="Prediction Confidence"):
    sorted_items = sorted(probabilities_dict.items(), key=lambda x: x[1])
    labels = [x[0] for x in sorted_items]
    values = [x[1] for x in sorted_items]
    colors_list = [RISK_COLORS.get(l, '#888') for l in labels]
    
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation='h',
        marker=dict(color=colors_list, line=dict(color='white', width=2)),
        text=[f'{v:.1%}' for v in values],
        textposition='outside',
        textfont=dict(size=13, color='#2c3e50'),
        hovertemplate='<b>%{y}</b><br>Probability: %{x:.2%}<extra></extra>',
    ))
    
    fig.update_layout(
        **plotly_layout_defaults(),
        title=dict(text=title, font=dict(size=15, color='#2c3e50')),
        xaxis=dict(
            range=[0, max(values) * 1.25],
            tickformat='.0%',
            showgrid=True, gridcolor='rgba(0,0,0,0.05)',
            zeroline=False,
        ),
        yaxis=dict(showgrid=False),
        height=320,
    )
    return fig


def plot_model_comparison(metrics_df, metrics_to_plot=None):
    if metrics_to_plot is None:
        metrics_to_plot = ['Test Accuracy', 'Precision (macro)', 'Recall (macro)', 'F1-Score (macro)']
    
    models = metrics_df.index.tolist()
    colors_models = ['#2E86AB', '#52B788', '#E63946']
    
    fig = go.Figure()
    for i, model in enumerate(models):
        values = [metrics_df.loc[model, m] for m in metrics_to_plot]
        fig.add_trace(go.Bar(
            name=model,
            x=metrics_to_plot,
            y=values,
            marker=dict(color=colors_models[i % len(colors_models)],
                        line=dict(color='white', width=1)),
            text=[f'{v:.3f}' for v in values],
            textposition='outside',
            hovertemplate=f'<b>{model}</b><br>%{{x}}: %{{y:.4f}}<extra></extra>',
        ))
    
    fig.update_layout(
        **plotly_layout_defaults(),
        title=dict(text='Model Performance Comparison', font=dict(size=16)),
        barmode='group',
        xaxis=dict(showgrid=False),
        yaxis=dict(range=[0, 1], showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickformat='.0%'),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        height=450,
    )
    return fig


def plot_shap_local(top_features_list, pred_label, title=None):
    sorted_feats = sorted(top_features_list, key=lambda x: x['shap_value'])
    
    feature_labels = [
        f"{f['feature']}<br><span style='font-size:10px;color:#888'>val: {f['value']:.2f}</span>"
        for f in sorted_feats
    ]
    shap_vals = [f['shap_value'] for f in sorted_feats]
    colors_signed = ['#27ae60' if v > 0 else '#e74c3c' for v in shap_vals]
    
    fig = go.Figure(go.Bar(
        x=shap_vals, y=feature_labels, orientation='h',
        marker=dict(color=colors_signed, line=dict(color='white', width=1)),
        text=[f'{v:+.4f}' for v in shap_vals],
        textposition='outside',
        textfont=dict(size=11),
        hovertemplate='<b>%{y}</b><br>SHAP: %{x:+.4f}<extra></extra>',
    ))
    
    title_text = title or f'Top Features Contributing to "{pred_label}" Prediction'
    fig.update_layout(
        **plotly_layout_defaults(),
        title=dict(text=title_text, font=dict(size=14)),
        xaxis=dict(
            title='SHAP Value (impact on prediction)',
            showgrid=True, gridcolor='rgba(0,0,0,0.05)',
            zeroline=True, zerolinecolor='rgba(0,0,0,0.3)',
        ),
        yaxis=dict(showgrid=False, automargin=True),
        height=500,
        showlegend=False,
    )
    return fig


def plot_kbs_implications(implication_signals, predicted_label):
    classes = list(implication_signals.keys())
    counts = list(implication_signals.values())
    colors_list = [RISK_COLORS.get(c, '#888') for c in classes]
    line_widths = [4 if c == predicted_label else 1 for c in classes]
    line_colors = ['black' if c == predicted_label else 'white' for c in classes]
    
    fig = go.Figure(go.Bar(
        x=counts, y=classes, orientation='h',
        marker=dict(color=colors_list, line=dict(color=line_colors, width=line_widths)),
        text=[f'<b>{c}</b>' for c in counts],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Rules pointing to this: %{x}<extra></extra>',
    ))
    
    fig.update_layout(
        **plotly_layout_defaults(),
        title=dict(text='KBS Rules Implications by Class', font=dict(size=14)),
        xaxis=dict(title='# Rules pointing to this class', showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(showgrid=False),
        height=300,
        showlegend=False,
    )
    return fig


# ============================================================
# UI HELPERS
# ============================================================

def render_risk_badge(risk_level):
    color = RISK_COLORS.get(risk_level, '#888888')
    return f"""
    <span style="
        background: linear-gradient(135deg, {color} 0%, {color}cc 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        box-shadow: 0 2px 8px {color}40;
    ">{risk_level}</span>
    """


def render_big_prediction_card(pred_label, confidence, true_label=None):
    color = RISK_COLORS.get(pred_label, '#888')
    
    true_html = ""
    if true_label:
        is_correct = (pred_label == true_label)
        mark = "✓ CORRECT" if is_correct else "✗ INCORRECT"
        mark_color = "#27ae60" if is_correct else "#e74c3c"
        true_html = f"""
        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.1);">
            <div style="color: #7f8c8d; font-size: 12px;">GROUND TRUTH</div>
            <div style="color: {RISK_COLORS.get(true_label, '#888')}; font-weight: bold; font-size: 18px; margin: 4px 0;">
                {true_label}
            </div>
            <div style="color: {mark_color}; font-weight: bold; font-size: 14px;">{mark}</div>
        </div>
        """
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {color}25 0%, {color}08 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 2px solid {color}50;
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        box-shadow: 0 8px 32px {color}20;
    ">
        <div style="color: #7f8c8d; font-size: 12px; letter-spacing: 1.5px; margin-bottom: 12px;">
            PREDICTED RISK PROFILE
        </div>
        <div style="color: {color}; font-size: 40px; font-weight: 800; line-height: 1;">
            {pred_label}
        </div>
        <div style="margin-top: 16px;">
            <span style="color: #7f8c8d; font-size: 14px;">Confidence: </span>
            <span style="color: #2c3e50; font-weight: 700; font-size: 22px;">{confidence:.1%}</span>
        </div>
        {true_html}
    </div>
    """


def render_stat_card(value, label, icon=None, color='#2E86AB'):
    icon_html = f'<div style="font-size: 28px; margin-bottom: 8px;">{icon}</div>' if icon else ''
    return f"""
    <div style="
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 24px 20px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 8px 24px rgba(31, 38, 135, 0.08);
        text-align: center;
        transition: transform 0.2s ease;
    ">
        {icon_html}
        <div style="
            font-size: 2em;
            font-weight: 700;
            background: linear-gradient(135deg, {color} 0%, {color}aa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        ">{value}</div>
        <div style="
            color: #7f8c8d;
            font-size: 0.9em;
            font-weight: 500;
            margin-top: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">{label}</div>
    </div>
    """
