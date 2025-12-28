import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import type { LatLngExpression } from 'leaflet'
import * as L from 'leaflet'
import {
  getNeighborhoods,
  optimizeRoute
} from '../../services/routeService'
import type {
  IRouteRequest,
  IOptimizedRouteResponse
} from '../../types/IRoute'

// Fix for default marker icons in Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const RouteCreator = () => {
  const [neighborhoods, setNeighborhoods] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [selectedNeighborhood, setSelectedNeighborhood] = useState('')
  const [weekStartDate, setWeekStartDate] = useState('')
  const [quickMode, setQuickMode] = useState(true)

  const [routeResult, setRouteResult] = useState<IOptimizedRouteResponse | null>(null)

  const center: LatLngExpression = [40.1885, 28.8846]

  useEffect(() => {
    loadInitialData()
    setDefaultWeekStart()
  }, [])

  const loadInitialData = async () => {
    try {
      const neighborhoodsData = await getNeighborhoods()

      setNeighborhoods(neighborhoodsData.neighborhoods)

      if (neighborhoodsData.neighborhoods.length > 0) {
        setSelectedNeighborhood(neighborhoodsData.neighborhoods[0])
      }
    } catch (err) {
      console.error('Failed to load initial data:', err)
      setError('Failed to load neighborhoods')
    }
  }

  const setDefaultWeekStart = () => {
    const today = new Date()
    const nextMonday = new Date(today)
    const dayOfWeek = today.getDay()
    const daysUntilMonday = dayOfWeek === 0 ? 1 : 8 - dayOfWeek
    nextMonday.setDate(today.getDate() + daysUntilMonday)
    setWeekStartDate(nextMonday.toISOString().split('T')[0])
  }

  const handleGenerateRoute = async () => {
    if (!selectedNeighborhood || !weekStartDate) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError(null)
    setRouteResult(null)

    try {
      const request: IRouteRequest = {
        neighborhood: selectedNeighborhood,
        week_start_date: weekStartDate,
        quick_mode: quickMode
      }

      const response = await optimizeRoute(request)
      setRouteResult(response)
    } catch (err: any) {
      console.error('Route optimization failed:', err)
      setError(err.response?.data?.detail || 'Route optimization failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadGeoJSON = () => {
    if (!routeResult) return

    const dataStr = JSON.stringify(routeResult.geojson, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `route_${selectedNeighborhood}_${weekStartDate}.geojson`
    link.click()
    URL.revokeObjectURL(url)
  }

  const pointToLayer = (feature: any, latlng: any) => {
    const props = feature.properties

    if (props.type === 'depot') {
      // Depot marker
      const depotIcon = L.divIcon({
        className: 'custom-depot-marker',
        html: '<div style="background-color: #3b82f6; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">D</div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      })
      return L.marker(latlng, { icon: depotIcon })
    }

    if (props.type === 'container') {
      // Container marker
      const color = '#10b981' // Green for containers
      const containerIcon = L.divIcon({
        className: 'custom-container-marker',
        html: `<div style="background-color: ${color}; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">${props.order}</div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      })
      return L.marker(latlng, { icon: containerIcon })
    }

    return L.marker(latlng)
  }

  const onEachFeature = (feature: any, layer: any) => {
    const props = feature.properties

    if (props.type === 'depot') {
      layer.bindPopup(`
        <div class="p-2">
          <h3 class="font-bold text-sm mb-1">Depot</h3>
          <p class="text-xs">Starting location for collection routes</p>
        </div>
      `)
    }

    if (props.type === 'container') {
      layer.bindPopup(`
        <div class="p-2">
          <h3 class="font-bold text-sm mb-1">Container #${props.container_id}</h3>
          <p class="text-xs"><strong>Stop Order:</strong> ${props.order}</p>
          <p class="text-xs"><strong>Distance from previous:</strong> ${props.distance_from_previous_km} km</p>
          <p class="text-xs"><strong>Total distance:</strong> ${props.cumulative_distance_km} km</p>
        </div>
      `)
    }

    if (props.type === 'route') {
      layer.bindPopup(`
        <div class="p-2">
          <h3 class="font-bold text-sm mb-1">Optimized Route</h3>
          <p class="text-xs"><strong>Total Distance:</strong> ${props.total_distance_km} km</p>
          <p class="text-xs"><strong>Total Containers:</strong> ${props.total_containers}</p>
        </div>
      `)
    }
  }

  const getRouteStyle = (feature: any) => {
    if (feature?.properties?.type === 'route') {
      return {
        color: '#3b82f6',
        weight: 4,
        opacity: 0.8
      }
    }
    return {}
  }

  // Extract route statistics from GeoJSON
  const getRouteStats = () => {
    if (!routeResult?.geojson?.features) return null

    const routeFeature = routeResult.geojson.features.find(
      (f: any) => f.properties?.type === 'route'
    )

    if (!routeFeature) return null

    return {
      total_distance: routeFeature.properties.total_distance_km,
      total_containers: routeFeature.properties.total_containers
    }
  }

  const stats = getRouteStats()

  return (
    <div className="flex h-full">
      <div className="w-96 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Create Neighborhood Route</h1>

          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Route Parameters</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Neighborhood
                  </label>
                  <select
                    value={selectedNeighborhood}
                    onChange={(e) => setSelectedNeighborhood(e.target.value)}
                    disabled={loading}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  >
                    {neighborhoods.map((neighborhood) => (
                      <option key={neighborhood} value={neighborhood}>
                        {neighborhood}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Week Start Date
                  </label>
                  <input
                    type="date"
                    value={weekStartDate}
                    onChange={(e) => setWeekStartDate(e.target.value)}
                    disabled={loading}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  />
                </div>

                <div className="flex items-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <input
                    type="checkbox"
                    id="quickMode"
                    checked={quickMode}
                    onChange={(e) => setQuickMode(e.target.checked)}
                    disabled={loading}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <label htmlFor="quickMode" className="text-sm text-gray-700 cursor-pointer">
                    <span className="font-medium">Quick Mode</span> - Faster optimization
                  </label>
                </div>

                <button
                  onClick={handleGenerateRoute}
                  disabled={loading || !selectedNeighborhood || !weekStartDate}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                >
                  {loading ? 'Optimizing Route...' : 'Generate Optimized Route'}
                </button>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
              </div>
            </div>

            {routeResult && stats && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-gray-900">Route Results</h2>

                <div className="p-4 bg-gray-50 rounded-md">
                  <h3 className="font-medium text-gray-900 mb-2">Vehicle Assignment</h3>
                  <p className="text-sm text-gray-700"><strong>Type:</strong> {routeResult.vehicle_type}</p>
                  <p className="text-sm text-gray-700"><strong>ID:</strong> {routeResult.vehicle_id}</p>
                </div>

                <div className="p-4 bg-gray-50 rounded-md">
                  <h3 className="font-medium text-gray-900 mb-2">Route Statistics</h3>
                  <p className="text-sm text-gray-700">
                    <strong>Total Containers:</strong> {stats.total_containers}
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>Total Distance:</strong> {stats.total_distance} km
                  </p>
                </div>

                {routeResult.schedule && routeResult.schedule.length > 0 && (
                  <div className="p-4 bg-gray-50 rounded-md">
                    <h3 className="font-medium text-gray-900 mb-2">Collection Schedule</h3>
                    <div className="space-y-2">
                      {routeResult.schedule.map((day, idx) => (
                        <div key={idx} className="text-sm">
                          <p className="font-medium text-gray-900">
                            {day.day || `Day ${idx + 1}`}
                          </p>
                          <p className="text-gray-600">
                            {day.containers || 0} containers, {day.distance_km || 0} km
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={handleDownloadGeoJSON}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 font-medium"
                >
                  Download GeoJSON
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1">
        <MapContainer center={center} zoom={12} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {routeResult && routeResult.geojson && (
            <GeoJSON
              key={JSON.stringify(routeResult.geojson)}
              data={routeResult.geojson}
              style={getRouteStyle}
              pointToLayer={pointToLayer}
              onEachFeature={onEachFeature}
            />
          )}
        </MapContainer>
      </div>
    </div>
  )
}

export default RouteCreator
