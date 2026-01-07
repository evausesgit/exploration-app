# France Market Scanner

Identify French company "gems" - small teams with high revenue/profits, ideal for AI automation or acquisition.

## Data Available

| Source | File | Records | Size |
|--------|------|---------|------|
| **SIRENE** (companies) | `sirene_unites_legales.parquet` | 29M | 716MB |
| **SIRENE** (establishments) | `sirene_etablissements.parquet` | 42M | 1.9GB |
| **INPI** (annual accounts) | `inpi_comptes_*.parquet` | 6.6M | 325MB |
| **BODACC** (legal announcements) | `bodacc_annonces.parquet` | 50K | 17MB |
| **Total** | | | **2.9GB** |

## Quick Start

```bash
uv sync
```

### Query with chdb (ClickHouse SQL on Parquet)

```python
import chdb

# Simple query
chdb.query('''
    SELECT siren, chiffre_affaires, resultat_net
    FROM file("data/parquet/inpi_comptes_2022.parquet")
    WHERE chiffre_affaires > 1000000
    LIMIT 10
''', 'PrettyCompact')
```

## Joining Data

Join INPI financials with SIRENE company info:

```python
import chdb

result = chdb.query('''
    SELECT
        i.siren,
        s.denomination,
        s.tranche_effectifs as employees,
        s.activite_principale as naf_code,
        i.chiffre_affaires as revenue,
        i.resultat_net as profit
    FROM file("data/parquet/inpi_comptes_2022.parquet") i
    JOIN file("data/parquet/sirene_unites_legales.parquet") s
        ON i.siren = s.siren
    WHERE i.chiffre_affaires > 1000000
    ORDER BY i.chiffre_affaires DESC
    LIMIT 20
''', 'DataFrame')  # returns pandas DataFrame
```

### Employee brackets (`tranche_effectifs`)

| Code | Employees |
|------|-----------|
| 00 | 0 |
| 01 | 1-2 |
| 02 | 3-5 |
| 03 | 6-9 |
| 11 | 10-19 |
| 12 | 20-49 |
| 21 | 50-99 |
| NN | Unknown (~90%) |

### Find small teams with high revenue

```python
import chdb

# Companies with <10 employees but >1M revenue
result = chdb.query('''
    SELECT
        i.siren,
        s.denomination,
        s.tranche_effectifs,
        s.activite_principale,
        i.chiffre_affaires,
        i.resultat_net,
        round(i.resultat_net / i.chiffre_affaires * 100, 1) as margin_pct
    FROM file("data/parquet/inpi_comptes_2022.parquet") i
    JOIN file("data/parquet/sirene_unites_legales.parquet") s
        ON i.siren = s.siren
    WHERE i.chiffre_affaires > 1000000
      AND i.resultat_net > 0
      AND s.tranche_effectifs IN ('01', '02', '03')
    ORDER BY margin_pct DESC
    LIMIT 50
''', 'DataFrame')
```

## Finding Gems

Query to find small teams with high revenue per employee:

```python
import chdb

result = chdb.query("""
    SELECT
        i.siren,
        s.denomination,
        s.tranche_effectifs as emp,
        s.activite_principale as naf,
        round(i.chiffre_affaires, 0) as revenue,
        round(i.resultat_net, 0) as profit,
        round(i.chiffre_affaires /
            multiIf(s.tranche_effectifs = '01', 1.5,
                    s.tranche_effectifs = '02', 4,
                    s.tranche_effectifs = '03', 7.5, 1), 0) as rev_per_emp,
        round(i.resultat_net / i.chiffre_affaires * 100, 1) as margin
    FROM file('data/parquet/inpi_comptes_2022.parquet') i
    JOIN file('data/parquet/sirene_unites_legales.parquet') s
        ON i.siren = s.siren
    WHERE i.chiffre_affaires > 500000
      AND i.resultat_net > 0
      AND s.tranche_effectifs IN ('01', '02', '03')  -- <10 employees
    ORDER BY rev_per_emp DESC
    LIMIT 30
""", 'DataFrame')
```

### Caveats

Many "gems" are actually:
- **Holding companies** (NAF 64.xx, 70.10Z) - no real employees, just financial flows
- **Subsidiaries** - employees counted in parent company
- **Trading companies** - high revenue, low margin commodity trading

Filter them out:
```sql
WHERE s.activite_principale NOT LIKE '64%'  -- exclude holdings
  AND s.activite_principale NOT LIKE '70.10%'
  AND i.resultat_net / i.chiffre_affaires > 0.05  -- >5% margin
```

## Data Reliability

### The SIRENE Employee Problem

The `tranche_effectifs` field from SIRENE is **unreliable**:

| Issue | Reality |
|-------|---------|
| 90% are "NN" (unknown) | Most companies never declare |
| Self-declared | No verification, rarely updated |
| Brackets are stale | Company grows from 5 to 300, still shows "02" |

**Example**: CONGO MARITIME shows `tranche_effectifs = "02"` (3-5 employees) but actually has ~300 employees based on payroll.

### The Solution: Use Payroll Data

INPI provides `charges_personnel` (total staff costs) from **audited annual accounts**. This is much more reliable:

| Source | Field | Reliability | Why |
|--------|-------|-------------|-----|
| **INPI** | `charges_personnel` | **HIGH** | Audited income statement, legal requirement |
| **INPI** | `resultat_net` | **HIGH** | Official annual accounts filed with Greffe |
| **SIRENE** | `tranche_effectifs` | **LOW** | Self-declared, rarely updated |

### What is `charges_personnel`?

Total employer cost for all employees, including:
- Gross salaries
- Social charges (~45% of gross in France)
- Benefits and bonuses

**Average cost per employee in France: ~70,000€/year**

```
charges_personnel = 2,100,000€
estimated_employees = 2,100,000 / 70,000 = 30 employees
```

### Better Query: Payroll-Based Employee Estimates

```python
import chdb

result = chdb.query("""
    SELECT
        i.siren,
        s.denomination,
        s.activite_principale as naf,
        round(i.chiffre_affaires / 1e6, 2) as revenue_millions,
        round(i.charges_personnel / 1e6, 2) as payroll_millions,
        round(i.resultat_net / 1e6, 2) as profit_millions,

        -- Payroll-based employee estimate (70K avg cost in France)
        round(i.charges_personnel / 70000, 0) as estimated_employees,

        -- Key ratios
        round(i.resultat_net / (i.charges_personnel / 70000), 0) as profit_per_employee,
        round(i.chiffre_affaires / (i.charges_personnel / 70000), 0) as revenue_per_employee,
        round(i.resultat_net / i.chiffre_affaires * 100, 1) as margin_pct

    FROM file('data/parquet/inpi_comptes_2022.parquet') i
    JOIN file('data/parquet/sirene_unites_legales.parquet') s
        ON i.siren = s.siren
    WHERE i.charges_personnel > 700000           -- At least ~10 employees
      AND i.resultat_net > 0                     -- Profitable
      AND i.resultat_net < i.chiffre_affaires   -- Exclude holding companies (dividend income)
      AND s.activite_principale NOT IN ('70.10Z', '64.20Z', '64.30Z')  -- Exclude holdings
      AND i.resultat_net / i.chiffre_affaires BETWEEN 0.05 AND 0.50   -- Realistic margins
    ORDER BY profit_per_employee DESC
    LIMIT 50
""", 'DataFrame')
```

### Why Filter `resultat_net < chiffre_affaires`?

Holding companies receive **dividends from subsidiaries** which appear in `resultat_net` but not in `chiffre_affaires`:

| Company | Revenue | Profit | What's happening |
|---------|---------|--------|------------------|
| BOLLORE SE | 1.7M€ | 43M€ | Dividends from subsidiaries |
| VINCI (holding) | 0.2M€ | 29M€ | Same - not operating profit |

These aren't real "gems" - they're financial structures with a few HQ staff.

## Limitations of Payroll-Based Estimates

### The 70K€ Average Varies by Sector

| Sector | Real cost/employee | Our 70K estimate | Effect on ratio |
|--------|-------------------|------------------|-----------------|
| Tech/Finance/Pharma | 100-120K€ | 70K€ | **Overcounts** employees → ratio looks worse |
| Retail/Agriculture | 45-55K€ | 70K€ | **Undercounts** employees → ratio looks better |

**Implication:**
- High-wage sectors: We might MISS real gems (false negatives)
- Low-wage sectors: We might see FAKE gems (false positives)

### Group vs Entity: Why SIRENE and Payroll Don't Match

SIRENE `tranche_effectifs` often counts **all employees in the corporate group**, while INPI `charges_personnel` is only for **that specific legal entity**.

Example from our data:
```
SANOFI group structure:
├── SANOFI SA (parent)         → SIRENE: "11" (10000+ group employees)
│                              → INPI payroll: 14M€ (~200 HQ staff)
├── SANOFI CHIMIE (subsidiary) → SIRENE: "21" (part of group count)
│                              → INPI payroll: 2.8M€ (~40 employees)
└── SANOFI PASTEUR EUROPE      → SIRENE: "02" (???)
                               → INPI payroll: 7.3M€ (~104 employees)
```

**This isn't stale data - it's different accounting scopes.**

### Recommended Strategy

Use **both** data sources depending on context:

```python
# Strategy: Trust SIRENE when available and plausible, else use payroll

CASE
    -- If SIRENE is known AND payroll roughly matches bracket, use SIRENE
    WHEN tranche_effectifs NOT IN ('NN', '')
     AND charges_personnel / 70000 BETWEEN bracket_min * 0.3 AND bracket_max * 3
    THEN sirene_midpoint

    -- Otherwise fall back to payroll estimate
    ELSE charges_personnel / 70000
END as estimated_employees
```

For **standalone companies** (not part of a group), SIRENE is often accurate when declared.
For **group structures**, payroll-based estimates are more reliable for the specific entity.

### Better Metric: Profit Per Payroll Euro (No Assumptions)

The "profit per employee" metric requires assuming a cost per employee (70K? 100K?). This introduces circular logic - changing the assumption changes the absolute numbers but not the ranking.

**Better approach**: Use `profit / payroll` directly:

```python
profit_per_payroll_euro = resultat_net / charges_personnel
```

This is pure data, no assumptions:
- **> 0.50** = exceptional (50 cents profit per euro of payroll)
- **> 0.30** = very good
- **> 0.15** = good

```python
import chdb

result = chdb.query("""
    SELECT
        i.siren,
        s.denomination,
        s.activite_principale as naf,
        round(i.chiffre_affaires / 1e6, 2) as revenue_M,
        round(i.charges_personnel / 1e6, 2) as payroll_M,
        round(i.resultat_net / 1e6, 2) as profit_M,

        -- ACTUAL RATIO - no assumptions
        round(i.resultat_net / i.charges_personnel, 2) as profit_per_payroll_euro,
        round(100 * i.resultat_net / i.chiffre_affaires, 1) as margin_pct

    FROM file('data/parquet/inpi_comptes_2022.parquet') i
    JOIN file('data/parquet/sirene_unites_legales.parquet') s
        ON i.siren = s.siren
    WHERE i.charges_personnel > 500000           -- Some scale
      AND i.resultat_net > 0                     -- Profitable
      AND i.resultat_net < i.chiffre_affaires   -- Not a holding
      AND s.activite_principale NOT IN ('70.10Z', '64.20Z', '64.30Z')
    ORDER BY profit_per_payroll_euro DESC
    LIMIT 50
""", 'DataFrame')
```

If you still want "profit per employee" for intuition, you can convert:
```
profit_per_employee = profit_per_payroll_euro × assumed_cost_per_employee
                    = 0.50 × 70,000 = 35,000€/employee
```

## Limitations

| Issue | Impact |
|-------|--------|
| **75% missing revenue** | Most small companies use confidential filings |
| **90% unknown employees** | `tranche_effectifs = 'NN'` for most companies |
| **Payroll varies by sector** | 50K-100K per employee depending on wages |
| **Group vs entity mismatch** | SIRENE counts group, INPI is entity-level |
| **2023 incomplete** | Only 1.2M records vs 2.2M in 2022 |

## How Data Was Produced

| Source | Method |
|--------|--------|
| **SIRENE** | Downloaded from data.gouv.fr (Parquet), exported |
| **INPI** | Downloaded 1,297 7z archives from data.cquest.org mirror, extracted XML with 12 workers |
| **BODACC** | API calls to OpenDataSoft |

```bash
# Regenerate INPI (takes ~1 hour)
uv run python extract_inpi.py
```

## File Structure

```
data/parquet/
├── sirene_unites_legales.parquet   (716MB, 29M companies)
├── sirene_etablissements.parquet   (1.9GB, 42M establishments)
├── inpi_comptes_2020.parquet       (72MB, 1.4M accounts)
├── inpi_comptes_2021.parquet       (93MB, 1.9M accounts)
├── inpi_comptes_2022.parquet       (106MB, 2.2M accounts)
├── inpi_comptes_2023.parquet       (55MB, 1.2M accounts)
└── bodacc_annonces.parquet         (17MB, 50K announcements)
```

## Tech Stack

- **chdb**: ClickHouse engine for instant SQL on Parquet
- **pandas/pyarrow**: DataFrame operations
- **uv**: Fast Python package manager
