import { useEffect, useState } from 'react'
import { Polyline, Marker, useMap } from 'react-leaflet'
import L from 'leaflet'
import type { IRouteFeature } from '../../types/IRoute'

interface IAnimatedRouteProps {
  route: IRouteFeature
  onComplete: () => void
}

// Start marker icon
const startIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

// End marker icon
const endIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

// Moving marker icon
const truckIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

export const AnimatedRoute = ({ route, onComplete }: IAnimatedRouteProps) => {
  const map = useMap()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [animatedPath, setAnimatedPath] = useState<[number, number][]>([])

  const coordinates = route.geometry.coordinates.map(
    ([lon, lat]) => [lat, lon] as [number, number]
  )

  const startPoint = coordinates[0]
  const endPoint = coordinates[coordinates.length - 1]

  useEffect(() => {
    const bounds = L.latLngBounds(coordinates)
    map.fitBounds(bounds, { padding: [50, 50] })

    setCurrentIndex(0)
    setAnimatedPath([])

    const totalSteps = coordinates.length
    const animationDuration = 5000
    const stepDelay = animationDuration / totalSteps

    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= totalSteps - 1) {
          clearInterval(interval)
          setTimeout(onComplete, 1000)
          return prev
        }
        return prev + 1
      })
    }, stepDelay)

    return () => clearInterval(interval)
  }, [route, map, onComplete])

  useEffect(() => {
    setAnimatedPath(coordinates.slice(0, currentIndex + 1))
  }, [currentIndex])

  const currentPosition = coordinates[currentIndex]

  return (
    <>
      <Marker position={startPoint} icon={startIcon}>
        <div className="font-semibold">Start</div>
      </Marker>

      <Marker position={endPoint} icon={endIcon}>
        <div className="font-semibold">End</div>
      </Marker>

      {animatedPath.length > 1 && (
        <Polyline
          positions={animatedPath}
          pathOptions={{
            color: '#3b82f6',
            weight: 5,
            opacity: 0.8,
          }}
        />
      )}

      <Polyline
        positions={coordinates}
        pathOptions={{
          color: '#cbd5e1',
          weight: 3,
          opacity: 0.4,
          dashArray: '5, 10',
        }}
      />

      {currentPosition && (
        <Marker position={currentPosition} icon={truckIcon}>
          <div className="font-semibold">
            {route.properties.vehicle_name}
          </div>
        </Marker>
      )}
    </>
  )
}
