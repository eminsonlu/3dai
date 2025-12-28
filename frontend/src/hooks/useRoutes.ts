import { useState, useEffect } from 'react'
import { getRoutes, getRouteStats } from '../services/routeService'
import type { IRouteGeoJSON, IRouteStats } from '../types/IRoute'

export const useRoutes = () => {
  const [routes, setRoutes] = useState<IRouteGeoJSON | null>(null)
  const [stats, setStats] = useState<IRouteStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRoutes = async () => {
    try {
      setLoading(true)
      setError(null)

      const [routesData, statsData] = await Promise.all([
        getRoutes(),
        getRouteStats(),
      ])

      setRoutes(routesData)
      setStats(statsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch routes')
      console.error('Error fetching routes:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRoutes()
  }, [])

  return { routes, stats, loading, error, refetch: fetchRoutes }
}
