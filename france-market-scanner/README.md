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

## Data Dictionary

### SIRENE - Unités Légales (29M companies, 716MB)

Legal entities registered in France.

| Column | Type | Coverage | Description |
|--------|------|----------|-------------|
| `siren` | String | 100% | 9-digit company identifier |
| `statut_diffusion` | String | 100% | O=public, P=private |
| `date_creation` | Date | 100% | Company creation date |
| `sigle` | String | 5% | Company acronym |
| `denomination` | String | **53%** | Company name (47% are individuals) |
| `denomination_usuelle_1/2/3` | String | <1% | Alternative names |
| `prenom` | String | 47% | First name (for individuals) |
| `nom` | String | 47% | Last name (for individuals) |
| `categorie_juridique` | String | 100% | Legal form code (5710=SAS, 5499=SARL...) |
| `activite_principale` | String | **99.9%** | NAF code (industry classification) |
| `nomenclature_activite` | String | 100% | NAF version (NAFRev2) |
| `tranche_effectifs` | String | **6%** | Employee bracket - **UNRELIABLE** |
| `annee_effectifs` | Int | 6% | Year of employee declaration |
| `caractere_employeur` | String | 35% | O=employer, N=no employees |
| `categorie_entreprise` | String | **36%** | PME/ETI/GE classification |
| `annee_categorie_entreprise` | Int | 36% | Year of category |
| `economie_sociale_solidaire` | String | 3% | O/N - social economy |
| `societe_mission` | String | <1% | O/N - mission-driven company |
| `etat_administratif` | String | 100% | A=active (58%), C=closed |
| `date_cessation` | Date | 42% | Closure date |
| `date_derniere_mise_a_jour` | DateTime | 100% | Last update |
| `_loaded_at` | DateTime | 100% | ETL timestamp |
| `_source_file` | String | 100% | Source file name |

**Key limitations:**
- 94% have unknown employee count (`tranche_effectifs = 'NN'`)
- 47% are individuals (no company name, use `prenom`/`nom`)
- 42% are closed businesses

### SIRENE - Établissements (42M establishments, 1.9GB)

Physical locations/branches of companies.

| Column | Type | Coverage | Description |
|--------|------|----------|-------------|
| `siret` | String | 100% | 14-digit establishment ID (siren + nic) |
| `siren` | String | 100% | Parent company |
| `nic` | String | 100% | 5-digit establishment number |
| `statut_diffusion` | String | 100% | O=public, P=private |
| `date_creation` | Date | 100% | Establishment creation |
| `denomination_usuelle` | String | 3% | Trade name |
| `enseigne_1/2/3` | String | **19%** | Shop sign/brand |
| `activite_principale` | String | **99.9%** | NAF code |
| `nomenclature_activite` | String | 100% | NAF version |
| `activite_principale_registre_metiers` | String | 2% | Craft register code |
| `etablissement_siege` | Bool | 100% | true=headquarters |
| `tranche_effectifs` | String | **5.5%** | Employee bracket |
| `annee_effectifs` | Int | 5.5% | Year of employee data |
| `caractere_employeur` | String | 30% | O=employer |
| `complement_adresse` | String | 15% | Address complement |
| `numero_voie` | String | 70% | Street number |
| `indice_repetition` | String | 2% | B, TER, etc. |
| `type_voie` | String | 75% | RUE, AVENUE, etc. |
| `libelle_voie` | String | 80% | Street name |
| `code_postal` | String | **99.3%** | Postal code |
| `libelle_commune` | String | 99% | City name |
| `libelle_commune_etranger` | String | <1% | Foreign city |
| `code_commune` | String | 99% | INSEE commune code |
| `code_cedex` | String | 5% | CEDEX code |
| `libelle_cedex` | String | 5% | CEDEX label |
| `code_pays_etranger` | String | <1% | Foreign country code |
| `libelle_pays_etranger` | String | <1% | Foreign country name |
| `departement` | String | 99% | Department code |
| `region` | String | 99% | Region code |
| `etat_administratif` | String | 100% | A=active (40%), F=closed |
| `date_cessation` | Date | 60% | Closure date |
| `date_derniere_mise_a_jour` | DateTime | 100% | Last update |
| `_loaded_at` | DateTime | 100% | ETL timestamp |
| `_source_file` | String | 100% | Source file |

**Key limitations:**
- 60% are closed establishments
- Employee data even worse (5.5% known)
- Use for address/location data, not employee counts

### INPI - Comptes Annuels (6.6M accounts, 325MB)

Annual financial accounts filed with commercial courts.

| Column | Type | Coverage | Description |
|--------|------|----------|-------------|
| `siren` | String | 100% | Company identifier |
| `date_cloture` | String | 100% | Fiscal year end (YYYY-MM-DD) |
| `annee_cloture` | Int | 100% | Fiscal year |
| `duree_exercice` | Int | 95% | Period length in months |
| `type_comptes` | String | 100% | C=complet, S=simplifié, K=consolidé |
| `date_depot` | String | 100% | Filing date |
| `code_greffe` | String | 100% | Court code |
| `confidentialite` | String | 100% | 1=confidential (**55%**), 0=public |
| **Balance Sheet - Assets** |
| `immobilisations_incorporelles` | Float | 20% | Intangible assets |
| `immobilisations_corporelles` | Float | 20% | Tangible assets |
| `immobilisations_financieres` | Float | 20% | Financial assets |
| `actif_immobilise_net` | Float | 20% | Total fixed assets |
| `stocks` | Float | 15% | Inventory |
| `creances_clients` | Float | 20% | Accounts receivable |
| `disponibilites` | Float | 20% | Cash & equivalents |
| `actif_circulant` | Float | 20% | Current assets |
| `total_actif` | Float | 22% | Total assets |
| **Balance Sheet - Liabilities** |
| `capital_social` | Float | 25% | Share capital |
| `reserves` | Float | 20% | Retained earnings |
| `resultat_exercice` | Float | 25% | Net income (same as resultat_net) |
| `capitaux_propres` | Float | **44%** | Shareholders' equity |
| `dettes` | Float | 20% | Total debt |
| `total_passif` | Float | 22% | Total liabilities |
| **Income Statement** |
| `chiffre_affaires` | Float | **23%** | Revenue |
| `charges_personnel` | Float | **23%** | Payroll (salaries + social charges) |
| `resultat_exploitation` | Float | 20% | Operating income |
| `resultat_financier` | Float | 15% | Financial result |
| `resultat_exceptionnel` | Float | 10% | Exceptional items |
| `resultat_net` | Float | **29%** | Net profit/loss |

**Account types:**
| Code | Name | Count | Has Revenue |
|------|------|-------|-------------|
| C | Complet (full) | 1.5M | 25% |
| S | Simplifié (simplified) | 700K | 18% |
| K | Consolidé (consolidated) | 4K | **92%** |

**Key limitations:**
- **55% file confidential accounts** (no financials visible)
- Only 23% have visible revenue
- Small companies hide numbers; large companies are visible
- Best sector coverage: medical labs, software publishing

### BODACC - Annonces (50K announcements, 17MB)

Legal announcements (company events).

| Column | Type | Coverage | Description |
|--------|------|----------|-------------|
| `id` | String | 100% | Announcement ID |
| `siren` | String | **99.6%** | Company identifier |
| `numero_annonce` | String | 100% | Announcement number |
| `date_parution` | Date | 100% | Publication date |
| `numero_parution` | String | 100% | Publication number |
| `type_bulletin` | String | 100% | Bulletin type |
| `famille` | String | 100% | Event type (see below) |
| `nature` | String | 80% | Event nature |
| `denomination` | String | **0%** | Company name - **EMPTY** |
| `forme_juridique` | String | 50% | Legal form |
| `administration` | String | 30% | Management info |
| `adresse` | String | 70% | Address |
| `code_postal` | String | 70% | Postal code |
| `ville` | String | 70% | City |
| `activite` | String | 40% | Activity description |
| `details` | JSON | 80% | Structured details |
| `type_procedure` | String | 7% | Procedure type (bankruptcy) |
| `date_jugement` | Date | 7% | Judgment date |
| `tribunal` | String | 50% | Court name |
| `date_cloture_exercice` | Date | 40% | Fiscal year end |
| `type_depot` | String | 40% | Filing type |
| `contenu_annonce` | String | 80% | Full announcement text |
| `_loaded_at` | DateTime | 100% | ETL timestamp |
| `_source_file` | String | 100% | Source file |

**Event types (`famille`):**
| Type | Count | Description |
|------|-------|-------------|
| dpc | 19K | Dépôt des comptes (account filings) |
| modification | 9K | Company changes |
| creation | 9K | New companies |
| radiation | 7K | Company closures |
| collective | 3K | Bankruptcy proceedings |
| vente | 681 | Business sales |
| immatriculation | 714 | Registrations |

**Key limitations:**
- Only 50K records (small sample)
- `denomination` is empty - must join with SIRENE
- Limited to recent announcements

## Data Quality Summary

| Issue | Impact |
|-------|--------|
| **77% revenue hidden** | Most INPI filings are confidential |
| **94% employees unknown** | SIRENE `tranche_effectifs` useless |
| **55% INPI confidential** | Small companies hide numbers |
| **BODACC names empty** | Must join with SIRENE for company names |
| **60% establishments closed** | Filter by `etat_administratif = 'A'` |

## Tech Stack

- **chdb**: ClickHouse engine for instant SQL on Parquet
- **pandas/pyarrow**: DataFrame operations
- **uv**: Fast Python package manager
