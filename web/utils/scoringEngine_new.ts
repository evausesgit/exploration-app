interface Opportunity {
  ca: number
  effectif: number
  ca_per_employee: number
  marge_pct: number
  activite: string
  objet_social: string
  immobilisations: number
}

export interface ScoreBreakdown {
  ca_per_employee: {
    points: number
    max: number
    detail: string
  }
  sector: {
    points: number
    max: number
    detail: string
    matches: number
  }
  profitability: {
    points: number
    max: number
    detail: string
  }
  low_assets: {
    points: number
    max: number
    detail: string
  }
  bonus: {
    points: number
    detail: string
  }
  total: number
}

interface ScoringCriteria {
  ca_per_employee: {
    enabled: boolean
    weight: number
    thresholds: Array<{value: number, points: number}>
  }
  sector: {
    enabled: boolean
    weight: number
    points_per_match: number
    bonus_threshold: number
  }
  profitability: {
    enabled: boolean
    weight: number
    thresholds: Array<{value: number, points: number}>
  }
  low_assets: {
    enabled: boolean
    weight: number
    thresholds: Array<{ratio: number, points: number}>
  }
}

// Secteurs prioritaires (même liste que Python)
const SECTEURS_PRIORITAIRES: Record<string, string[]> = {
  'conseil': ['conseil', 'consulting', 'audit', 'accompagnement', 'stratégie', 'transformation digitale', 'organisation'],
  'marketing_digital': ['marketing', 'publicité', 'communication', 'seo', 'sem', 'social media', 'content', 'influence', 'ads', 'media'],
  'saas_tech': ['saas', 'software', 'logiciel', 'plateforme', 'application', 'cloud', 'api', 'développement'],
  'formation': ['formation', 'training', 'coaching', 'enseignement', 'e-learning', 'éducation', 'pédagogie'],
  'courtage_intermediation': ['courtage', 'courtier', 'intermédiaire', 'intermédiation', 'plateforme', 'marketplace', 'broker'],
  'services_rh': ['recrutement', 'rh', 'ressources humaines', 'talent', 'headhunting', 'staffing', 'interim'],
  'services_financiers': ['comptabilité', 'expertise comptable', 'finance', 'gestion', 'compliance', 'contrôle de gestion', 'audit financier'],
  'services_juridiques': ['juridique', 'legal', 'droit', 'avocat', 'notaire', 'propriété intellectuelle', 'compliance']
}

export function calculateScoreWithBreakdown(
  opportunity: Opportunity,
  criteria: ScoringCriteria
): ScoreBreakdown {
  const breakdown: ScoreBreakdown = {
    ca_per_employee: { points: 0, max: criteria.ca_per_employee.weight, detail: '' },
    sector: { points: 0, max: criteria.sector.weight, detail: '', matches: 0 },
    profitability: { points: 0, max: criteria.profitability.weight, detail: '' },
    low_assets: { points: 0, max: criteria.low_assets.weight, detail: '' },
    bonus: { points: 0, detail: '' },
    total: 0
  }

  // 1. Ratio CA/effectif
  if (criteria.ca_per_employee.enabled) {
    const caPerEmployee = opportunity.ca_per_employee
    const sortedThresholds = [...criteria.ca_per_employee.thresholds].sort((a, b) => b.value - a.value)

    for (const threshold of sortedThresholds) {
      if (caPerEmployee >= threshold.value) {
        breakdown.ca_per_employee.points = threshold.points
        breakdown.ca_per_employee.detail = `${(caPerEmployee / 1000).toFixed(0)}k€/sal ≥ ${(threshold.value / 1000).toFixed(0)}k€`
        break
      }
    }
  } else {
    breakdown.ca_per_employee.detail = 'Critère désactivé'
  }

  // 2. Secteur d'activité
  if (criteria.sector.enabled) {
    const texteComplet = `${opportunity.activite} ${opportunity.objet_social}`.toLowerCase()
    let secteurMatches = 0
    const matchedSectors: string[] = []

    for (const [secteurName, keywords] of Object.entries(SECTEURS_PRIORITAIRES)) {
      for (const keyword of keywords) {
        if (texteComplet.includes(keyword.toLowerCase())) {
          secteurMatches++
          matchedSectors.push(secteurName)
          break
        }
      }
    }

    breakdown.sector.matches = secteurMatches

    // Attribution des points selon le nombre de matches
    if (secteurMatches >= criteria.sector.bonus_threshold) {
      breakdown.sector.points = criteria.sector.weight
      breakdown.sector.detail = `${secteurMatches} secteurs (≥${criteria.sector.bonus_threshold}) : ${matchedSectors.join(', ')}`
    } else if (secteurMatches >= 2) {
      breakdown.sector.points = Math.round(criteria.sector.weight * 0.83)
      breakdown.sector.detail = `${secteurMatches} secteurs : ${matchedSectors.join(', ')}`
    } else if (secteurMatches >= 1) {
      breakdown.sector.points = Math.round(criteria.sector.weight * 0.67)
      breakdown.sector.detail = `${secteurMatches} secteur : ${matchedSectors.join(', ')}`
    } else {
      breakdown.sector.points = Math.round(criteria.sector.weight * 0.33)
      breakdown.sector.detail = 'Aucun secteur prioritaire détecté'
    }
  } else {
    breakdown.sector.detail = 'Critère désactivé'
  }

  // 3. Rentabilité (marge)
  if (criteria.profitability.enabled) {
    const marge = opportunity.marge_pct
    const sortedThresholds = [...criteria.profitability.thresholds].sort((a, b) => b.value - a.value)

    for (const threshold of sortedThresholds) {
      if (marge >= threshold.value) {
        breakdown.profitability.points = threshold.points
        breakdown.profitability.detail = `Marge ${marge.toFixed(1)}% ≥ ${threshold.value}%`
        break
      }
    }
  } else {
    breakdown.profitability.detail = 'Critère désactivé'
  }

  // 4. Faibles actifs physiques (immobilisations)
  if (criteria.low_assets.enabled) {
    const immobilisations = opportunity.immobilisations || 0
    const ca = opportunity.ca
    const ratio = ca > 0 ? immobilisations / ca : 1
    const sortedThresholds = [...criteria.low_assets.thresholds].sort((a, b) => a.ratio - b.ratio)

    for (const threshold of sortedThresholds) {
      if (ratio <= threshold.ratio) {
        breakdown.low_assets.points = threshold.points
        if (immobilisations === 0) {
          breakdown.low_assets.detail = 'Aucune immobilisation'
        } else {
          breakdown.low_assets.detail = `Immo ${(ratio * 100).toFixed(1)}% du CA ≤ ${(threshold.ratio * 100).toFixed(0)}%`
        }
        break
      }
    }
  } else {
    breakdown.low_assets.detail = 'Critère désactivé'
  }

  // Bonus si mots-clés de services immatériels
  const texteComplet = `${opportunity.activite} ${opportunity.objet_social}`.toLowerCase()
  const serviceKeywords = ['conseil', 'formation', 'digital', 'logiciel', 'plateforme', 'saas']
  for (const keyword of serviceKeywords) {
    if (texteComplet.includes(keyword)) {
      breakdown.bonus.points = 2
      breakdown.bonus.detail = `Mot-clé service : "${keyword}"`
      break
    }
  }

  // Calculer le total
  breakdown.total = Math.min(100, Math.round(
    breakdown.ca_per_employee.points +
    breakdown.sector.points +
    breakdown.profitability.points +
    breakdown.low_assets.points +
    breakdown.bonus.points
  ))

  return breakdown
}

export function calculateAutomationScore(
  opportunity: Opportunity,
  criteria: ScoringCriteria
): number {
  return calculateScoreWithBreakdown(opportunity, criteria).total
}

export function recalculateAllScores(
  opportunities: any[],
  criteria: ScoringCriteria
): any[] {
  return opportunities.map(opp => ({
    ...opp,
    automation_score: calculateAutomationScore(opp, criteria)
  })).sort((a, b) => b.automation_score - a.automation_score)
  .map((opp, index) => ({
    ...opp,
    rank: index + 1
  }))
}
