import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import { useRoutes } from '../../hooks/useRoutes'
import { StatsPanel } from '../../components/StatsPanel'
import { RouteList } from '../../components/RouteList'
import { AnimatedRoute } from '../../components/AnimatedRoute'
import { useRouteStore } from '../../stores/routeStore'
import type { IRouteFeature } from '../../types/IRoute'
import 'leaflet/dist/leaflet.css'

const BURSA_CENTER: [number, number] = [40.1917, 29.0611]

export const RouteMapContainer = () => {
  const { routes, stats, loading, error } = useRoutes()
  const { selectedRouteIds, animatingRouteId, setAnimatingRoute } = useRouteStore()

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-bold text-lg mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    )
  }

  const handleFeatureClick = (feature: IRouteFeature) => {
    const props = feature.properties
    const div = document.createElement('div')
    div.className = 'p-2'
    div.innerHTML = `
      <h3 class="font-bold text-gray-800 mb-2">${props.vehicle_name}</h3>
      <div class="text-sm space-y-1">
        <p><span class="font-semibold">Type:</span> ${props.vehicle_type}</p>
        <p><span class="font-semibold">Date:</span> ${props.route_date}</p>
        <p><span class="font-semibold">Duration:</span> ${props.duration_minutes} min</p>
        <p><span class="font-semibold">Distance:</span> ${props.total_distance_km.toFixed(1)} km</p>
      </div>
    `
    return div
  }

  // Filter routes based on selection
  const visibleRoutes = routes?.features.filter((route) =>
    selectedRouteIds.length === 0
      ? true
      : selectedRouteIds.includes(route.properties.route_id)
  )

  const animatingRoute = routes?.features.find(
    (route) => route.properties.route_id === animatingRouteId
  )

  const handleAnimationComplete = () => {
    setAnimatingRoute(null)
  }

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={BURSA_CENTER}
        zoom={12}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {animatingRoute && (
          <AnimatedRoute
            route={animatingRoute}
            onComplete={handleAnimationComplete}
          />
        )}

        {!animatingRoute && visibleRoutes && visibleRoutes.length > 0 && (
          <GeoJSON
            key={selectedRouteIds.join(',')}
            data={{ type: 'FeatureCollection', features: visibleRoutes } as any}
            style={(feature) => {
              const colors = [
                '#ef4444',
                '#3b82f6',
                '#10b981',
                '#f59e0b',
                '#8b5cf6',
                '#ec4899',
              ]
              const colorIndex =
                (feature?.properties?.vehicle_id || 0) % colors.length
              return {
                color: colors[colorIndex],
                weight: 3,
                opacity: 0.7,
              }
            }}
            onEachFeature={(feature, layer) => {
              layer.bindPopup(handleFeatureClick(feature as IRouteFeature))
            }}
          />
        )}
      </MapContainer>

      {/* Route List Sidebar */}
      {routes && <RouteList routes={routes.features} />}

      <StatsPanel stats={stats} loading={loading} />

      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-[2000]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600 font-medium">Loading routes...</p>
          </div>
        </div>
      )}
    </div>
  )
}
