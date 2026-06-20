# Transparent Investment Intention Dashboard

**Decision Support System** berbasis Streamlit yang mengintegrasikan ML + SHAP + KBS.

**Penulis:** Naufal Rizki Abyan (23082010235)  
**Proyek:** Magang Riset — Universitas Pembangunan Nasional "Veteran" Jawa Timur

---

## Prerequisite

Pastikan semua notebook sudah dijalankan **sebelum** menjalankan dashboard:

```
✅ 02_preprocessing.ipynb   → menghasilkan data/processed/ + models/label_encoder.pkl
✅ 03_modeling.ipynb        → menghasilkan models/best_model.pkl + model_metadata.json
✅ 04_explainability.ipynb  → menghasilkan models/shap_explainer.pkl + src/kbs/rules.py
```

## Cara Install Dependencies

```bash
# Dari folder project root (bukan dari dashboard/)
pip install -r dashboard/requirements.txt
```

## Cara Menjalankan Dashboard

```bash
# Dari folder project ROOT (bukan dari dashboard/)
streamlit run dashboard/app.py
```

Dashboard akan terbuka di browser: `http://localhost:8501`

## Struktur Halaman

| Halaman | Fungsi | DSS Subsystem |
|---------|--------|---------------|
| 🏠 Home | Intro & navigasi | Dialog |
| 📊 Overview | Dataset stats & model performance | Data |
| 🎯 Prediction | Prediksi risk profile (dual input mode) | Model |
| 🔍 SHAP Explanation | Statistical explainability | Model |
| ⚖️ KBS Rules | Domain knowledge explanation | Model |

## Struktur File

```
dashboard/
├── app.py                    # Entry point (Home page)
├── requirements.txt          # Dependencies
├── README.md                 # File ini
├── pages/
│   ├── 1_📊_Overview.py
│   ├── 2_🎯_Prediction.py
│   ├── 3_🔍_SHAP_Explanation.py
│   └── 4_⚖️_KBS_Rules.py
└── utils/
    ├── __init__.py
    └── helpers.py            # Shared functions & cache loaders
```

## Troubleshooting

**Error: `ModuleNotFoundError: No module named 'src'`**
→ Pastikan jalankan dari **project root**, bukan dari folder `dashboard/`

**Error: `shap_explainer.pkl not found`**
→ Jalankan dulu `04_explainability.ipynb`

**Error: `best_model.pkl not found`**
→ Jalankan dulu `03_modeling.ipynb`

**SHAP page menampilkan data tidak akurat**
→ Mock SHAP file terdeteksi. Jalankan `04_explainability.ipynb` untuk generate real SHAP values.
