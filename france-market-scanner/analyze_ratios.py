"""Find companies with best profit/employee ratios using payroll-based estimates."""
import duckdb

# Connect to parquet files
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
    WHERE charges_personnel > 100000  -- At least 100K payroll (filter tiny companies)
      AND resultat_net IS NOT NULL
      AND chiffre_affaires > 0
),
company_info AS (
    SELECT
        siren,
        denomination as nom,
        tranche_effectifs as sirene_effectif_code
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
)
SELECT
    a.siren,
    c.nom,
    a.date_cloture,

    -- Raw financials
    round(a.chiffre_affaires / 1e6, 2) as ca_millions,
    round(a.charges_personnel / 1e6, 2) as payroll_millions,
    round(a.resultat_net / 1e6, 2) as resultat_millions,

    -- Estimated employees from payroll (avg 70K€ total cost per person in France)
    round(a.charges_personnel / 70000, 0) as estimated_employees,

    -- SIRENE bracket for comparison
    c.sirene_effectif_code,

    -- Key ratios
    round(a.resultat_net / (a.charges_personnel / 70000), 0) as profit_per_employee,
    round(a.chiffre_affaires / (a.charges_personnel / 70000), 0) as revenue_per_employee,

    -- Profit margin
    round(100 * a.resultat_net / a.chiffre_affaires, 1) as margin_pct

FROM latest_accounts a
LEFT JOIN company_info c ON a.siren = c.siren
WHERE a.rn = 1
  AND a.resultat_net > 0  -- Profitable only
  AND (a.charges_personnel / 70000) >= 5  -- At least ~5 employees
ORDER BY profit_per_employee DESC
LIMIT 50
"""

print("Top 50 companies by profit per employee (using payroll-based estimates)")
print("=" * 100)
print()

df = con.execute(query).df()
print(df.to_string())

print("\n\n")
print("Legend:")
print("  - estimated_employees = charges_personnel / 70,000€ (avg French employer cost)")
print("  - profit_per_employee = resultat_net / estimated_employees")
print("  - SIRENE codes: 00=0, 01=1-2, 02=3-5, 03=6-9, 11=10-19, 12=20-49, etc.")
