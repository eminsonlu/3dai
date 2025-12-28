# Frontend Route Optimization Implementation

## Overview

The frontend now fully integrates with the backend route optimization API, allowing users to create optimized trash collection routes for neighborhoods.

## Changes Made

### 1. **Updated `routeService.ts`**

Added the `optimizeRoute` function to communicate with the backend API:

```typescript
export const optimizeRoute = async (
  request: IRouteRequest
): Promise<IOptimizedRouteResponse> => {
  const response = await api.post('/api/optimize/route', request)
  return response.data
}
```

**Location**: `src/services/routeService.ts`

### 2. **Completely Rewrote `RouteCreator` Component**

The RouteCreator component was updated to match the new backend API structure:

**Features**:
- Neighborhood selection dropdown
- Week start date picker
- Quick mode toggle
- Route optimization with loading states
- Interactive map with custom markers:
  - **Blue Depot Marker (D)** - Starting location
  - **Green Numbered Markers** - Containers in collection order
  - **Blue Route Line** - Optimized path
- Statistics panel showing:
  - Vehicle type and ID
  - Total containers and distance
  - Collection schedule
- Download GeoJSON functionality

**Location**: `src/containers/RouteCreator/index.tsx`

**Removed**:
- Old optimization logic that referenced unused properties (`priority`, `expected_fullness`, `demand_kg`, `sequence`)
- Unused imports (`Marker`, `Popup`)
- Old feature type handling

### 3. **Updated `App.tsx` Routing**

Added the route creator page to the application:

```typescript
<Route path="/create-route" element={<RouteCreator />} />
```

**Location**: `src/App.tsx`

## User Interface

### Navigation

Two main pages accessible via the navigation bar:
1. **View Routes** (`/`) - View historical routes
2. **Create Route** (`/create-route`) - Create new optimized routes

### Create Route Page

**Left Sidebar (Parameters)**:
- **Neighborhood**: Select from available neighborhoods
- **Week Start Date**: Choose the Monday to start the week
- **Quick Mode**: Toggle for faster optimization (enabled by default)
- **Generate Button**: Starts the optimization process

**Right Side (Map)**:
Shows the optimized route with:
- Interactive markers with popups
- Color-coded visualization
- Route path overlay

**Results Section** (appears after optimization):
- Vehicle assignment details
- Route statistics
- Collection schedule
- Download GeoJSON button

## API Integration

### Endpoints Used

1. `GET /api/neighborhoods` - Fetch available neighborhoods
2. `POST /api/optimize/route` - Optimize route for selected neighborhood

### Request Format

```json
{
  "neighborhood": "19 MAYIS MAHALLESİ",
  "week_start_date": "2025-01-06",
  "quick_mode": true
}
```

### Response Format

The backend returns GeoJSON with:
- Depot point feature
- Container point features (with order, distances)
- Route line feature (with total distance and container count)

## Map Visualization

### Custom Markers

**Depot**:
- Blue circle with "D"
- 24x24px
- Always shown at the starting location

**Containers**:
- Green circles with collection order number (1, 2, 3...)
- 20x20px
- Shows popup with:
  - Container ID
  - Stop order
  - Distance from previous stop
  - Cumulative distance

**Route Line**:
- Blue line connecting all stops
- 4px weight
- 80% opacity
- Shows popup with total statistics

## File Structure

```
src/
├── App.tsx                          ✅ Updated - Added /create-route
├── services/
│   └── routeService.ts              ✅ Updated - Added optimizeRoute
├── containers/
│   └── RouteCreator/
│       └── index.tsx                ✅ Rewritten - New implementation
└── types/
    └── IRoute.ts                    ✅ Already had correct types
```

## Testing the Frontend

### Prerequisites

1. Backend running on `http://localhost:8000`
2. OSRM service running on `http://localhost:5000`
3. Database with neighborhoods and containers

### Steps to Test

1. **Start the frontend**:
   ```bash
   cd /Users/eminsonlu/Projects/trash-collection/routes/frontend
   npm run dev
   ```

2. **Open browser**: Navigate to `http://localhost:5173`

3. **Navigate to Create Route**: Click "Create Route" in the navigation

4. **Select parameters**:
   - Choose a neighborhood
   - Select a date
   - Keep Quick Mode enabled

5. **Generate route**: Click "Generate Optimized Route"

6. **View results**:
   - See the optimized route on the map
   - Check statistics in the sidebar
   - Click markers to see details
   - Download GeoJSON if needed

### Expected Behavior

- **Loading state**: "Optimizing Route..." button text while processing
- **Success**: Map shows depot, containers in order, and route line
- **Error**: Red error message if optimization fails
- **Statistics**: Accurate total distance and container count

## Environment Variables

Ensure your `.env` file has:

```bash
VITE_API_URL=http://localhost:8000
```

If not set, it defaults to `http://localhost:8000`.

## Error Handling

The component handles:
- **No neighborhoods**: Shows error message
- **API errors**: Displays error detail from backend
- **Missing fields**: Validates before submission
- **Loading states**: Disables buttons and shows loading text

## Performance Considerations

- **Quick Mode**: Recommended for testing (faster results)
- **Map re-rendering**: Uses `key` prop to force GeoJSON update
- **Marker icons**: Uses Leaflet divIcon for custom styling
- **Popup generation**: Inline HTML for better performance

## Future Improvements

Potential enhancements:
1. **Multiple trips**: Support for routes exceeding vehicle capacity
2. **Route editing**: Drag-and-drop to reorder stops
3. **Time estimates**: Show estimated collection times
4. **Comparison**: Compare multiple route strategies
5. **Export**: Additional export formats (PDF, Excel)
6. **Animation**: Animated route playback
7. **Clustering**: Group containers when zoomed out

## Troubleshooting

### Map not showing route

- Check browser console for errors
- Verify GeoJSON structure in response
- Check that backend is returning valid coordinates

### OSRM errors

- Ensure OSRM is running: `docker-compose ps osrm`
- Check OSRM logs: `docker-compose logs osrm`
- Verify OSRM health: `curl http://localhost:5000/health`

### Neighborhoods not loading

- Check backend API: `curl http://localhost:8000/api/neighborhoods`
- Verify database has neighborhoods
- Check CORS settings in backend

## Integration Checklist

- ✅ API service function added
- ✅ TypeScript types already defined
- ✅ Component rewritten for new API
- ✅ Routing configured
- ✅ Navigation already in place
- ✅ Error handling implemented
- ✅ Loading states added
- ✅ Map visualization working
- ✅ Download functionality included
- ✅ Unused code removed
