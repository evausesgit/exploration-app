"""Find small companies that extract profits as dividends.

Logic:
- High profits over multiple years
- But equity (capitaux_propres) doesn't grow proportionally
- = money is being paid out as dividends

Also look for:
- Small payroll (few employees)
- High revenue AND/OR high profit
- High cash on hand (disponibilites)
"""
import duckdb

con = duckdb.connect()

# First: Find companies with multiple years of data to track equity changes
query = """
WITH yearly_data AS (
    SELECT
        siren,
        annee_cloture as year,
        chiffre_affaires as revenue,
        resultat_net as profit,
        capitaux_propres as equity,
        charges_personnel as payroll,
        disponibilites as cash,
        reserves
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE resultat_net IS NOT NULL
      AND capitaux_propres IS NOT NULL
),
multi_year AS (
    SELECT
        siren,
        COUNT(DISTINCT year) as years_of_data,
        SUM(profit) as total_profit,
        MAX(equity) - MIN(equity) as equity_change,
        AVG(revenue) as avg_revenue,
        AVG(profit) as avg_profit,
        AVG(payroll) as avg_payroll,
        MAX(cash) as latest_cash,
        MAX(year) as latest_year
    FROM yearly_data
    WHERE year >= 2019
    GROUP BY siren
    HAVING COUNT(DISTINCT year) >= 3  -- At least 3 years of data
),
company_info AS (
    SELECT siren, denomination, activite_principale as naf
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
)
SELECT
    m.siren,
    c.denomination,
    c.naf,
    m.years_of_data,
    m.latest_year,

    -- Financials (average per year)
    round(m.avg_revenue / 1e6, 2) as avg_revenue_M,
    round(m.avg_profit / 1e6, 2) as avg_profit_M,
    round(m.avg_payroll / 1e6, 2) as avg_payroll_M,

    -- Total profit over the period
    round(m.total_profit / 1e6, 2) as total_profit_M,

    -- Equity change over the period
    round(m.equity_change / 1e6, 2) as equity_change_M,

    -- INFERRED DIVIDENDS = profit that didn't stay in the company
    round((m.total_profit - m.equity_change) / 1e6, 2) as inferred_dividends_M,

    -- Dividend payout ratio (what % of profits were extracted)
    CASE WHEN m.total_profit > 0
         THEN round(100 * (m.total_profit - m.equity_change) / m.total_profit, 0)
         ELSE 0
    END as payout_ratio_pct,

    -- Cash on hand
    round(m.latest_cash / 1e6, 2) as cash_M

FROM multi_year m
LEFT JOIN company_info c ON m.siren = c.siren
WHERE m.total_profit > 500000  -- At least 500K total profit over period
  AND m.avg_payroll BETWEEN 100000 AND 5000000  -- Small company (roughly 1-70 employees)
  AND m.total_profit > m.equity_change  -- More profit than equity growth = dividends
  AND c.naf NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z')  -- Not holdings
ORDER BY inferred_dividends_M DESC
LIMIT 100
"""

print("=" * 140)
print("DIVIDEND MACHINES: Small companies extracting profits")
print("=" * 140)
print()
print("inferred_dividends = total_profit - equity_change")
print("payout_ratio = % of profits extracted (not retained)")
print()

df = con.execute(query).df()
print(df.to_string(max_rows=100))

# Now find the REAL small gems: high revenue OR high profit with tiny payroll
print("\n\n")
print("=" * 140)
print("CASH COWS: Small teams (< 1M payroll) with big numbers")
print("=" * 140)

gems_query = """
WITH latest AS (
    SELECT
        siren,
        chiffre_affaires as revenue,
        resultat_net as profit,
        charges_personnel as payroll,
        disponibilites as cash,
        ROW_NUMBER() OVER (PARTITION BY siren ORDER BY date_cloture DESC) as rn
    FROM read_parquet('data/parquet/inpi_comptes_*.parquet')
    WHERE charges_personnel > 0
),
company_info AS (
    SELECT siren, denomination, activite_principale as naf
    FROM read_parquet('data/parquet/sirene_unites_legales.parquet')
)
SELECT
    l.siren,
    c.denomination,
    c.naf,
    round(l.revenue / 1e6, 2) as revenue_M,
    round(l.profit / 1e6, 2) as profit_M,
    round(l.payroll / 1e6, 2) as payroll_M,
    round(l.cash / 1e6, 2) as cash_M,
    round(l.profit / l.payroll, 2) as profit_per_payroll

FROM latest l
LEFT JOIN company_info c ON l.siren = c.siren
WHERE l.rn = 1
  AND l.payroll BETWEEN 70000 AND 1000000  -- 1-14 employees roughly
  AND (l.revenue > 5000000 OR l.profit > 500000)  -- High revenue OR high profit
  AND l.profit > 0
  AND l.profit < l.revenue  -- Not a holding
  AND c.naf NOT IN ('70.10Z', '64.20Z', '64.30Z', '66.30Z', '64.19Z')
ORDER BY profit_M DESC
LIMIT 50
"""

df2 = con.execute(gems_query).df()
print(df2.to_string())
