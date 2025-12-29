import { useEffect, useState } from 'react'
import Head from 'next/head'
import ScoringConfig from '../components/ScoringConfig'
import ScoreBreakdownModal from '../components/ScoreBreakdownModal'
import {
  calculateScoreWithBreakdown,
  recalculateAllScores,
  ScoreBreakdown
} from '../utils/scoringEngine'

interface Opportunity {
  rank: number
  denomination: string
  siren: string
  automation_score: number
  ca: number
  effectif: number
  ca_per_employee: number
  resultat: number
  marge_pct: number
  secteur: string
  activite: string
  objet_social: string
  date_creation: string
  ville: string
  code_postal: string
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

interface ScanData {
  metadata: {
    scan_date: string
    total_opportunities: number
    config: {
      secteurs: string[]
      departements: string[] | null
      min_ca: number
      max_effectif: number
      min_ca_per_employee: number
      min_score: number
    }
    statistics: {
      avg_score: number
      avg_ca_per_employee: number
      total_ca: number
    }
    scoring_config: {
      criteria: ScoringCriteria
    }
  }
  opportunities: Opportunity[]
}

export default function Home() {
  const [originalData, setOriginalData] = useState<ScanData | null>(null)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentCriteria, setCurrentCriteria] = useState<ScoringCriteria | null>(null)
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null)
  const [showBreakdownModal, setShowBreakdownModal] = useState(false)

  useEffect(() => {
    fetch('/data/automation_opportunities.json')
      .then(res => res.json())
      .then(data => {
        setOriginalData(data)
        setOpportunities(data.opportunities)
        setCurrentCriteria(data.metadata.scoring_config.criteria)
        setLoading(false)
      })
      .catch(err => {
        setError('Erreur lors du chargement des données')
        setLoading(false)
      })
  }, [])

  const handleConfigChange = (newCriteria: ScoringCriteria) => {
    if (originalData) {
      const recalculated = recalculateAllScores(originalData.opportunities, newCriteria)
      setOpportunities(recalculated)
      setCurrentCriteria(newCriteria)
    }
  }

  const handleOpenBreakdown = (opp: Opportunity) => {
    setSelectedOpportunity(opp)
    setShowBreakdownModal(true)
  }

  const handleSaveBreakdown = (editedBreakdown: ScoreBreakdown) => {
    if (!selectedOpportunity) return

    // Update the opportunity with the new score
    const updatedOpportunities = opportunities.map(opp => {
      if (opp.siren === selectedOpportunity.siren) {
        return {
          ...opp,
          automation_score: editedBreakdown.total
        }
      }
      return opp
    })

    // Re-sort and re-rank based on new scores
    const sorted = updatedOpportunities
      .sort((a, b) => b.automation_score - a.automation_score)
      .map((opp, index) => ({
        ...opp,
        rank: index + 1
      }))

    setOpportunities(sorted)
    setShowBreakdownModal(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement des opportunités...</p>
        </div>
      </div>
    )
  }

  if (error || !originalData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <p className="text-red-600">{error || 'Données non disponibles'}</p>
        </div>
      </div>
    )
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const avgScore = opportunities.reduce((sum, opp) => sum + opp.automation_score, 0) / opportunities.length
  const avgCaPerEmployee = opportunities.reduce((sum, opp) => sum + opp.ca_per_employee, 0) / opportunities.length
  const totalCa = opportunities.reduce((sum, opp) => sum + opp.ca, 0)

  return (
    <>
      <Head>
        <title>Opportunités d'Automatisation IA - Exploration App</title>
        <meta name="description" content="Scanner d'opportunités d'automatisation IA pour entreprises françaises" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              🤖 Opportunités d'Automatisation IA
            </h1>
            <p className="text-lg text-gray-600">
              Entreprises françaises à fort potentiel d'automatisation
            </p>
            <div className="mt-4 text-sm text-gray-500">
              Dernière mise à jour : {formatDate(originalData.metadata.scan_date)}
            </div>
          </div>

          {/* Scoring Configuration */}
          <ScoringConfig
            defaultConfig={originalData.metadata.scoring_config}
            onConfigChange={handleConfigChange}
          />

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">Opportunités détectées</div>
              <div className="text-3xl font-bold text-indigo-600">{opportunities.length}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">Score moyen</div>
              <div className="text-3xl font-bold text-indigo-600">{avgScore.toFixed(1)}<span className="text-lg">/100</span></div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">CA/salarié moyen</div>
              <div className="text-3xl font-bold text-indigo-600">{formatCurrency(avgCaPerEmployee)}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">CA total cumulé</div>
              <div className="text-3xl font-bold text-indigo-600">{(totalCa / 1e6).toFixed(1)}M€</div>
            </div>
          </div>

          {/* Opportunities Table */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rang</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entreprise</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score IA</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CA</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Effectif</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CA/salarié</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Marge</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Localisation</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {opportunities.map((opp) => (
                    <tr key={opp.siren} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-indigo-100 text-indigo-800 font-semibold text-sm">
                            {opp.rank}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{opp.denomination}</div>
                        <div className="text-sm text-gray-500">{opp.activite}</div>
                        <div className="text-xs text-gray-400 mt-1">SIREN: {opp.siren}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleOpenBreakdown(opp)}
                          className="flex items-center hover:opacity-80 transition-opacity group"
                          title="Cliquez pour voir le détail du score"
                        >
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className={`h-2 rounded-full ${
                                opp.automation_score >= 80 ? 'bg-green-500' :
                                opp.automation_score >= 60 ? 'bg-yellow-500' : 'bg-orange-500'
                              }`}
                              style={{ width: `${opp.automation_score}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-semibold text-gray-900 group-hover:text-indigo-600">
                            {opp.automation_score}
                          </span>
                          <svg className="ml-1 w-4 h-4 text-gray-400 group-hover:text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(opp.ca)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {opp.effectif}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-indigo-600">
                          {formatCurrency(opp.ca_per_employee)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          opp.marge_pct >= 20 ? 'bg-green-100 text-green-800' :
                          opp.marge_pct >= 10 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {opp.marge_pct.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>{opp.ville}</div>
                        <div className="text-xs text-gray-500">{opp.code_postal}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>Critères de scan : CA min {formatCurrency(originalData.metadata.config.min_ca)}, Effectif max {originalData.metadata.config.max_effectif}, Score min {originalData.metadata.config.min_score}/100</p>
            <p className="mt-2">Secteurs ciblés : {originalData.metadata.config.secteurs.join(', ')}</p>
          </div>
        </div>

        {/* Score Breakdown Modal */}
        {selectedOpportunity && currentCriteria && (
          <ScoreBreakdownModal
            isOpen={showBreakdownModal}
            onClose={() => setShowBreakdownModal(false)}
            companyName={selectedOpportunity.denomination}
            initialBreakdown={calculateScoreWithBreakdown(selectedOpportunity, currentCriteria)}
            onSave={handleSaveBreakdown}
          />
        )}
      </main>
    </>
  )
}
