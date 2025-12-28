import { useState, useMemo } from 'react'
import type { IRouteFeature } from '../../types/IRoute'
import { useRouteStore } from '../../stores/routeStore'

interface IRouteListProps {
  routes: IRouteFeature[]
}

export const RouteList = ({ routes }: IRouteListProps) => {
  const {
    selectedRouteIds,
    toggleRouteSelection,
    selectAllRoutes,
    clearSelection,
    setAnimatingRoute,
  } = useRouteStore()

  const [searchTerm, setSearchTerm] = useState('')
  const [filterVehicle, setFilterVehicle] = useState<string>('all')

  const vehicles = useMemo(() => {
    const uniqueVehicles = new Set(routes.map((r) => r.properties.vehicle_name))
    return Array.from(uniqueVehicles).sort()
  }, [routes])

  const filteredRoutes = useMemo(() => {
    return routes.filter((route) => {
      const matchesSearch =
        route.properties.vehicle_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        route.properties.route_date.includes(searchTerm)

      const matchesVehicle =
        filterVehicle === 'all' || route.properties.vehicle_name === filterVehicle

      return matchesSearch && matchesVehicle
    })
  }, [routes, searchTerm, filterVehicle])

  const handleSelectAll = () => {
    if (selectedRouteIds.length === filteredRoutes.length) {
      clearSelection()
    } else {
      selectAllRoutes(filteredRoutes.map((r) => r.properties.route_id))
    }
  }

  const handleRouteClick = (routeId: number) => {
    toggleRouteSelection(routeId)
  }

  const handleAnimateRoute = (routeId: number, event: React.MouseEvent) => {
    event.stopPropagation()
    setAnimatingRoute(routeId)
  }

  const isSelected = (routeId: number) => selectedRouteIds.includes(routeId)

  return (
    <div className="absolute left-4 top-4 bottom-4 w-80 bg-white rounded-lg shadow-lg z-[1000] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-3">Routes</h2>

        {/* Search */}
        <input
          type="text"
          placeholder="Search routes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
        />

        {/* Vehicle Filter */}
        <select
          value={filterVehicle}
          onChange={(e) => setFilterVehicle(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Vehicles</option>
          {vehicles.map((vehicle) => (
            <option key={vehicle} value={vehicle}>
              {vehicle}
            </option>
          ))}
        </select>

        {/* Select All */}
        <div className="mt-3 flex items-center justify-between">
          <button
            onClick={handleSelectAll}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {selectedRouteIds.length === filteredRoutes.length
              ? 'Deselect All'
              : 'Select All'}
          </button>
          <span className="text-sm text-gray-500">
            {selectedRouteIds.length} selected
          </span>
        </div>
      </div>

      {/* Route List */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredRoutes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No routes found
          </div>
        ) : (
          <div className="space-y-2">
            {filteredRoutes.map((route) => {
              const props = route.properties
              const selected = isSelected(props.route_id)

              return (
                <div
                  key={props.route_id}
                  onClick={() => handleRouteClick(props.route_id)}
                  className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    selected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                  role="button"
                  tabIndex={0}
                  aria-label={`Route for ${props.vehicle_name}`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleRouteClick(props.route_id)
                    }
                  }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-800">
                        {props.vehicle_name}
                      </h3>
                      <p className="text-xs text-gray-500">{props.vehicle_type}</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => {}}
                      className="mt-1 w-4 h-4 text-blue-600"
                      aria-label="Select route"
                    />
                  </div>

                  <div className="text-sm text-gray-600 space-y-1">
                    <div className="flex justify-between">
                      <span>Date:</span>
                      <span className="font-medium">{props.route_date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Duration:</span>
                      <span className="font-medium">{props.duration_minutes} min</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Distance:</span>
                      <span className="font-medium">
                        {props.total_distance_km.toFixed(1)} km
                      </span>
                    </div>
                  </div>

                  {selected && (
                    <button
                      onClick={(e) => handleAnimateRoute(props.route_id, e)}
                      className="mt-2 w-full px-3 py-1.5 bg-blue-500 text-white text-sm rounded-md hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
                      aria-label="Animate route"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      Animate Route
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 text-xs text-gray-500 text-center">
        Showing {filteredRoutes.length} of {routes.length} routes
      </div>
    </div>
  )
}
