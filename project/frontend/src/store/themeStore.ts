/**
 * Тема: атрибут `data-theme` на `<html>` + сохранение в localStorage.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/** Тёмная тема по умолчанию — без атрибута data-theme (см. :root в index.css). */
export type ThemeId = 'dark' | 'light' | 'autumn' | 'winter' | 'spring' | 'summer'

export const THEME_PERSIST_KEY = 'interview-management-theme'

export function applyThemeToDocument(theme: ThemeId): void {
  const root = document.documentElement
  if (theme === 'dark') {
    root.removeAttribute('data-theme')
  } else {
    root.setAttribute('data-theme', theme)
  }
}

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Активный переход темы — при новом выборе предыдущий пропускается (иначе Chromium бросает InvalidStateError). */
let activeThemeViewTransition: ViewTransition | null = null

function applyThemeUpdate(theme: ThemeId, set: (partial: { theme: ThemeId }) => void): void {
  set({ theme })
  applyThemeToDocument(theme)
}

interface ThemeState {
  theme: ThemeId
  setTheme: (theme: ThemeId) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'dark',
      setTheme: (theme) => {
        const update = () => applyThemeUpdate(theme, set)

        if (prefersReducedMotion()) {
          update()
          return
        }

        const doc = document as Document & { startViewTransition?: (cb: () => void) => ViewTransition }
        if (typeof doc.startViewTransition !== 'function') {
          update()
          return
        }

        if (activeThemeViewTransition) {
          try {
            activeThemeViewTransition.skipTransition()
          } catch {
            /* переход уже завершён */
          }
        }

        const vt = doc.startViewTransition(update)
        activeThemeViewTransition = vt
        void vt.finished.finally(() => {
          if (activeThemeViewTransition === vt) {
            activeThemeViewTransition = null
          }
        })
      },
    }),
    {
      name: THEME_PERSIST_KEY,
      partialize: (s) => ({ theme: s.theme }),
      onRehydrateStorage: () => (state) => {
        if (state?.theme) {
          applyThemeToDocument(state.theme)
        }
      },
    },
  ),
)

export const THEME_OPTIONS: { id: ThemeId; label: string; icon: string }[] = [
  { id: 'dark', label: 'Тёмная', icon: '🌙' },
  { id: 'light', label: 'Светлая', icon: '☀️' },
  { id: 'autumn', label: 'Осень', icon: '🍂' },
  { id: 'winter', label: 'Зима', icon: '❄️' },
  { id: 'spring', label: 'Весна', icon: '🌸' },
  { id: 'summer', label: 'Лето', icon: '🌻' },
]
