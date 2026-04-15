import pandas as pd
import numpy as np

df = pd.read_csv('Finance_Trends.csv')

print('='*60)
print('1. BENTUK DATA (SHAPE)')
print('='*60)
print(f'Jumlah Baris: {df.shape[0]}')
print(f'Jumlah Kolom: {df.shape[1]}')

print('\n' + '='*60)
print('2. NAMA KOLOM & TIPE DATA')
print('='*60)
print(df.dtypes.to_string())

print('\n' + '='*60)
print('3. MISSING VALUES')
print('='*60)
missing = df.isnull().sum()
missing_pct = (df.isnull().mean() * 100).round(2)
missing_df = pd.DataFrame({'Missing Count': missing, 'Missing %': missing_pct})
has_missing = missing_df[missing_df['Missing Count'] > 0]
if len(has_missing) > 0:
    print(has_missing.to_string())
else:
    print('Tidak ada missing values!')

print('\n' + '='*60)
print('4. DUPLIKASI')
print('='*60)
print(f'Jumlah baris duplikat: {df.duplicated().sum()}')
print(f'Persentase duplikat: {(df.duplicated().mean()*100):.2f}%')

print('\n' + '='*60)
print('5. STATISTIK DESKRIPTIF (NUMERIK)')
print('='*60)
print(df.describe().to_string())

print('\n' + '='*60)
print('6. STATISTIK DESKRIPTIF (KATEGORIKAL)')
print('='*60)
print(df.describe(include='object').to_string())

print('\n' + '='*60)
print('7. UNIQUE VALUES PER KOLOM')
print('='*60)
for col in df.columns:
    unique_count = df[col].nunique()
    if unique_count <= 15:
        print(f'\n--- {col} ({unique_count} unique) ---')
        print(df[col].value_counts().to_string())
    else:
        print(f'\n--- {col} ({unique_count} unique) --- [terlalu banyak, tampilkan top 10]')
        print(df[col].value_counts().head(10).to_string())

print('\n' + '='*60)
print('8. IDENTIFIKASI TIPE KOLOM')
print('='*60)
numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
print(f'Kolom Numerik ({len(numerical_cols)}): {numerical_cols}')
print(f'Kolom Kategorikal ({len(categorical_cols)}): {categorical_cols}')

print('\n' + '='*60)
print('9. KORELASI ANTAR VARIABEL NUMERIK')
print('='*60)
print(df[numerical_cols].corr().round(3).to_string())
