"""GeoJSON conversion utilities."""

from typing import List


def route_to_geojson(route_indices: List[int], containers: List,
                     vehicle_info: dict, schedule: List[dict]) -> dict:
    """Convert optimized route to GeoJSON FeatureCollection.

    Args:
        route_indices: List of container indices in route order
        containers: List of container objects
        vehicle_info: Dictionary with vehicle information (type, id, distance, capacity)
        schedule: List of schedule dictionaries

    Returns:
        GeoJSON FeatureCollection dictionary
    """
    features = []

    # Create LineString for the route
    coordinates = []
    for idx in route_indices:
        container = containers[idx]
        coordinates.append([container.lon, container.lat])

    route_feature = {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': coordinates
        },
        'properties': {
            'feature_type': 'route',
            'vehicle_type': vehicle_info['vehicle_type'],
            'vehicle_id': vehicle_info['vehicle_id'],
            'total_distance_km': vehicle_info['total_distance_km'],
            'total_stops': len(route_indices) - route_indices.count(0),
            'schedule': schedule
        }
    }
    features.append(route_feature)

    # Create Point features for each container
    for sequence_num, idx in enumerate(route_indices):
        container = containers[idx]

        if container.is_depot:
            continue

        container_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [container.lon, container.lat]
            },
            'properties': {
                'feature_type': 'container',
                'container_id': container.id,
                'sequence': sequence_num,
                'neighborhood': container.neighborhood,
                'priority': round(container.priority, 2),
                'expected_fullness': round(container.expected_fullness, 3),
                'demand_kg': round(container.demand_kg, 2)
            }
        }
        features.append(container_feature)

    return {
        'type': 'FeatureCollection',
        'features': features
    }
