"""Find REAL operating companies with best profit/employee ratios.

Filters out:
- Holding companies (revenue << profit = dividend income)
- Implausible SIRENE brackets
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
    WHERE charges_personnel > 500000  -- At least 500K payroll (~7 employees)
      AND resultat_net IS NOT NULL
      AND resultat_net > 0
      AND chiffre_affaires > 1000000  -- At least 1M revenue
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

    -- Raw financials
    round(a.chiffre_affaires / 1e6, 2) as ca_millions,
    round(a.charges_personnel / 1e6, 2) as payroll_millions,
    round(a.resultat_net / 1e6, 2) as resultat_millions,
    round(a.resultat_exploitation / 1e6, 2) as rex_millions,

    -- Estimated employees
    round(a.charges_personnel / 70000, 0) as estimated_employees,

    -- Key ratios
    round(a.resultat_net / (a.charges_personnel / 70000), 0) as profit_per_employee,
    round(a.chiffre_affaires / (a.charges_personnel / 70000), 0) as revenue_per_employee,
    round(100 * a.resultat_net / a.chiffre_affaires, 1) as margin_pct,

    -- SIRENE bracket
    c.sirene_effectif_code

FROM latest_accounts a
LEFT JOIN company_info c ON a.siren = c.siren
WHERE a.rn = 1
  -- FILTER OUT HOLDING COMPANIES: profit should be < revenue for operating business
  AND a.resultat_net < a.chiffre_affaires
  -- Filter out obvious holding company NAF codes
  AND c.naf_code NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z')
  -- At least 10 employees estimated
  AND (a.charges_personnel / 70000) >= 10
  -- Profit margin between 5% and 50% (realistic for operating company)
  AND (100.0 * a.resultat_net / a.chiffre_affaires) BETWEEN 5 AND 50
ORDER BY profit_per_employee DESC
LIMIT 50
"""

print("Top 50 OPERATING companies by profit per employee")
print("(Excluding holding companies and unrealistic margins)")
print("=" * 120)
print()

df = con.execute(query).df()
print(df.to_string())

print("\n")
print("Filters applied:")
print("  - Revenue > 1M€")
print("  - Payroll > 500K€ (min ~7 employees)")
print("  - Profit < Revenue (excludes holding companies living on dividends)")
print("  - NAF code not in holding/investment codes (70.10Z, 64.20Z, 64.30Z)")
print("  - Profit margin 5%-50% (realistic operating range)")
print("  - At least 10 estimated employees")
