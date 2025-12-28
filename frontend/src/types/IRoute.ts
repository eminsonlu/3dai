export interface IRouteProperties {
  route_id: number
  vehicle_id: number
  vehicle_name: string
  vehicle_type: string
  route_date: string
  start_time: string
  end_time: string
  duration_minutes: number
  total_distance_km: number
}

export interface IRouteFeature {
  type: 'Feature'
  geometry: {
    type: 'LineString'
    coordinates: number[][]
  }
  properties: IRouteProperties
}

export interface IRouteGeoJSON {
  type: 'FeatureCollection'
  features: IRouteFeature[]
}

export interface IRouteStats {
  total_routes: number
  total_vehicles: number
  total_days: number
  total_distance_km: number
  avg_duration_minutes: number
}

export interface IRouteRequest {
  neighborhood: string
  week_start_date: string
  quick_mode?: boolean
}

export interface IScheduleDay {
  date: string
  day_name: string
  start_hour: number
  end_hour: number
  start_time: string
  end_time: string
}

export interface IOptimizedRouteResponse {
  neighborhood: string
  week_start_date: string
  vehicle_type: string
  vehicle_id: string
  schedule: IScheduleDay[]
  geojson: any
}

export interface INeighborhoodList {
  neighborhoods: string[]
}
