import { describe, expect, it } from 'vitest'

import { isMentorAllowedPath, MENTOR_DEFAULT_PATH } from '../../constants/mentorRoutes'

describe('isMentorAllowedPath', () => {
  it('разрешает /interviews-database', () => {
    expect(isMentorAllowedPath('/interviews-database')).toBe(true)
  })

  it('разрешает auth/login/no-access', () => {
    expect(isMentorAllowedPath('/auth/callback')).toBe(true)
    expect(isMentorAllowedPath('/login')).toBe(true)
    expect(isMentorAllowedPath('/no-access')).toBe(true)
  })

  it('запрещает корень и другие разделы', () => {
    expect(isMentorAllowedPath('/')).toBe(false)
    expect(isMentorAllowedPath('/interviews')).toBe(false)
    expect(isMentorAllowedPath('/interns')).toBe(false)
  })

  it('дефолтный путь — база собеседований', () => {
    expect(MENTOR_DEFAULT_PATH).toBe('/interviews-database')
  })
})
