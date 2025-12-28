# Route Viewer Features

## New Features Added

### 1. Route List Sidebar (Left Side)
- **Search**: Search routes by vehicle name or date
- **Filter**: Filter by specific vehicle
- **Select All / Deselect All**: Quick selection controls
- Shows route count (selected / total)

### 2. Multi-Select Routes
- Click on any route card to select/deselect (checkbox)
- Select multiple routes at once
- Only selected routes are shown on map
- If nothing selected, all routes are shown

### 3. Animated Route Playback
- Click "Animate Route" button on any selected route
- Shows:
  - **Green marker**: Start point
  - **Red marker**: End point
  - **Blue marker**: Moving truck
  - **Blue line**: Path traveled (draws as truck moves)
  - **Gray dashed line**: Full route preview
- Map auto-zooms to fit the route
- Animation duration: 5 seconds
- Auto-completes and returns to normal view

### 4. Route Details
- Click on any route line to see popup with:
  - Vehicle name & type
  - Date
  - Duration
  - Distance

### 5. Statistics Panel (Top Right)
- Total routes
- Total vehicles
- Total days
- Total distance
- Average duration

## How to Use

### View All Routes
1. Start the app
2. All routes shown on map by default
3. Different colors for different vehicles

### View Specific Routes
1. Use search bar to find routes
2. OR use vehicle dropdown filter
3. Click routes to select them
4. Only selected routes shown on map

### Animate a Route
1. Select a route (click to check it)
2. Click "Animate Route" button
3. Watch the truck move along the route
4. Animation completes and returns to normal

### Compare Routes
1. Select multiple routes (Ctrl/Cmd + click)
2. See them overlaid on map
3. Different colors help distinguish them

## Keyboard Shortcuts
- `Space` or `Enter` on focused route = Select/deselect route
- `Tab` = Navigate through route list

## State Management
- Uses Zustand for state (simple and clean)
- Selected routes persist during session
- Animation state managed globally
