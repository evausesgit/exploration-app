"""Find mid-sized hidden gems - high profit/employee, not household names.

Target: Companies with 10-200 employees, good margins, solid revenue.
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
        resultat_exploitation,
        ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel IS NOT NULL
      AND resultat_net IS NOT NULL
      AND chiffre_affaires IS NOT NULL
),
company_info AS (
    SELECT
        siren,
        denomination as nom,
        tranche_effectifs as sirene_effectif_code,
        activite_principale as naf_code
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
)
SELECT
    a.siren,
    c.nom,
    c.naf_code,
    a.date_cloture,

    -- Financials
    round(a.chiffre_affaires / 1e6, 2) as ca_millions,
    round(a.charges_personnel / 1e6, 2) as payroll_millions,
    round(a.resultat_net / 1e6, 2) as resultat_millions,

    -- Estimated employees (using 70K avg cost)
    round(a.charges_personnel / 70000, 0) as est_employees,

    -- Key ratios
    round(a.resultat_net / (a.charges_personnel / 70000), 0) as profit_per_emp,
    round(a.chiffre_affaires / (a.charges_personnel / 70000), 0) as rev_per_emp,
    round(100 * a.resultat_net / a.chiffre_affaires, 1) as margin_pct

FROM latest_accounts a
LEFT JOIN company_info c ON a.siren = c.siren
WHERE a.rn = 1
  -- PROFITABLE
  AND a.resultat_net > 0
  -- REAL OPERATING COMPANY (not holding)
  AND a.resultat_net < a.chiffre_affaires
  AND c.naf_code NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z', '64.19Z')
  -- MID-SIZED (10-200 employees based on payroll)
  AND a.charges_personnel BETWEEN 700000 AND 14000000  -- 10-200 employees @ 70K
  -- SOLID REVENUE (1M-100M - not tiny, not giant)
  AND a.chiffre_affaires BETWEEN 1000000 AND 100000000
  -- HEALTHY MARGIN (10%-40%)
  AND (100.0 * a.resultat_net / a.chiffre_affaires) BETWEEN 10 AND 40
  -- GOOD PROFIT/EMPLOYEE (at least 30K profit per employee)
  AND (a.resultat_net / (a.charges_personnel / 70000)) > 30000
ORDER BY profit_per_emp DESC
LIMIT 100
"""

print("=" * 130)
print("HIDDEN GEMS: Mid-sized companies with exceptional profit/employee")
print("Filters: 10-200 employees | 1M-100M revenue | 10-40% margin | >30K profit/emp")
print("=" * 130)
print()

df = con.execute(query).df()

# Group by sector
print(df.to_string(max_rows=100))

# Summary by NAF code
print("\n\nTOP SECTORS (by avg profit/employee):")
print("-" * 60)
sector_summary = """
SELECT
    c.naf_code,
    COUNT(*) as company_count,
    round(AVG(a.resultat_net / (a.charges_personnel / 70000)), 0) as avg_profit_per_emp,
    round(AVG(100.0 * a.resultat_net / a.chiffre_affaires), 1) as avg_margin
FROM (
    SELECT siren, date_cloture, chiffre_affaires, charges_personnel, resultat_net,
           ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel IS NOT NULL AND resultat_net IS NOT NULL AND chiffre_affaires IS NOT NULL
) a
LEFT JOIN (
    SELECT siren, activite_principale as naf_code
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
) c ON a.siren = c.siren
WHERE a.rn = 1
  AND a.resultat_net > 0
  AND a.resultat_net < a.chiffre_affaires
  AND c.naf_code NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z', '64.19Z')
  AND a.charges_personnel BETWEEN 700000 AND 14000000
  AND a.chiffre_affaires BETWEEN 1000000 AND 100000000
  AND (100.0 * a.resultat_net / a.chiffre_affaires) BETWEEN 10 AND 40
  AND (a.resultat_net / (a.charges_personnel / 70000)) > 30000
GROUP BY c.naf_code
HAVING COUNT(*) >= 3
ORDER BY avg_profit_per_emp DESC
LIMIT 20
"""
df2 = con.execute(sector_summary).df()
print(df2.to_string())
