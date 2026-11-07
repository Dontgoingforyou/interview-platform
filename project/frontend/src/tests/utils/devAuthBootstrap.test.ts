import { afterEach, describe, expect, it, vi } from 'vitest'

import { DEV_BYPASS_ACCESS_TOKEN } from '../../constants/devAuth'
import { useAuthStore } from '../../store/authStore'
import { applyDevBypassIfNeeded } from '../../utils/devAuthBootstrap'

describe('applyDevBypassIfNeeded', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    useAuthStore.setState({
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
      user: null,
    })
  })

  it('ничего не делает без bypass', () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('PROD', false)
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'false')
    applyDevBypassIfNeeded()
    expect(useAuthStore.getState().accessToken).toBeNull()
  })

  it('подставляет mock-сессию в bypass режиме', () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('PROD', false)
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'true')
    applyDevBypassIfNeeded()
    const s = useAuthStore.getState()
    expect(s.accessToken).toBe(DEV_BYPASS_ACCESS_TOKEN)
    expect(s.user?.email).toBe('dev@local.invalid')
  })

  it('не перетирает уже валидную SSO-сессию', () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('PROD', false)
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'true')
    useAuthStore.setState({
      accessToken: 'real-token',
      refreshToken: null,
      expiresAt: Date.now() + 10000,
      user: {
        email: 'real@example.com',
        username: 'real',
        full_name: 'Real',
        manager_role: 'manager',
        groups: [],
      },
    })
    applyDevBypassIfNeeded()
    expect(useAuthStore.getState().accessToken).toBe('real-token')
    expect(useAuthStore.getState().user?.email).toBe('real@example.com')
  })
})
