# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
# ]
# ///

"""Analyze container collection time data."""

import pandas as pd

df = pd.read_csv('../../NB_hackathon_2025-main/Nilufer_bin_collection_dataset/container_collect_time.csv')

print("=" * 70)
print("CONTAINER COLLECTION TIME DATA ANALYSIS")
print("=" * 70)

print(f"\nTotal rows: {len(df):,}")
print(f"\nColumns: {list(df.columns)}")

print(f"\n\nUnique neighborhoods: {df['mahalle'].nunique()}")
print(f"Date range: {df['tarih'].min()} to {df['tarih'].max()}")
print(f"Hour range: {df['saat'].min()} to {df['saat'].max()}")

print("\n\nNeighborhood types:")
print(df['mahalle_tipi'].value_counts())

print("\n\nCollection time flag (toplama_saati):")
print(df['toplama_saati'].value_counts())

print("\n\nSample data statistics:")
print(df[['cop_yogunlugu_kg', 'konteyner_doluluk_orani', 'toplam_konteyner']].describe())

print("\n\nDay types (gun_tipi):")
print(df['gun_tipi'].value_counts())

print("\n\nContainer type breakdown (first 5 neighborhoods):")
for mahalle in df['mahalle'].unique()[:5]:
    mdf = df[df['mahalle'] == mahalle].iloc[0]
    print(f"\n{mahalle}:")
    print(f"  Underground: {mdf['yeralti_konteyner']}")
    print(f"  770L: {mdf['konteyner_770lt']}")
    print(f"  400L: {mdf['konteyner_400lt']}")
    print(f"  Plastic: {mdf['plastik_konteyner']}")
    print(f"  Total: {mdf['toplam_konteyner']}")
    print(f"  Type: {mdf['mahalle_tipi']}")
    print(f"  Population: {mdf['nufus']}")

print("\n\n" + "=" * 70)
print("WASTE ACCUMULATION PATTERNS")
print("=" * 70)

# Analyze when containers fill up
print("\nAverage waste accumulation by hour:")
hourly = df.groupby('saat')['cop_yogunlugu_kg'].mean()
print(hourly)

print("\n\nAverage fullness ratio by hour:")
fullness = df.groupby('saat')['konteyner_doluluk_orani'].mean()
print(fullness)

print("\n\nPeak accumulation hours (when fullness > 0.8):")
peak_hours = df[df['konteyner_doluluk_orani'] > 0.8].groupby('saat').size()
print(peak_hours)

print("\n\nCollection recommendations by neighborhood type:")
for ntype in df['mahalle_tipi'].unique():
    type_df = df[df['mahalle_tipi'] == ntype]
    avg_fullness = type_df.groupby('saat')['konteyner_doluluk_orani'].mean()
    # Find first hour when average fullness > 0.7
    critical_hour = avg_fullness[avg_fullness > 0.7].index.min() if any(avg_fullness > 0.7) else None
    print(f"\n{ntype.upper()}:")
    print(f"  Critical hour (>70% full): {critical_hour if critical_hour else 'Never reaches 70%'}")
    print(f"  Max fullness: {type_df['konteyner_doluluk_orani'].max():.2%}")
    print(f"  Total containers: {type_df['toplam_konteyner'].iloc[0]:,}")
