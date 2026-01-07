"""Find gems using ACTUAL ratios - no assumed employee cost needed.

The real metrics that matter:
- profit / payroll  = profit per euro spent on staff
- profit / revenue  = profit margin
- revenue / payroll = revenue efficiency

These are ACTUAL data, no assumptions.
"""
import duckdb

con = duckdb.connect()

query = """
WITH latest_accounts AS (
    SELECT
        siren,
        date_cloture,
        chiffre_affaires,
        charges_personnel,
        resultat_net,
        ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel > 0
      AND resultat_net IS NOT NULL
      AND chiffre_affaires > 0
),
company_info AS (
    SELECT
        siren,
        denomination as nom,
        activite_principale as naf_code
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
)
SELECT
    a.siren,
    c.nom,
    c.naf_code,
    a.date_cloture,

    -- Raw financials (millions)
    round(a.chiffre_affaires / 1e6, 2) as revenue_M,
    round(a.charges_personnel / 1e6, 2) as payroll_M,
    round(a.resultat_net / 1e6, 2) as profit_M,

    -- ACTUAL RATIOS - no assumptions needed
    round(a.resultat_net / a.charges_personnel, 2) as profit_per_payroll_euro,
    round(a.chiffre_affaires / a.charges_personnel, 1) as revenue_per_payroll_euro,
    round(100 * a.resultat_net / a.chiffre_affaires, 1) as profit_margin_pct

FROM latest_accounts a
LEFT JOIN company_info c ON a.siren = c.siren
WHERE a.rn = 1
  AND a.resultat_net > 0
  AND a.resultat_net < a.chiffre_affaires  -- Not a holding
  AND c.naf_code NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z')  -- Not holdings
  -- Mid-sized by payroll
  AND a.charges_personnel BETWEEN 500000 AND 15000000
  -- Reasonable revenue
  AND a.chiffre_affaires BETWEEN 1000000 AND 100000000
  -- Healthy margin
  AND (100.0 * a.resultat_net / a.chiffre_affaires) BETWEEN 5 AND 45
ORDER BY profit_per_payroll_euro DESC
LIMIT 50
"""

print("=" * 130)
print("GEMS BY PROFIT/PAYROLL RATIO (no employee estimate needed)")
print("=" * 130)
print()
print("profit_per_payroll_euro = how much profit for each euro spent on staff")
print("  > 0.50 = exceptional (50 cents profit per euro of payroll)")
print("  > 0.30 = very good")
print("  > 0.15 = good")
print()

df = con.execute(query).df()
print(df.to_string())

# Now let's see which SECTORS have the best ratios
print("\n\n")
print("=" * 100)
print("BEST SECTORS BY PROFIT/PAYROLL RATIO")
print("=" * 100)

sector_query = """
WITH latest AS (
    SELECT siren, chiffre_affaires, charges_personnel, resultat_net,
           ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel > 0 AND resultat_net > 0 AND chiffre_affaires > 0
)
SELECT
    c.naf_code,
    COUNT(*) as n_companies,
    round(AVG(a.resultat_net / a.charges_personnel), 2) as avg_profit_per_payroll,
    round(AVG(100.0 * a.resultat_net / a.chiffre_affaires), 1) as avg_margin_pct,
    round(AVG(a.chiffre_affaires / a.charges_personnel), 1) as avg_rev_per_payroll
FROM latest a
JOIN (SELECT siren, activite_principale as naf_code
      FROM read_parquet('data/parquet/sirene_unites_legales.parquet')) c
    ON a.siren = c.siren
WHERE a.rn = 1
  AND a.resultat_net < a.chiffre_affaires
  AND c.naf_code NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z', '64.19Z')
  AND a.charges_personnel BETWEEN 500000 AND 15000000
  AND a.chiffre_affaires BETWEEN 1000000 AND 100000000
  AND (100.0 * a.resultat_net / a.chiffre_affaires) BETWEEN 5 AND 45
GROUP BY c.naf_code
HAVING COUNT(*) >= 5
ORDER BY avg_profit_per_payroll DESC
LIMIT 30
"""

df2 = con.execute(sector_query).df()
print(df2.to_string())
