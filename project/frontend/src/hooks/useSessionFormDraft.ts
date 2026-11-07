import { useCallback, useEffect, useRef } from 'react'

/**
 * Черновик формы в sessionStorage (только пока открыта вкладка).
 * Восстановление один раз при монтировании; сохранение с debounce при изменении полей.
 */
export function useSessionFormDraft<T extends Record<string, unknown>>({
  storageKey,
  form,
  setForm,
  enabled,
  debounceMs = 550,
}: {
  storageKey: string
  form: T
  setForm: React.Dispatch<React.SetStateAction<T>>
  enabled: boolean
  debounceMs?: number
}) {
  const hydrated = useRef(false)

  useEffect(() => {
    if (!enabled || hydrated.current) {
      return
    }
    hydrated.current = true
    try {
      const raw = sessionStorage.getItem(storageKey)
      if (!raw) {
        return
      }
      const parsed = JSON.parse(raw) as Partial<T>
      if (!parsed || typeof parsed !== 'object') {
        return
      }
      const keys = Object.keys(parsed as object).filter((k) => {
        const v = (parsed as Record<string, unknown>)[k]
        return v !== undefined && v !== ''
      })
      if (keys.length === 0) {
        return
      }
      setForm((prev) => ({ ...prev, ...parsed }))
    } catch {
      try {
        sessionStorage.removeItem(storageKey)
      } catch {
        /* ignore */
      }
    }
  }, [enabled, storageKey, setForm])

  useEffect(() => {
    if (!enabled) {
      return
    }
    const id = window.setTimeout(() => {
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(form))
      } catch {
        /* quota / private mode */
      }
    }, debounceMs)
    return () => clearTimeout(id)
  }, [form, enabled, storageKey, debounceMs])

  const clearDraft = useCallback(() => {
    try {
      sessionStorage.removeItem(storageKey)
    } catch {
      /* ignore */
    }
  }, [storageKey])

  return { clearDraft }
}
