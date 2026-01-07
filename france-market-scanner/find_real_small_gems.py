"""Find ACTUALLY small independent companies - not subsidiaries of giants.

Filters:
- Revenue between 1M and 20M (too small for CAC40 subsidiary)
- Payroll between 200K and 2M (3-30 employees roughly)
- Not obviously a subsidiary name (no "FRANCE", "EUROPE", "SAS" of known giants)
- Has actual business activity (not holding NAF codes)
"""
import chdb

query = """
WITH latest AS (
    SELECT
        siren,
        date_cloture,
        chiffre_affaires as revenue,
        resultat_net as profit,
        charges_personnel as payroll,
        disponibilites as cash,
        capital_social,
        ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM file('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel > 0
      AND resultat_net IS NOT NULL
      AND chiffre_affaires > 0
),
company_info AS (
    SELECT
        siren,
        denomination,
        activite_principale as naf,
        categorie_entreprise,  -- PME, ETI, GE
        date_creation
    FROM file('data/parquet/sirene_unites_legales.parquet')
)
SELECT
    l.siren,
    c.denomination,
    c.naf,
    c.categorie_entreprise as cat,
    l.date_cloture,

    round(l.revenue / 1e6, 2) as revenue_M,
    round(l.profit / 1e6, 2) as profit_M,
    round(l.payroll / 1e6, 2) as payroll_M,
    round(l.cash / 1e6, 2) as cash_M,
    round(l.capital_social / 1e3, 0) as capital_K,

    round(l.profit / l.payroll, 2) as profit_per_payroll,
    round(100 * l.profit / l.revenue, 1) as margin_pct

FROM latest l
LEFT JOIN company_info c ON l.siren = c.siren
WHERE l.rn = 1
  -- SIZE FILTERS: Actually small
  AND l.revenue BETWEEN 1000000 AND 20000000  -- 1M-20M revenue
  AND l.payroll BETWEEN 200000 AND 2000000     -- 3-30 employees roughly
  AND l.profit > 100000                         -- At least 100K profit

  -- NOT A HOLDING
  AND l.profit < l.revenue
  AND c.naf NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z', '64.19Z', '64.99Z')

  -- CATEGORY FILTER: PME only (excludes ETI and GE = big groups)
  AND (c.categorie_entreprise = 'PME' OR c.categorie_entreprise IS NULL)

  -- Exclude obvious subsidiary names
  AND c.denomination NOT LIKE '%FRANCE%'
  AND c.denomination NOT LIKE '%EUROPE%'
  AND c.denomination NOT LIKE '%INTERNATIONAL%'
  AND c.denomination NOT LIKE '%HOLDING%'
  AND c.denomination NOT LIKE '%GROUP%'

  -- Good margin (real operating business)
  AND (100.0 * l.profit / l.revenue) BETWEEN 5 AND 40

ORDER BY profit_per_payroll DESC
LIMIT 100
"""

print("=" * 130)
print("REAL SMALL GEMS: Independent PMEs with high profit/payroll")
print("Filters: 1-20M revenue | 200K-2M payroll | PME category | No giant subsidiaries")
print("=" * 130)
print()

result = chdb.query(query, 'DataFrame')
print(result.to_string(max_rows=100))

# Show by sector
print("\n\n")
print("BY SECTOR:")
print("-" * 80)
sector_query = """
WITH latest AS (
    SELECT siren, chiffre_affaires as revenue, resultat_net as profit, charges_personnel as payroll,
           ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM file('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel > 0 AND resultat_net > 0 AND chiffre_affaires > 0
)
SELECT
    c.naf,
    COUNT(*) as n,
    round(AVG(l.profit / l.payroll), 2) as avg_profit_per_payroll,
    round(AVG(100.0 * l.profit / l.revenue), 1) as avg_margin,
    round(AVG(l.revenue) / 1e6, 2) as avg_revenue_M
FROM latest l
JOIN (SELECT siren, activite_principale as naf, categorie_entreprise, denomination
      FROM file('data/parquet/sirene_unites_legales.parquet')) c ON l.siren = c.siren
WHERE l.rn = 1
  AND l.revenue BETWEEN 1000000 AND 20000000
  AND l.payroll BETWEEN 200000 AND 2000000
  AND l.profit > 100000
  AND l.profit < l.revenue
  AND c.naf NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z', '64.19Z', '64.99Z')
  AND (c.categorie_entreprise = 'PME' OR c.categorie_entreprise IS NULL)
  AND c.denomination NOT LIKE '%FRANCE%'
  AND c.denomination NOT LIKE '%EUROPE%'
  AND c.denomination NOT LIKE '%INTERNATIONAL%'
  AND c.denomination NOT LIKE '%HOLDING%'
  AND c.denomination NOT LIKE '%GROUP%'
  AND (100.0 * l.profit / l.revenue) BETWEEN 5 AND 40
GROUP BY c.naf
HAVING COUNT(*) >= 5
ORDER BY avg_profit_per_payroll DESC
LIMIT 20
"""
result2 = chdb.query(sector_query, 'DataFrame')
print(result2.to_string())
