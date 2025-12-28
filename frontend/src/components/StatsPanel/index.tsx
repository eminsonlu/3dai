import type { IRouteStats } from '../../types/IRoute'

interface IStatsPanelProps {
  stats: IRouteStats | null
  loading: boolean
}

export const StatsPanel = ({ stats, loading }: IStatsPanelProps) => {
  if (loading) {
    return (
      <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg z-[1000]">
        <p className="text-gray-500">Loading stats...</p>
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg z-[1000] min-w-[250px]">
      <h3 className="text-lg font-bold mb-3 text-gray-800">Route Statistics</h3>

      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-600">Total Routes:</span>
          <span className="font-semibold text-gray-800">{stats.total_routes}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Vehicles:</span>
          <span className="font-semibold text-gray-800">{stats.total_vehicles}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Days:</span>
          <span className="font-semibold text-gray-800">{stats.total_days}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Total Distance:</span>
          <span className="font-semibold text-gray-800">
            {stats.total_distance_km.toFixed(1)} km
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Avg Duration:</span>
          <span className="font-semibold text-gray-800">
            {stats.avg_duration_minutes} min
          </span>
        </div>
      </div>
    </div>
  )
}
