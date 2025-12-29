import { useState, useEffect } from 'react'

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

interface ScoringConfigProps {
  defaultConfig: { criteria: ScoringCriteria }
  onConfigChange: (config: ScoringCriteria) => void
}

export default function ScoringConfig({ defaultConfig, onConfigChange }: ScoringConfigProps) {
  const [config, setConfig] = useState<ScoringCriteria>(defaultConfig.criteria)
  const [showConfig, setShowConfig] = useState(false)

  useEffect(() => {
    setConfig(defaultConfig.criteria)
  }, [defaultConfig])

  const handleToggleCriteria = (criteria: keyof ScoringCriteria) => {
    const newConfig = {
      ...config,
      [criteria]: {
        ...config[criteria],
        enabled: !config[criteria].enabled
      }
    }
    setConfig(newConfig)
  }

  const handleWeightChange = (criteria: keyof ScoringCriteria, weight: number) => {
    const newConfig = {
      ...config,
      [criteria]: {
        ...config[criteria],
        weight: weight
      }
    }
    setConfig(newConfig)
  }

  const handleApply = () => {
    onConfigChange(config)
  }

  const handleReset = () => {
    setConfig(defaultConfig.criteria)
    onConfigChange(defaultConfig.criteria)
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          ⚙️ Configuration du Scoring
        </h2>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
        >
          {showConfig ? 'Masquer' : 'Afficher'}
        </button>
      </div>

      {showConfig && (
        <div className="space-y-6">
          {/* CA par employé */}
          <div className="border-b pb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.ca_per_employee.enabled}
                  onChange={() => handleToggleCriteria('ca_per_employee')}
                  className="h-5 w-5 text-indigo-600 rounded"
                />
                <label className="text-lg font-semibold text-gray-900">
                  1️⃣ Ratio CA/Effectif
                </label>
              </div>
              <span className="text-sm text-gray-500">
                Poids max: {config.ca_per_employee.weight} points
              </span>
            </div>

            {config.ca_per_employee.enabled && (
              <div className="ml-8 space-y-3">
                <div>
                  <label className="block text-sm text-gray-700 mb-2">
                    Poids du critère: {config.ca_per_employee.weight} points
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={config.ca_per_employee.weight}
                    onChange={(e) => handleWeightChange('ca_per_employee', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-2">Paliers (valeurs en €) :</p>
                  <div className="grid grid-cols-2 gap-2">
                    {config.ca_per_employee.thresholds.map((t, idx) => (
                      <div key={idx} className="flex items-center space-x-2">
                        <span>≥ {(t.value / 1000).toFixed(0)}k€</span>
                        <span className="text-indigo-600 font-medium">→ {t.points}pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Secteur */}
          <div className="border-b pb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.sector.enabled}
                  onChange={() => handleToggleCriteria('sector')}
                  className="h-5 w-5 text-indigo-600 rounded"
                />
                <label className="text-lg font-semibold text-gray-900">
                  2️⃣ Secteur d'Activité
                </label>
              </div>
              <span className="text-sm text-gray-500">
                Poids max: {config.sector.weight} points
              </span>
            </div>

            {config.sector.enabled && (
              <div className="ml-8 space-y-3">
                <div>
                  <label className="block text-sm text-gray-700 mb-2">
                    Poids du critère: {config.sector.weight} points
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={config.sector.weight}
                    onChange={(e) => handleWeightChange('sector', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
                <div className="text-sm text-gray-600">
                  <p>Bonus si correspondance avec secteurs prioritaires (conseil, marketing, SaaS, etc.)</p>
                </div>
              </div>
            )}
          </div>

          {/* Rentabilité */}
          <div className="border-b pb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.profitability.enabled}
                  onChange={() => handleToggleCriteria('profitability')}
                  className="h-5 w-5 text-indigo-600 rounded"
                />
                <label className="text-lg font-semibold text-gray-900">
                  3️⃣ Rentabilité (Marge)
                </label>
              </div>
              <span className="text-sm text-gray-500">
                Poids max: {config.profitability.weight} points
              </span>
            </div>

            {config.profitability.enabled && (
              <div className="ml-8 space-y-3">
                <div>
                  <label className="block text-sm text-gray-700 mb-2">
                    Poids du critère: {config.profitability.weight} points
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="30"
                    value={config.profitability.weight}
                    onChange={(e) => handleWeightChange('profitability', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-2">Paliers (marge en %) :</p>
                  <div className="grid grid-cols-2 gap-2">
                    {config.profitability.thresholds.map((t, idx) => (
                      <div key={idx} className="flex items-center space-x-2">
                        <span>≥ {t.value}%</span>
                        <span className="text-indigo-600 font-medium">→ {t.points}pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Actifs physiques */}
          <div className="pb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={config.low_assets.enabled}
                  onChange={() => handleToggleCriteria('low_assets')}
                  className="h-5 w-5 text-indigo-600 rounded"
                />
                <label className="text-lg font-semibold text-gray-900">
                  4️⃣ Faibles Actifs Physiques
                </label>
              </div>
              <span className="text-sm text-gray-500">
                Poids max: {config.low_assets.weight} points
              </span>
            </div>

            {config.low_assets.enabled && (
              <div className="ml-8 space-y-3">
                <div>
                  <label className="block text-sm text-gray-700 mb-2">
                    Poids du critère: {config.low_assets.weight} points
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="30"
                    value={config.low_assets.weight}
                    onChange={(e) => handleWeightChange('low_assets', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-2">Paliers (ratio immobilisations/CA) :</p>
                  <div className="grid grid-cols-2 gap-2">
                    {config.low_assets.thresholds.map((t, idx) => (
                      <div key={idx} className="flex items-center space-x-2">
                        <span>{'< '}{(t.ratio * 100).toFixed(0)}% du CA</span>
                        <span className="text-indigo-600 font-medium">→ {t.points}pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-4 pt-4 border-t">
            <button
              onClick={handleReset}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
            >
              Réinitialiser
            </button>
            <button
              onClick={handleApply}
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors font-medium"
            >
              Appliquer et Recalculer
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
