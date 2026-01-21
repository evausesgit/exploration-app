"""Check: Do companies with known SIRENE codes have matching payroll estimates?

Hypothesis: Well-managed companies keep SIRENE updated, so when code != NN,
it should roughly match payroll-based estimate.
"""
import duckdb

con = duckdb.connect()

# SIRENE bracket midpoints
BRACKET_MIDPOINTS = {
    '00': 0,
    '01': 1.5,   # 1-2
    '02': 4,     # 3-5
    '03': 7.5,   # 6-9
    '11': 14.5,  # 10-19
    '12': 34.5,  # 20-49
    '21': 74.5,  # 50-99
    '22': 149.5, # 100-199
    '31': 249.5, # 200-249
    '32': 374.5, # 250-499
    '41': 749.5, # 500-999
    '42': 1499.5, # 1000-1999
    '51': 3499.5, # 2000-4999
    '52': 7499.5, # 5000-9999
    '53': 10000,  # 10000+
}

query = """
WITH latest AS (
    SELECT siren, charges_personnel,
           ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel > 0
),
combined AS (
    SELECT
        a.siren,
        s.denomination,
        s.tranche_effectifs as sirene_code,
        a.charges_personnel,
        round(a.charges_personnel / 70000, 0) as est_employees_70k,
        round(a.charges_personnel / 50000, 0) as est_employees_50k,
        round(a.charges_personnel / 100000, 0) as est_employees_100k
    FROM latest a
    JOIN (SELECT siren, denomination, tranche_effectifs
          FROM read_parquet('data/parquet/sirene_unites_legales.parquet')) s
        ON a.siren = s.siren
    WHERE a.rn = 1
      AND s.tranche_effectifs NOT IN ('NN', '')
      AND s.tranche_effectifs IS NOT NULL
)
SELECT * FROM combined
WHERE est_employees_70k > 0
"""

df = con.execute(query).df()

print("=" * 100)
print("COMPARING SIRENE BRACKETS VS PAYROLL-BASED ESTIMATES")
print("=" * 100)

# Add SIRENE midpoint
df['sirene_midpoint'] = df['sirene_code'].map(BRACKET_MIDPOINTS)
df = df.dropna(subset=['sirene_midpoint'])

# Calculate ratio: payroll estimate / SIRENE midpoint
df['ratio_70k'] = df['est_employees_70k'] / df['sirene_midpoint']
df['ratio_50k'] = df['est_employees_50k'] / df['sirene_midpoint']
df['ratio_100k'] = df['est_employees_100k'] / df['sirene_midpoint']

# Filter out zeros
df = df[df['sirene_midpoint'] > 0]

print(f"\nTotal companies with known SIRENE code: {len(df):,}")
print()

# Accuracy by bracket
print("ACCURACY BY SIRENE BRACKET (ratio = payroll_estimate / sirene_midpoint)")
print("-" * 80)
print("If SIRENE is accurate: ratio should be ~1.0")
print("If ratio >> 1: SIRENE is UNDERSTATING employees (stale data)")
print("If ratio << 1: SIRENE is OVERSTATING employees (or high-wage sector)")
print()

for code in sorted(BRACKET_MIDPOINTS.keys()):
    subset = df[df['sirene_code'] == code]
    if len(subset) >= 10:
        median_ratio = subset['ratio_70k'].median()
        pct_close = len(subset[(subset['ratio_70k'] > 0.5) & (subset['ratio_70k'] < 2)]) / len(subset) * 100
        print(f"  {code} ({BRACKET_MIDPOINTS[code]:>6.0f} emp): "
              f"n={len(subset):>6,}  "
              f"median_ratio={median_ratio:>5.1f}  "
              f"within_2x={pct_close:>5.1f}%")

print()
print()

# Show extreme mismatches
print("EXTREME MISMATCHES: SIRENE says small, payroll says big")
print("-" * 80)
mismatches = df[(df['sirene_code'].isin(['01', '02', '03'])) & (df['est_employees_70k'] > 50)]
mismatches = mismatches.sort_values('est_employees_70k', ascending=False).head(20)
print(mismatches[['siren', 'denomination', 'sirene_code', 'est_employees_70k', 'charges_personnel']].to_string())

print()
print()

# Show well-matched examples
print("WELL-MATCHED: SIRENE and payroll agree (ratio 0.8-1.2)")
print("-" * 80)
matched = df[(df['ratio_70k'] > 0.8) & (df['ratio_70k'] < 1.2) & (df['est_employees_70k'] > 10)]
matched = matched.sample(min(20, len(matched)))
print(matched[['siren', 'denomination', 'sirene_code', 'sirene_midpoint', 'est_employees_70k', 'ratio_70k']].to_string())

print()
print()

# Summary stats
print("SUMMARY: How often does SIRENE match payroll estimate?")
print("-" * 80)
for threshold in [0.5, 1.0, 2.0]:
    within = len(df[(df['ratio_70k'] > 1/threshold) & (df['ratio_70k'] < threshold)]) / len(df) * 100
    print(f"  Within {threshold}x: {within:.1f}%")
