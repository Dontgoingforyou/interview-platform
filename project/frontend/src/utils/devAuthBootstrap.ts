/**
 * После rehydrate zustand persist подставляет фиктивную сессию в dev bypass режиме.
 */
import { DEV_BYPASS_ACCESS_TOKEN, getDevMockUser, isDevBypassAuth } from '../constants/devAuth'
import { useAuthStore } from '../store/authStore'

export function applyDevBypassIfNeeded(): void {
  if (!isDevBypassAuth()) {
    return
  }
  const s = useAuthStore.getState()
  if (s.accessToken && s.accessToken !== DEV_BYPASS_ACCESS_TOKEN && s.user) {
    return
  }
  useAuthStore.setState({
    accessToken: DEV_BYPASS_ACCESS_TOKEN,
    refreshToken: null,
    expiresAt: Date.now() + 86400000,
    user: getDevMockUser(),
  })
}
