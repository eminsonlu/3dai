Here is a basic guide to creating a route for a single neighborhood with 55 containers. We will use the "Nearest Neighbor" (Greedy) approach.

Think of this like a game of "Connect the Dots," where you always draw a line to the closest dot you haven't touched yet.

Phase 1: Preparation (Filter Your Data)
Before you calculate anything, you must ensure you are routing the correct items.

Select Neighborhood: Get all containers where neighborhood_id = X. (Total: 55).

Select Vehicle: Choose a vehicle (e.g., "Large Truck").

Filter by Type: Keep only the containers that this truck can lift.

Note: If your neighborhood has 50 "Large" bins and 5 "Underground" bins, you cannot make one route. You need two separate lists because they require different vehicles (Standard Truck vs. Crane Truck).

Assumption: Let's assume all 55 containers fit your "Large Truck".

Phase 2: The Logic (Step-by-Step)
You have a truck at the Depot and a list of 55 Unvisited Containers.

Start: Truck is at Depot.

Scan: Calculate the distance from the Depot to all 55 containers.

Select: Find the one with the shortest distance. Let's say it's Container #12.

Move: Drive to Container #12.

Add #12 to your Route List.

Remove #12 from your Unvisited List.

Repeat: Now, you are at #12. Calculate the distance from #12 to the remaining 54 containers.

Find the closest one (e.g., #08).

Drive there.

Loop: Keep doing this until the Unvisited List is empty.

Return: From the last container, drive back to Depot.

Phase 3: Python Implementation
Here is a Python script that implements this logic. It is simplified to be understandable.

(Note: This uses a placeholder for distance. In your real system, you would replace get_distance with your OSRM call.)

Python

import math

# 1. Setup Data (Mocking your database)
# Format: [id, lat, long]
depot = {'id': 'Depot', 'lat': 40.18, 'long': 29.06}

# Imagine this is your list of 55 containers from the DB
containers = [
    {'id': 101, 'lat': 40.182, 'long': 29.063},
    {'id': 102, 'lat': 40.185, 'long': 29.065},
    {'id': 103, 'lat': 40.181, 'long': 29.061},
    # ... imagine 52 more here ...
]

def get_distance(p1, p2):
    """
    In real life: Call your OSRM API here.
    For this example: We use simple math (Euclidean) to show logic.
    """
    return math.sqrt((p1['lat'] - p2['lat'])**2 + (p1['long'] - p2['long'])**2)

def create_route(start_point, all_containers):
    route = []
    unvisited = all_containers.copy()
    current_location = start_point

    total_dist = 0

    # 2. The Main Loop
    while len(unvisited) > 0:
        nearest_container = None
        min_dist = float('inf') # Infinity

        # Find the closest neighbor to WHERE WE ARE NOW
        for container in unvisited:
            dist = get_distance(current_location, container)

            if dist < min_dist:
                min_dist = dist
                nearest_container = container

        # We found the next step!
        route.append(nearest_container['id'])
        total_dist += min_dist

        # Update our status
        current_location = nearest_container
        unvisited.remove(nearest_container)
        print(f"Driving to Container {nearest_container['id']} (Dist: {min_dist:.4f})")

    # 3. Return to Depot
    return_dist = get_distance(current_location, start_point)
    total_dist += return_dist

    print("--- Route Finished ---")
    print(f"Total Distance: {total_dist:.4f}")
    return route

# Run it
final_route = create_route(depot, containers)
print(f"Final Order: {final_route}")
Phase 4: What if the truck gets full? (Capacity Constraint)
Your Vehicles table likely has a capacity (e.g., "Can take 40 containers"). But you have 55 containers.

You need to add a simple check inside the loop:

Python

vehicle_capacity = 40
current_load = 0

# Inside the While Loop...
    # (Find nearest container logic...)

    current_load += 1 # Or add container volume if you have it

    if current_load >= vehicle_capacity:
        print("Truck is full! Returning to Depot to empty...")
        # Add distance to depot
        # Reset current_location to Depot
        # Reset current_load to 0
        # Continue the loop for the remaining 15 containers
Summary of Next Steps
Query: Select 55 containers from one neighborhood.

Distance Function: Replace the math in my script with your OSRM requests.get code.

Run: Execute the script. It will give you a list like [103, 101, 102...].

Save: Save this order into your Routes or a RouteSteps table.

DEPOT PLACE OR ROUTE START: 40.19653566137532, 28.93751059947524