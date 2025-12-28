# Frontend - Route Visualization

React + TypeScript + Leaflet map to visualize trash collection routes.

## Setup

```bash
# Install dependencies
npm install

# Configure environment
cp .env.example .env
```

## Development

```bash
npm run dev
```

Open http://localhost:5173

## Features

- ✓ Interactive map with Leaflet
- ✓ Route list sidebar with search & filter
- ✓ Multi-select routes (checkbox selection)
- ✓ Animated route playback (shows truck moving from start to end)
- ✓ Color-coded routes by vehicle
- ✓ Route details on click
- ✓ Statistics panel
- ✓ Filter by vehicle
- ✓ Search routes by name or date

## Structure

```
src/
├── containers/RouteMap/     # Map container
├── components/StatsPanel/   # Statistics component
├── services/                # API services
├── hooks/                   # Custom hooks
└── types/                   # TypeScript types
```
