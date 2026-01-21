"""Find gems in HIGH-WAGE sectors (tech, finance, pharma, consulting).

In these sectors, real cost/employee is 90-120K€, not 70K€.
So our 70K estimate OVERCOUNTS employees, making ratios look WORSE than reality.
If they still look good at 70K estimate, they're probably REALLY good.
"""
import duckdb

con = duckdb.connect()

# High-wage NAF codes (90-120K€ per employee typically)
HIGH_WAGE_NAF = """
    '62.01Z',  -- Programming
    '62.02A',  -- IT consulting
    '62.02B',  -- IT facilities management
    '62.03Z',  -- Computer facilities management
    '62.09Z',  -- Other IT services
    '63.11Z',  -- Data processing/hosting
    '63.12Z',  -- Web portals
    '58.29A',  -- Software publishing (games)
    '58.29B',  -- Software publishing (other)
    '58.29C',  -- Software publishing
    '64.11Z',  -- Central banking
    '64.19Z',  -- Other monetary intermediation
    '64.91Z',  -- Financial leasing
    '64.92Z',  -- Other credit granting
    '64.99Z',  -- Other financial services
    '66.11Z',  -- Financial market admin
    '66.12Z',  -- Securities brokerage
    '66.19A',  -- Financial asset management
    '66.19B',  -- Other financial support
    '66.21Z',  -- Risk evaluation
    '66.22Z',  -- Insurance agents
    '66.29Z',  -- Other insurance support
    '70.21Z',  -- PR and communications
    '70.22Z',  -- Business consulting
    '71.11Z',  -- Architecture
    '71.12A',  -- Engineering consulting
    '71.12B',  -- Technical studies
    '71.20A',  -- Testing laboratories
    '71.20B',  -- Technical analysis
    '72.11Z',  -- Biotech R&D
    '72.19Z',  -- Other R&D natural sciences
    '72.20Z',  -- R&D social sciences
    '73.11Z',  -- Advertising agencies
    '73.12Z',  -- Media buying
    '21.10Z',  -- Pharma manufacturing
    '21.20Z',  -- Pharma preparations
    '26.11Z',  -- Electronic components
    '26.20Z',  -- Computers
    '26.30Z',  -- Communications equipment
    '26.51A',  -- Instruments manufacturing
    '26.51B',  -- Instruments manufacturing
    '26.60Z',  -- Medical devices
    '30.30Z'   -- Aerospace
"""

query = f"""
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
    WHERE charges_personnel > 0
      AND resultat_net IS NOT NULL
      AND chiffre_affaires > 0
),
company_info AS (
    SELECT
        siren,
        denomination as nom,
        tranche_effectifs as sirene_code,
        activite_principale as naf_code
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
)
SELECT
    a.siren,
    c.nom,
    c.naf_code,
    a.date_cloture,

    -- Financials
    round(a.chiffre_affaires / 1e6, 2) as ca_M,
    round(a.charges_personnel / 1e6, 2) as payroll_M,
    round(a.resultat_net / 1e6, 2) as profit_M,

    -- Conservative estimate (70K) - OVERCOUNTS for high-wage
    round(a.charges_personnel / 70000, 0) as est_emp_70k,

    -- Realistic estimate for high-wage (100K)
    round(a.charges_personnel / 100000, 0) as est_emp_100k,

    -- Ratios using CONSERVATIVE 70K (if good here, definitely good in reality)
    round(a.resultat_net / (a.charges_personnel / 70000), 0) as profit_per_emp_70k,

    -- Ratios using REALISTIC 100K (closer to reality for these sectors)
    round(a.resultat_net / (a.charges_personnel / 100000), 0) as profit_per_emp_100k,

    round(100 * a.resultat_net / a.chiffre_affaires, 1) as margin_pct,
    c.sirene_code

FROM latest_accounts a
LEFT JOIN company_info c ON a.siren = c.siren
WHERE a.rn = 1
  AND a.resultat_net > 0
  AND a.resultat_net < a.chiffre_affaires  -- Not a holding
  AND c.naf_code IN ({HIGH_WAGE_NAF})
  -- Mid-sized: 5-100 employees (at 100K estimate)
  AND a.charges_personnel BETWEEN 500000 AND 10000000
  -- Decent revenue
  AND a.chiffre_affaires BETWEEN 1000000 AND 50000000
  -- Good margin
  AND (100.0 * a.resultat_net / a.chiffre_affaires) BETWEEN 10 AND 45
ORDER BY profit_per_emp_100k DESC
LIMIT 100
"""

print("=" * 140)
print("HIGH-WAGE SECTOR GEMS (Tech, Finance, Pharma, Consulting)")
print("These use 100K€/employee estimate - more accurate for these sectors")
print("=" * 140)
print()

df = con.execute(query).df()
print(df.to_string(max_rows=100))

print("\n")
print("NOTE: profit_per_emp_100k is the realistic figure for these high-wage sectors")
print("      profit_per_emp_70k is CONSERVATIVE (actual performance is even better)")

# Summary by NAF
print("\n\nBY SECTOR:")
print("-" * 80)
summary = f"""
SELECT
    c.naf_code,
    COUNT(*) as n,
    round(AVG(a.resultat_net / (a.charges_personnel / 100000)), 0) as avg_profit_per_emp,
    round(AVG(100.0 * a.resultat_net / a.chiffre_affaires), 1) as avg_margin
FROM (
    SELECT siren, chiffre_affaires, charges_personnel, resultat_net,
           ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel > 0 AND resultat_net > 0 AND chiffre_affaires > 0
) a
JOIN (
    SELECT siren, activite_principale as naf_code
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
) c ON a.siren = c.siren
WHERE a.rn = 1
  AND a.resultat_net < a.chiffre_affaires
  AND c.naf_code IN ({HIGH_WAGE_NAF})
  AND a.charges_personnel BETWEEN 500000 AND 10000000
  AND a.chiffre_affaires BETWEEN 1000000 AND 50000000
  AND (100.0 * a.resultat_net / a.chiffre_affaires) BETWEEN 10 AND 45
GROUP BY c.naf_code
HAVING COUNT(*) >= 3
ORDER BY avg_profit_per_emp DESC
"""
df2 = con.execute(summary).df()
print(df2.to_string())
