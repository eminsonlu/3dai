import { create } from 'zustand'

interface IRouteStore {
  selectedRouteIds: number[]
  animatingRouteId: number | null
  toggleRouteSelection: (routeId: number) => void
  selectAllRoutes: (routeIds: number[]) => void
  clearSelection: () => void
  setAnimatingRoute: (routeId: number | null) => void
}

export const useRouteStore = create<IRouteStore>((set) => ({
  selectedRouteIds: [],
  animatingRouteId: null,

  toggleRouteSelection: (routeId) =>
    set((state) => ({
      selectedRouteIds: state.selectedRouteIds.includes(routeId)
        ? state.selectedRouteIds.filter((id) => id !== routeId)
        : [...state.selectedRouteIds, routeId],
    })),

  selectAllRoutes: (routeIds) =>
    set({ selectedRouteIds: routeIds }),

  clearSelection: () =>
    set({ selectedRouteIds: [] }),

  setAnimatingRoute: (routeId) =>
    set({ animatingRouteId: routeId }),
}))
