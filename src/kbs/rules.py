"""
Knowledge-Based System Rules Engine
====================================

15 rules dalam 5 kategori untuk natural language explanation
investment intention prediction.

Penulis: Naufal Rizki Abyan (23082010235)
Proyek: Transparent Investment Intention Analysis
"""


def apply_kbs_rules(features):
    """
    Apply 15 KBS rules ke customer features.

    Parameters
    ----------
    features : pd.Series, dict, atau numpy array dengan feature names
        Feature values untuk 1 customer (33 features)

    Returns
    -------
    list of dict
        Triggered rules dengan keys: rule_id, category, finding, implication, reference
    """
    triggered = []
    f = features

    def get_val(key, default=0):
        if hasattr(f, "get"):
            return f.get(key, default)
        try:
            return f[key]
        except (KeyError, IndexError):
            return default

    # === CATEGORY 1: Capacity Assessment (4 rules) ===
    cap = get_val("investmentCapacity", 0)

    if cap == 0:
        triggered.append({
            "rule_id": "R1.1",
            "category": "Capacity Assessment",
            "finding": "Investment capacity rendah (<30K EUR)",
            "implication": "Profil cenderung Conservative atau Income untuk preservation modal",
            "reference": "MiFID II Article 25 - Suitability Assessment"
        })
    elif cap == 3:
        triggered.append({
            "rule_id": "R1.2",
            "category": "Capacity Assessment",
            "finding": "Investment capacity tinggi (>300K EUR)",
            "implication": "Memungkinkan profil Aggressive dengan toleransi risiko lebih tinggi",
            "reference": "Modern Portfolio Theory (Markowitz, 1952)"
        })
    elif cap in [1, 2]:
        triggered.append({
            "rule_id": "R1.3",
            "category": "Capacity Assessment",
            "finding": "Investment capacity menengah (30K-300K EUR)",
            "implication": "Profil Balanced atau Income paling sesuai",
            "reference": "Lifecycle Investment Theory"
        })

    has_q = get_val("has_questionnaire", 0)
    if has_q == 0:
        triggered.append({
            "rule_id": "R1.4",
            "category": "Capacity Assessment",
            "finding": "Customer tidak memiliki questionnaire yang lengkap",
            "implication": "Risk profile dengan reliabilitas terbatas - rekomendasi perlu dilengkapi assessment",
            "reference": "MiFID II Article 25(2) - Suitability Information"
        })

    # === CATEGORY 2: Trading Behavior (4 rules) ===
    buy_ratio = get_val("buy_ratio", 0.5)
    sell_buy_ratio = get_val("sell_to_buy_value_ratio", 1.0)
    total_inv = get_val("total_invested", 0)

    if buy_ratio > 0.65:
        triggered.append({
            "rule_id": "R2.1",
            "category": "Trading Behavior",
            "finding": f"Buy ratio tinggi ({buy_ratio:.2f}) - dominant accumulator",
            "implication": "Long-term investor mindset, konsisten dengan Aggressive/Balanced",
            "reference": "Disposition Effect (Shefrin & Statman, 1985)"
        })
    elif buy_ratio < 0.40:
        triggered.append({
            "rule_id": "R2.2",
            "category": "Trading Behavior",
            "finding": f"Sell ratio dominan (buy ratio={buy_ratio:.2f})",
            "implication": "Profit-taking behavior, konsisten dengan Income atau Conservative",
            "reference": "Disposition Effect (Shefrin & Statman, 1985)"
        })

    if sell_buy_ratio > 1.5:
        triggered.append({
            "rule_id": "R2.3",
            "category": "Trading Behavior",
            "finding": f"Net seller: total sold > 1.5x total invested ({sell_buy_ratio:.2f})",
            "implication": "Behavior divestasi - perlu review apakah konsisten dengan profil",
            "reference": "Behavioral Finance - Loss Aversion (Kahneman & Tversky, 1979)"
        })

    if total_inv > 18853:
        triggered.append({
            "rule_id": "R2.4",
            "category": "Trading Behavior",
            "finding": f"Total invested tinggi (>18.853 EUR, top 25%)",
            "implication": "High exposure - mendukung profil Aggressive atau Balanced",
            "reference": "Behavioral Finance - Endowment Effect"
        })

    # === CATEGORY 3: Portfolio Diversification (3 rules) ===
    n_stocks = get_val("unique_stocks_traded", 0)
    n_sectors = get_val("unique_sectors_traded", 0)

    if n_stocks >= 5:
        triggered.append({
            "rule_id": "R3.1",
            "category": "Portfolio Diversification",
            "finding": f"Portfolio terdiversifikasi ({int(n_stocks)} unique stocks)",
            "implication": "Risk management mature, konsisten dengan Balanced atau Aggressive",
            "reference": "Modern Portfolio Theory - Diversification (Markowitz, 1952)"
        })
    elif n_stocks == 1:
        triggered.append({
            "rule_id": "R3.2",
            "category": "Portfolio Diversification",
            "finding": "Portfolio terkonsentrasi pada 1 saham",
            "implication": "High idiosyncratic risk - tidak konsisten dengan Conservative",
            "reference": "Modern Portfolio Theory - Diversification"
        })

    if n_sectors >= 3:
        triggered.append({
            "rule_id": "R3.3",
            "category": "Portfolio Diversification",
            "finding": f"Sector diversification baik ({int(n_sectors)} sektor berbeda)",
            "implication": "Risk diversification cross-sectoral yang efektif",
            "reference": "Modern Portfolio Theory"
        })

    # === CATEGORY 4: Temporal Pattern (2 rules) ===
    period = get_val("investment_period_days", 0)
    avg_gap = get_val("avg_days_between_transactions", 0)

    if period > 1583:
        triggered.append({
            "rule_id": "R4.1",
            "category": "Temporal Pattern",
            "finding": f"Long-term investor ({int(period)} hari aktif)",
            "implication": "Konsistensi jangka panjang - lebih mungkin Balanced atau Income",
            "reference": "Lifecycle Investment Theory"
        })

    if avg_gap < 39.7 and avg_gap > 0:
        triggered.append({
            "rule_id": "R4.2",
            "category": "Temporal Pattern",
            "finding": f"High-frequency trader (gap rata-rata {avg_gap:.0f} hari)",
            "implication": "Active trader pattern - konsisten dengan Aggressive",
            "reference": "Behavioral Finance - Overconfidence Bias (Barber & Odean, 2001)"
        })

    # === CATEGORY 5: Channel & Segment (2 rules) ===
    digital = get_val("digital_ratio", 0)
    is_premium = get_val("customerType_Premium", 0) == 1

    if digital > 0.75:
        triggered.append({
            "rule_id": "R5.1",
            "category": "Channel Preference",
            "finding": f"High digital adoption ({digital:.0%} via Internet Banking)",
            "implication": "Tech-savvy investor - berkorelasi dengan Aggressive (younger demographic)",
            "reference": "Diffusion of Innovation Theory (Rogers, 2003)"
        })

    if is_premium:
        triggered.append({
            "rule_id": "R5.2",
            "category": "Customer Segment",
            "finding": "Premium customer (high net worth)",
            "implication": "Akses ke advisory yang lebih sofistikat, profil bisa Aggressive/Balanced",
            "reference": "MiFID II Article 25 - Client Categorization"
        })

    return triggered


def get_rules_by_category(rules):
    """Group rules by category for display."""
    by_category = {}
    for r in rules:
        by_category.setdefault(r["category"], []).append(r)
    return by_category
