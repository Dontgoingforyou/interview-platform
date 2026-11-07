import { useEffect } from 'react'

const INTERNAL_NAV_KEY = 'student_logout_internal_nav'
const INTERNAL_NAV_MAX_AGE_MS = 2000

function isRecentInternalNav(): boolean {
  try {
    const t = sessionStorage.getItem(INTERNAL_NAV_KEY)
    if (!t) {
      return false
    }
    return Date.now() - parseInt(t, 10) < INTERNAL_NAV_MAX_AGE_MS
  } catch {
    return false
  }
}

/**
 * При закрытии вкладки — beacon на выход из Django-сессии.
 * clearSession не вызывается: нет надёжного способа отличить reload от закрытия вкладки
 * в синхронном обработчике pagehide. Django-сессия аннулируется беконом;
 * Сессия живёт в httpOnly-куке.
 */
export function useStudentLogoutOnTabClose(enabled: boolean) {
  useEffect(() => {
    if (!enabled) {
      return
    }

    function onPageHide() {
      if (isRecentInternalNav()) {
        return
      }
      const origin = window.location.origin
      const url = `${origin}/accounts/logout-beacon/?t=${Date.now()}`
      void fetch(url, { method: 'GET', credentials: 'include', keepalive: true }).catch(() => {})
    }

    window.addEventListener('pagehide', onPageHide)
    return () => window.removeEventListener('pagehide', onPageHide)
  }, [enabled])
}

/** Пометка внутренней навигации по клику на ссылку того же origin. */
export function useMarkStudentInternalLinkClicks(enabled: boolean) {
  useEffect(() => {
    if (!enabled) {
      return
    }
    function onClick(e: MouseEvent) {
      const el = (e.target as HTMLElement | null)?.closest?.('a')
      if (el instanceof HTMLAnchorElement && el.href && el.origin === window.location.origin) {
        try {
          sessionStorage.setItem(INTERNAL_NAV_KEY, String(Date.now()))
        } catch {
          /* ignore */
        }
      }
    }
    document.body.addEventListener('click', onClick, true)
    return () => document.body.removeEventListener('click', onClick, true)
  }, [enabled])
}
