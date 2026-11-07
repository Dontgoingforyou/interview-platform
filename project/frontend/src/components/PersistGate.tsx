import { type ReactNode, useEffect, useState } from 'react'

import { applyDevBypassIfNeeded } from '../utils/devAuthBootstrap'
import { useAuthStore } from '../store/authStore'

interface PersistGateProps {
  children: ReactNode
}

/**
 * Ждёт восстановления zustand persist из localStorage, затем применяет dev bypass.
 * Иначе первый кадр видит «не залогинен» и мигает редирект на /login.
 */
function PersistGate({ children }: PersistGateProps) {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    async function finish() {
      applyDevBypassIfNeeded()
      setReady(true)
    }
    if (useAuthStore.persist.hasHydrated()) {
      queueMicrotask(finish)
      return
    }
    const unsub = useAuthStore.persist.onFinishHydration(finish)
    return unsub
  }, [])

  if (!ready) {
    return (
      <div
        style={{
          padding: '1.5rem',
          fontFamily: 'system-ui, sans-serif',
          color: 'var(--text-secondary, #888)',
        }}
      >
        Загрузка…
      </div>
    )
  }

  return children
}

export default PersistGate
