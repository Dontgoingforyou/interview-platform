import { describe, expect, it } from 'vitest'

import { isHrAllowedPath } from '../../constants/hrRoutes'

describe('isHrAllowedPath', () => {
  it('разрешает корень', () => {
    expect(isHrAllowedPath('/')).toBe(true)
    expect(isHrAllowedPath('')).toBe(true)
  })

  it('разрешает списки и разделы из whitelist', () => {
    expect(isHrAllowedPath('/interviews')).toBe(true)
    expect(isHrAllowedPath('/interviews-database')).toBe(true)
    expect(isHrAllowedPath('/interns')).toBe(true)
    expect(isHrAllowedPath('/companies')).toBe(true)
    expect(isHrAllowedPath('/managers')).toBe(true)
    expect(isHrAllowedPath('/employees')).toBe(true)
    expect(isHrAllowedPath('/employees/some@mail')).toBe(true)
  })

  it('запрещает админские и посторонние разделы', () => {
    expect(isHrAllowedPath('/knowledge-base')).toBe(false)
    expect(isHrAllowedPath('/debts')).toBe(false)
    expect(isHrAllowedPath('/help')).toBe(false)
    expect(isHrAllowedPath('/employees/admin/kpi')).toBe(false)
  })

  it('запрещает формы создания и редактирования', () => {
    expect(isHrAllowedPath('/interviews/new')).toBe(false)
    expect(isHrAllowedPath('/interviews/12/edit')).toBe(false)
    expect(isHrAllowedPath('/interviews/12/duplicate')).toBe(false)
    expect(isHrAllowedPath('/interns/new')).toBe(false)
    expect(isHrAllowedPath('/interns/5/edit')).toBe(false)
  })
})
