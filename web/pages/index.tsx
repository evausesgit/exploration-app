import { useEffect, useState } from 'react'
import Head from 'next/head'

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
  }
  opportunities: Opportunity[]
}

export default function Home() {
  const [data, setData] = useState<ScanData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/data/automation_opportunities.json')
      .then(res => res.json())
      .then(data => {
        setData(data)
        setLoading(false)
      })
      .catch(err => {
        setError('Erreur lors du chargement des données')
        setLoading(false)
      })
  }, [])

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

  if (error || !data) {
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
              Dernière mise à jour : {formatDate(data.metadata.scan_date)}
            </div>
          </div>

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">Opportunités détectées</div>
              <div className="text-3xl font-bold text-indigo-600">{data.metadata.total_opportunities}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">Score moyen</div>
              <div className="text-3xl font-bold text-indigo-600">{data.metadata.statistics.avg_score.toFixed(1)}<span className="text-lg">/100</span></div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">CA/salarié moyen</div>
              <div className="text-3xl font-bold text-indigo-600">{formatCurrency(data.metadata.statistics.avg_ca_per_employee)}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-sm font-medium text-gray-500 mb-2">CA total cumulé</div>
              <div className="text-3xl font-bold text-indigo-600">{(data.metadata.statistics.total_ca / 1e6).toFixed(1)}M€</div>
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
                  {data.opportunities.map((opp) => (
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
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className={`h-2 rounded-full ${
                                opp.automation_score >= 80 ? 'bg-green-500' :
                                opp.automation_score >= 60 ? 'bg-yellow-500' : 'bg-orange-500'
                              }`}
                              style={{ width: `${opp.automation_score}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-semibold text-gray-900">{opp.automation_score}</span>
                        </div>
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
            <p>Critères de scan : CA min {formatCurrency(data.metadata.config.min_ca)}, Effectif max {data.metadata.config.max_effectif}, Score min {data.metadata.config.min_score}/100</p>
            <p className="mt-2">Secteurs ciblés : {data.metadata.config.secteurs.join(', ')}</p>
          </div>
        </div>
      </main>
    </>
  )
}
