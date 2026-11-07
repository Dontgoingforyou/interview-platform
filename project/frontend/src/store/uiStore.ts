/**
 * Состояние UI: сайдбар и мобильное меню.
 * Свёрнутость сайдбара — в localStorage (`sidebarCollapsed`).
 */
import { create } from 'zustand'

const SIDEBAR_KEY = 'sidebarCollapsed'

function readCollapsedFromStorage(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_KEY) === 'true'
  } catch {
    return false
  }
}

interface UiState {
  sidebarCollapsed: boolean
  mobileMenuOpen: boolean
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void
  setMobileMenuOpen: (open: boolean) => void
  toggleMobileMenu: () => void
}

export const useUiStore = create<UiState>((set, get) => ({
  sidebarCollapsed: readCollapsedFromStorage(),
  mobileMenuOpen: false,

  setSidebarCollapsed: (collapsed) => {
    try {
      localStorage.setItem(SIDEBAR_KEY, collapsed ? 'true' : 'false')
    } catch {
      /* игнорируем private mode */
    }
    set({ sidebarCollapsed: collapsed })
  },

  toggleSidebar: () => {
    const next = !get().sidebarCollapsed
    get().setSidebarCollapsed(next)
  },

  setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),

  toggleMobileMenu: () => set((s) => ({ mobileMenuOpen: !s.mobileMenuOpen })),
}))
