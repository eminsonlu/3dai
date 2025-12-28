"""Route optimization service using Ant Colony Optimization (ACO) with OSRM."""

import requests
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Depot location (from route.md)
DEPOT_LOCATION = {
    "lat": 40.19653566137532,
    "lon": 28.93751059947524
}

# OSRM configuration
OSRM_BASE_URL = "http://localhost:5001"

# ACO Parameters
ACO_NUM_ANTS = 100          # Number of ants per iteration
ACO_NUM_ITERATIONS = 20      # Number of iterations
ACO_ALPHA = 1.0             # Pheromone importance
ACO_BETA = 2.0              # Distance heuristic importance
ACO_RHO = 0.1               # Evaporation rate
ACO_Q = 100.0               # Pheromone deposit factor
ACO_ELITE_WEIGHT = 2.0      # Extra weight for best solution
ACO_INITIAL_PHEROMONE = 0.01  # Initial pheromone level


@dataclass
class Container:
    """Container data model for routing."""
    container_id: int
    latitude: float
    longitude: float
    vehicle_type: str


@dataclass
class RouteStop:
    """A stop in the route."""
    container_id: int
    latitude: float
    longitude: float
    distance_from_previous: float
    cumulative_distance: float
    order: int
    geometry_to_here: Optional[List] = None  # Route geometry from previous stop


@dataclass
class RouteResult:
    """Complete route optimization result."""
    neighborhood: str
    vehicle_type: str
    total_distance_km: float
    total_containers: int
    stops: List[RouteStop]
    requires_multiple_trips: bool
    trip_count: int


class OSRMClient:
    """Client for OSRM routing API."""

    def __init__(self, base_url: str = OSRM_BASE_URL):
        self.base_url = base_url

    def get_distance(self, from_point: Dict, to_point: Dict) -> Tuple[Optional[float], Optional[List]]:
        """
        Get driving distance and route geometry between two points using OSRM.

        Args:
            from_point: Dictionary with 'lat' and 'lon' keys
            to_point: Dictionary with 'lat' and 'lon' keys

        Returns:
            Tuple of (distance in kilometers, route geometry coordinates)
        """
        try:
            # OSRM expects lon,lat format
            coords = f"{from_point['lon']},{from_point['lat']};{to_point['lon']},{to_point['lat']}"
            url = f"{self.base_url}/route/v1/driving/{coords}"

            params = {
                "overview": "full",
                "geometries": "geojson"
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                # Distance is in meters, convert to km
                distance_m = route["distance"]
                geometry = route["geometry"]["coordinates"]
                return distance_m / 1000.0, geometry

            logger.warning(f"OSRM returned no route: {data.get('code')}")
            return None, None

        except requests.exceptions.RequestException as e:
            logger.error(f"OSRM request failed: {e}")
            # Fallback to Euclidean distance if OSRM fails
            return self._euclidean_distance(from_point, to_point), None

    def _euclidean_distance(self, from_point: Dict, to_point: Dict) -> float:
        """Fallback: Calculate approximate distance using Haversine formula."""
        import math

        lat1, lon1 = math.radians(from_point['lat']), math.radians(from_point['lon'])
        lat2, lon2 = math.radians(to_point['lat']), math.radians(to_point['lon'])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in km
        r = 6371

        return c * r


class RouteOptimizer:
    """Route optimizer using Nearest Neighbor algorithm."""

    def __init__(self, osrm_client: Optional[OSRMClient] = None):
        self.osrm = osrm_client or OSRMClient()

    def optimize_route(
        self,
        neighborhood: str,
        containers: List[Container],
        vehicle_capacity: int = 40,
        depot: Dict = None
    ) -> RouteResult:
        """
        Optimize route for containers using Nearest Neighbor algorithm.

        Args:
            neighborhood: Neighborhood name
            containers: List of containers to collect
            vehicle_capacity: Maximum containers per trip
            depot: Starting location (defaults to DEPOT_LOCATION)

        Returns:
            RouteResult with optimized stops
        """
        if not containers:
            raise ValueError("No containers provided")

        depot = depot or DEPOT_LOCATION
        vehicle_type = containers[0].vehicle_type if containers else "Unknown"

        # Check if multiple trips needed
        requires_multiple_trips = len(containers) > vehicle_capacity
        trip_count = (len(containers) + vehicle_capacity - 1) // vehicle_capacity

        # For now, optimize single trip (can be extended for multiple trips)
        containers_to_route = containers[:vehicle_capacity]

        stops = self._create_aco_route(depot, containers_to_route)

        # Calculate total distance
        total_distance = sum(stop.distance_from_previous for stop in stops)

        # Add return to depot
        if stops:
            last_stop = stops[-1]
            return_distance, _ = self.osrm.get_distance(
                {"lat": last_stop.latitude, "lon": last_stop.longitude},
                depot
            )
            if return_distance is not None:
                total_distance += return_distance

        return RouteResult(
            neighborhood=neighborhood,
            vehicle_type=vehicle_type,
            total_distance_km=total_distance,
            total_containers=len(containers_to_route),
            stops=stops,
            requires_multiple_trips=requires_multiple_trips,
            trip_count=trip_count
        )

    def _build_distance_matrix(
        self,
        depot: Dict,
        containers: List[Container]
    ) -> Tuple[np.ndarray, Dict]:
        """
        Build distance matrix for all pairs of locations (depot + containers).
        Also cache geometry for route reconstruction.

        Args:
            depot: Starting depot location
            containers: List of containers

        Returns:
            Tuple of (distance_matrix, geometry_cache)
            - distance_matrix[i][j] = distance from location i to j
            - geometry_cache[(i,j)] = route geometry from i to j
        """
        n = len(containers) + 1  # +1 for depot
        distance_matrix = np.zeros((n, n))
        geometry_cache = {}

        # Build list of all locations (depot first, then containers)
        locations = [depot] + [
            {"lat": c.latitude, "lon": c.longitude} for c in containers
        ]

        # Calculate distances for all pairs
        for i in range(n):
            for j in range(n):
                if i == j:
                    distance_matrix[i][j] = 0.0
                    continue

                distance, geometry = self.osrm.get_distance(locations[i], locations[j])

                if distance is not None:
                    distance_matrix[i][j] = distance
                    geometry_cache[(i, j)] = geometry
                else:
                    # Fallback: use large distance if OSRM fails
                    distance_matrix[i][j] = 999.0
                    logger.warning(f"Could not get distance from {i} to {j}")

        logger.info(f"Built distance matrix: {n}x{n} locations")
        return distance_matrix, geometry_cache

    def _initialize_pheromones(self, n: int) -> np.ndarray:
        """
        Initialize pheromone matrix with equal small values.

        Args:
            n: Number of locations (depot + containers)

        Returns:
            Pheromone matrix (n x n)
        """
        return np.full((n, n), ACO_INITIAL_PHEROMONE)

    def _select_next_container(
        self,
        current_idx: int,
        unvisited_indices: List[int],
        pheromones: np.ndarray,
        distances: np.ndarray
    ) -> int:
        """
        Probabilistically select next container based on pheromone and distance.

        Args:
            current_idx: Current location index
            unvisited_indices: List of unvisited container indices
            pheromones: Pheromone matrix
            distances: Distance matrix

        Returns:
            Index of selected next container
        """
        probabilities = []

        for idx in unvisited_indices:
            # Pheromone factor
            tau = pheromones[current_idx][idx] ** ACO_ALPHA

            # Heuristic factor (inverse of distance)
            if distances[current_idx][idx] > 0:
                eta = (1.0 / distances[current_idx][idx]) ** ACO_BETA
            else:
                eta = 0.0

            probabilities.append(tau * eta)

        # Normalize probabilities
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            # If all probabilities are 0, use uniform distribution
            probabilities = [1.0 / len(unvisited_indices)] * len(unvisited_indices)

        # Select next container using roulette wheel selection
        selected_idx = random.choices(unvisited_indices, weights=probabilities)[0]
        return selected_idx

    def _construct_ant_solution(
        self,
        pheromones: np.ndarray,
        distances: np.ndarray,
        num_containers: int
    ) -> Tuple[List[int], float]:
        """
        Construct a complete tour for a single ant.

        Args:
            pheromones: Pheromone matrix
            distances: Distance matrix
            num_containers: Number of containers to visit

        Returns:
            Tuple of (tour, total_distance)
            - tour: List of container indices in visit order (0-indexed from containers)
            - total_distance: Total tour distance
        """
        # Start at depot (index 0)
        current_idx = 0
        unvisited = list(range(1, num_containers + 1))  # Container indices (1 to n)
        tour = []
        total_distance = 0.0

        # Visit all containers
        while unvisited:
            next_idx = self._select_next_container(current_idx, unvisited, pheromones, distances)
            tour.append(next_idx - 1)  # Convert to 0-indexed container list
            total_distance += distances[current_idx][next_idx]
            unvisited.remove(next_idx)
            current_idx = next_idx

        # Return to depot
        total_distance += distances[current_idx][0]

        return tour, total_distance

    def _update_pheromones(
        self,
        pheromones: np.ndarray,
        all_tours: List[Tuple[List[int], float]],
        best_tour: Tuple[List[int], float],
        global_best_tour: Tuple[List[int], float]
    ) -> np.ndarray:
        """
        Update pheromone matrix: evaporation + deposit.

        Args:
            pheromones: Current pheromone matrix
            all_tours: All ant tours from current iteration
            best_tour: Best tour from current iteration
            global_best_tour: Best tour found so far

        Returns:
            Updated pheromone matrix
        """
        n = pheromones.shape[0]

        # Evaporation
        pheromones = (1 - ACO_RHO) * pheromones

        # Deposit pheromone from best iteration tour
        tour_indices, tour_distance = best_tour
        if tour_distance > 0:
            deposit = ACO_Q / tour_distance

            # Depot to first container
            pheromones[0][tour_indices[0] + 1] += deposit

            # Between containers
            for i in range(len(tour_indices) - 1):
                from_idx = tour_indices[i] + 1
                to_idx = tour_indices[i + 1] + 1
                pheromones[from_idx][to_idx] += deposit

            # Last container to depot
            pheromones[tour_indices[-1] + 1][0] += deposit

        # Elite ant: deposit extra pheromone from global best
        if global_best_tour and global_best_tour[1] > 0:
            tour_indices, tour_distance = global_best_tour
            deposit = ACO_ELITE_WEIGHT * ACO_Q / tour_distance

            # Depot to first container
            pheromones[0][tour_indices[0] + 1] += deposit

            # Between containers
            for i in range(len(tour_indices) - 1):
                from_idx = tour_indices[i] + 1
                to_idx = tour_indices[i + 1] + 1
                pheromones[from_idx][to_idx] += deposit

            # Last container to depot
            pheromones[tour_indices[-1] + 1][0] += deposit

        return pheromones

    def _two_opt(
        self,
        tour: List[int],
        distance_matrix: np.ndarray
    ) -> List[int]:
        """
        Improve a tour using the 2-opt local search algorithm.
        It repeatedly searches for pairs of edges that can be swapped to reduce the tour length.

        Args:
            tour: A list of container indices (0-indexed from the containers list).
            distance_matrix: The distance matrix where index 0 is the depot.

        Returns:
            The improved tour as a list of container indices.
        """
        best_tour = tour
        path = [0] + [i + 1 for i in best_tour] + [0]  # Full path with depot
        improved = True
        while improved:
            improved = False
            for i in range(1, len(path) - 2):
                for j in range(i + 1, len(path) - 1):
                    # Consider edges (i-1, i) and (j, j+1)
                    # Current: ... (i-1) -> i ... j -> (j+1) ...
                    # New:     ... (i-1) -> j ... i -> (j+1) ... (reverse segment i to j)
                    
                    current_dist = distance_matrix[path[i-1], path[i]] + distance_matrix[path[j], path[j+1]]
                    new_dist = distance_matrix[path[i-1], path[j]] + distance_matrix[path[i], path[j+1]]

                    if new_dist < current_dist:
                        # Improvement found, reverse the segment from i to j
                        path[i:j+1] = reversed(path[i:j+1])
                        improved = True
                        # Break inner loops and restart search from the beginning
                        break
                if improved:
                    break
        
        # Return the container part of the tour, converting back to 0-indexed container indices
        return [node - 1 for node in path[1:-1]]

    def _create_aco_route(
        self,
        depot: Dict,
        containers: List[Container]
    ) -> List[RouteStop]:
        """
        Create route using Ant Colony Optimization (ACO) algorithm.

        Args:
            depot: Starting depot location
            containers: List of containers to visit

        Returns:
            List of RouteStops in optimal order with geometry
        """
        if not containers:
            return []

        logger.info(f"Starting ACO optimization for {len(containers)} containers")

        # Step 1: Build distance matrix and cache geometry
        logger.info("Building distance matrix...")
        distance_matrix, geometry_cache = self._build_distance_matrix(depot, containers)

        # Step 2: Initialize pheromones
        n = len(containers) + 1  # +1 for depot
        pheromones = self._initialize_pheromones(n)

        # Step 3: Run ACO algorithm
        global_best_tour = None
        global_best_distance = float('inf')

        for iteration in range(ACO_NUM_ITERATIONS):
            logger.info(f"ACO Iteration {iteration + 1}/{ACO_NUM_ITERATIONS}")

            # Construct solutions for all ants
            iteration_tours = []
            for ant_id in range(ACO_NUM_ANTS):
                tour, distance = self._construct_ant_solution(
                    pheromones,
                    distance_matrix,
                    len(containers)
                )

                # Refine the ant's tour with 2-opt local search
                refined_tour = self._two_opt(tour, distance_matrix)

                # Recalculate distance for the refined tour
                refined_distance = 0.0
                path = [0] + [i + 1 for i in refined_tour] + [0]
                for k in range(len(path) - 1):
                    refined_distance += distance_matrix[path[k], path[k+1]]
                
                iteration_tours.append((refined_tour, refined_distance))

            # Find best tour in this iteration
            best_iter_tour = min(iteration_tours, key=lambda x: x[1])
            best_iter_distance = best_iter_tour[1]

            # Update global best
            if best_iter_distance < global_best_distance:
                global_best_tour = best_iter_tour
                global_best_distance = best_iter_distance
                logger.info(f"New best distance: {global_best_distance:.2f} km")

            # Update pheromones
            pheromones = self._update_pheromones(
                pheromones,
                iteration_tours,
                best_iter_tour,
                global_best_tour
            )

        logger.info(f"ACO completed. Best distance: {global_best_distance:.2f} km")

        # Step 4: Reconstruct route with RouteStop objects and geometry
        if global_best_tour is None:
            logger.error("ACO failed to find a tour")
            return []

        tour_indices, _ = global_best_tour
        route_stops = []
        cumulative_distance = 0.0

        # Depot to first container
        prev_idx = 0
        for order, container_idx in enumerate(tour_indices, start=1):
            curr_idx = container_idx + 1  # +1 for depot offset

            # Get distance and geometry
            segment_distance = distance_matrix[prev_idx][curr_idx]
            geometry = geometry_cache.get((prev_idx, curr_idx))

            cumulative_distance += segment_distance

            container = containers[container_idx]
            stop = RouteStop(
                container_id=container.container_id,
                latitude=container.latitude,
                longitude=container.longitude,
                distance_from_previous=segment_distance,
                cumulative_distance=cumulative_distance,
                order=order,
                geometry_to_here=geometry
            )
            route_stops.append(stop)

            prev_idx = curr_idx

        return route_stops

    def _create_nearest_neighbor_route(
        self,
        start_point: Dict,
        containers: List[Container]
    ) -> List[RouteStop]:
        """
        Create route using Nearest Neighbor (greedy) algorithm.

        Args:
            start_point: Starting location
            containers: List of containers to visit

        Returns:
            List of RouteStops in optimal order
        """
        route = []
        unvisited = containers.copy()
        current_location = start_point
        cumulative_distance = 0.0
        order = 1

        while unvisited:
            nearest_container = None
            min_distance = float('inf')
            best_geometry = None

            # Find nearest unvisited container
            for container in unvisited:
                container_point = {
                    "lat": container.latitude,
                    "lon": container.longitude
                }

                distance, geometry = self.osrm.get_distance(current_location, container_point)

                if distance is not None and distance < min_distance:
                    min_distance = distance
                    best_geometry = geometry
                    nearest_container = container

            if nearest_container is None:
                logger.warning("Could not find route to remaining containers")
                break

            # Add to route
            cumulative_distance += min_distance

            stop = RouteStop(
                container_id=nearest_container.container_id,
                latitude=nearest_container.latitude,
                longitude=nearest_container.longitude,
                distance_from_previous=min_distance,
                cumulative_distance=cumulative_distance,
                order=order,
                geometry_to_here=best_geometry
            )

            route.append(stop)
            unvisited.remove(nearest_container)

            # Update current location
            current_location = {
                "lat": nearest_container.latitude,
                "lon": nearest_container.longitude
            }

            order += 1

            logger.debug(
                f"Added container {nearest_container.container_id} "
                f"(distance: {min_distance:.2f}km, total: {cumulative_distance:.2f}km)"
            )

        return route
