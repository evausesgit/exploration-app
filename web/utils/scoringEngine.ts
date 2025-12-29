interface Opportunity {
  ca: number
  effectif: number
  ca_per_employee: number
  marge_pct: number
  activite: string
  objet_social: string
  immobilisations: number
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

export function calculateAutomationScore(
  opportunity: Opportunity,
  criteria: ScoringCriteria
): number {
  let score = 0

  // 1. Ratio CA/effectif
  if (criteria.ca_per_employee.enabled) {
    const caPerEmployee = opportunity.ca_per_employee

    // Trouver le palier correspondant (du plus élevé au plus bas)
    const sortedThresholds = [...criteria.ca_per_employee.thresholds].sort((a, b) => b.value - a.value)
    for (const threshold of sortedThresholds) {
      if (caPerEmployee >= threshold.value) {
        score += threshold.points
        break
      }
    }
  }

  // 2. Secteur d'activité
  if (criteria.sector.enabled) {
    const texteComplet = `${opportunity.activite} ${opportunity.objet_social}`.toLowerCase()

    let secteurMatches = 0
    for (const keywords of Object.values(SECTEURS_PRIORITAIRES)) {
      for (const keyword of keywords) {
        if (texteComplet.includes(keyword.toLowerCase())) {
          secteurMatches++
          break // Un seul match par secteur
        }
      }
    }

    // Attribution des points selon le nombre de matches
    if (secteurMatches >= criteria.sector.bonus_threshold) {
      score += criteria.sector.weight
    } else if (secteurMatches >= 2) {
      score += criteria.sector.weight * 0.83 // 25/30
    } else if (secteurMatches >= 1) {
      score += criteria.sector.weight * 0.67 // 20/30
    } else {
      score += criteria.sector.weight * 0.33 // 10/30
    }
  }

  // 3. Rentabilité (marge)
  if (criteria.profitability.enabled) {
    const marge = opportunity.marge_pct

    // Trouver le palier correspondant
    const sortedThresholds = [...criteria.profitability.thresholds].sort((a, b) => b.value - a.value)
    for (const threshold of sortedThresholds) {
      if (marge >= threshold.value) {
        score += threshold.points
        break
      }
    }
  }

  // 4. Faibles actifs physiques (immobilisations)
  if (criteria.low_assets.enabled) {
    const immobilisations = opportunity.immobilisations || 0
    const ca = opportunity.ca
    const ratio = ca > 0 ? immobilisations / ca : 1

    // Trouver le palier correspondant (du plus bas au plus élevé pour les ratios)
    const sortedThresholds = [...criteria.low_assets.thresholds].sort((a, b) => a.ratio - b.ratio)
    for (const threshold of sortedThresholds) {
      if (ratio <= threshold.ratio) {
        score += threshold.points
        break
      }
    }
  }

  // Bonus si mots-clés de services immatériels
  const texteComplet = `${opportunity.activite} ${opportunity.objet_social}`.toLowerCase()
  const serviceKeywords = ['conseil', 'formation', 'digital', 'logiciel', 'plateforme', 'saas']
  for (const keyword of serviceKeywords) {
    if (texteComplet.includes(keyword)) {
      score += 2
      break
    }
  }

  return Math.min(100, Math.round(score))
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
