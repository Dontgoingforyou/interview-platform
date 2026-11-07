import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  DEV_BYPASS_ACCESS_TOKEN,
  getDevMockUser,
  isDevBypassAuth,
} from '../../constants/devAuth'

describe('devAuth', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('isDevBypassAuth false без VITE_DEV_BYPASS_AUTH', () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('PROD', false)
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'false')
    expect(isDevBypassAuth()).toBe(false)
  })

  it('isDevBypassAuth true только в DEV с флагом', () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('PROD', false)
    vi.stubEnv('VITE_DEV_BYPASS_AUTH', 'true')
    expect(isDevBypassAuth()).toBe(true)
  })

  it('getDevMockUser: роль admin по умолчанию', () => {
    vi.stubEnv('VITE_DEV_MOCK_ROLE', '')
    const u = getDevMockUser()
    expect(u.email).toBe('dev@local.invalid')
    expect(u.manager_role).toBe('admin')
    expect(u.groups).toContain('admin')
    expect(DEV_BYPASS_ACCESS_TOKEN).toBe('__DEV_BYPASS__')
  })

  it('getDevMockUser: hr / mentor / manager', () => {
    vi.stubEnv('VITE_DEV_MOCK_ROLE', 'hr')
    expect(getDevMockUser().manager_role).toBe('hr')
    expect(getDevMockUser().groups).toEqual(['hrs'])

    vi.stubEnv('VITE_DEV_MOCK_ROLE', 'mentor')
    expect(getDevMockUser().manager_role).toBe('mentor')
    expect(getDevMockUser().groups).toEqual(['mentors'])

    vi.stubEnv('VITE_DEV_MOCK_ROLE', 'manager')
    expect(getDevMockUser().manager_role).toBe('manager')
    expect(getDevMockUser().groups).toEqual(['employment'])
  })
})
