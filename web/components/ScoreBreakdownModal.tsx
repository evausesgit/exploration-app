import { useState, useEffect } from 'react'
import { ScoreBreakdown } from '../utils/scoringEngine'

interface ScoreBreakdownModalProps {
  isOpen: boolean
  onClose: () => void
  companyName: string
  initialBreakdown: ScoreBreakdown
  onSave?: (editedBreakdown: ScoreBreakdown) => void
}

export default function ScoreBreakdownModal({
  isOpen,
  onClose,
  companyName,
  initialBreakdown,
  onSave
}: ScoreBreakdownModalProps) {
  const [breakdown, setBreakdown] = useState<ScoreBreakdown>(initialBreakdown)
  const [isEditing, setIsEditing] = useState(false)

  useEffect(() => {
    setBreakdown(initialBreakdown)
  }, [initialBreakdown])

  const handlePointsChange = (criterion: keyof Omit<ScoreBreakdown, 'total'>, newPoints: number) => {
    const criterionData = breakdown[criterion]
    const max = 'max' in criterionData ? criterionData.max : 100
    const clampedPoints = Math.max(0, Math.min(max, newPoints))

    const newBreakdown = {
      ...breakdown,
      [criterion]: {
        ...breakdown[criterion],
        points: clampedPoints
      }
    }

    // Recalculer le total
    newBreakdown.total = Math.min(100, Math.round(
      newBreakdown.ca_per_employee.points +
      newBreakdown.sector.points +
      newBreakdown.profitability.points +
      newBreakdown.low_assets.points +
      newBreakdown.bonus.points
    ))

    setBreakdown(newBreakdown)
  }

  const handleSave = () => {
    if (onSave) {
      onSave(breakdown)
    }
    setIsEditing(false)
  }

  const handleReset = () => {
    setBreakdown(initialBreakdown)
    setIsEditing(false)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{companyName}</h2>
            <p className="text-sm text-gray-500 mt-1">Détail du scoring</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
          >
            ×
          </button>
        </div>

        {/* Score Total */}
        <div className="p-6 bg-gradient-to-r from-indigo-50 to-purple-50">
          <div className="text-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Score Total</div>
            <div className="text-5xl font-bold text-indigo-600">{breakdown.total}</div>
            <div className="text-sm text-gray-500 mt-1">/ 100 points</div>
          </div>
        </div>

        {/* Critères */}
        <div className="p-6 space-y-4">
          {/* CA per Employee */}
          <CriterionCard
            title="💰 Ratio CA/Effectif"
            points={breakdown.ca_per_employee.points}
            max={breakdown.ca_per_employee.max}
            detail={breakdown.ca_per_employee.detail}
            isEditing={isEditing}
            onPointsChange={(val) => handlePointsChange('ca_per_employee', val)}
          />

          {/* Sector */}
          <CriterionCard
            title="🎯 Secteur d'Activité"
            points={breakdown.sector.points}
            max={breakdown.sector.max}
            detail={breakdown.sector.detail}
            isEditing={isEditing}
            onPointsChange={(val) => handlePointsChange('sector', val)}
            badge={breakdown.sector.matches > 0 ? `${breakdown.sector.matches} match${breakdown.sector.matches > 1 ? 'es' : ''}` : undefined}
          />

          {/* Profitability */}
          <CriterionCard
            title="📈 Rentabilité"
            points={breakdown.profitability.points}
            max={breakdown.profitability.max}
            detail={breakdown.profitability.detail}
            isEditing={isEditing}
            onPointsChange={(val) => handlePointsChange('profitability', val)}
          />

          {/* Low Assets */}
          <CriterionCard
            title="🪶 Faibles Actifs"
            points={breakdown.low_assets.points}
            max={breakdown.low_assets.max}
            detail={breakdown.low_assets.detail}
            isEditing={isEditing}
            onPointsChange={(val) => handlePointsChange('low_assets', val)}
          />

          {/* Bonus */}
          {breakdown.bonus.points > 0 && (
            <CriterionCard
              title="⭐ Bonus"
              points={breakdown.bonus.points}
              max={undefined}
              detail={breakdown.bonus.detail}
              isEditing={isEditing}
              onPointsChange={(val) => handlePointsChange('bonus', val)}
            />
          )}
        </div>

        {/* Actions */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-6 flex justify-between items-center">
          {!isEditing ? (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
              >
                Fermer
              </button>
              <button
                onClick={() => setIsEditing(true)}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
              >
                Éditer les points
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleReset}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
              >
                Réinitialiser
              </button>
              <div className="flex gap-3">
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
                >
                  Annuler
                </button>
                <button
                  onClick={handleSave}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                >
                  Enregistrer
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

interface CriterionCardProps {
  title: string
  points: number
  max?: number
  detail: string
  isEditing: boolean
  onPointsChange: (points: number) => void
  badge?: string
}

function CriterionCard({ title, points, max, detail, isEditing, onPointsChange, badge }: CriterionCardProps) {
  const percentage = max ? (points / max) * 100 : 0
  const getColorClass = (pct: number) => {
    if (pct >= 80) return 'bg-green-500'
    if (pct >= 60) return 'bg-blue-500'
    if (pct >= 40) return 'bg-yellow-500'
    return 'bg-gray-400'
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          {badge && (
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full font-medium">
              {badge}
            </span>
          )}
        </div>
        <div className="flex items-baseline gap-1">
          {isEditing ? (
            <input
              type="number"
              value={points}
              onChange={(e) => onPointsChange(parseInt(e.target.value) || 0)}
              min="0"
              max={max}
              className="w-16 px-2 py-1 border border-indigo-300 rounded text-right font-bold text-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          ) : (
            <span className="text-2xl font-bold text-indigo-600">{points}</span>
          )}
          {max && <span className="text-sm text-gray-500">/ {max}</span>}
        </div>
      </div>

      {max && (
        <div className="mb-3">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${getColorClass(percentage)} transition-all duration-300`}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      )}

      <p className="text-sm text-gray-600 italic">{detail}</p>
    </div>
  )
}
