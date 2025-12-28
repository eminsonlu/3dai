import { api } from './baseService'
import type {
  IRouteGeoJSON,
  IRouteStats,
  INeighborhoodList,
  IRouteRequest,
  IOptimizedRouteResponse
} from '../types/IRoute'

export const getRoutes = async (): Promise<IRouteGeoJSON> => {
  const response = await api.get('/api/routes')
  return response.data
}

export const getRouteStats = async (): Promise<IRouteStats> => {
  const response = await api.get('/api/routes/stats')
  return response.data
}

export const getNeighborhoods = async (): Promise<INeighborhoodList> => {
  const response = await api.get('/api/neighborhoods')
  return response.data
}

export const optimizeRoute = async (
  request: IRouteRequest
): Promise<IOptimizedRouteResponse> => {
  const response = await api.post('/api/optimize/route', request)
  return response.data
}
