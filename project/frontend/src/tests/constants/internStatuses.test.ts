import { describe, expect, it } from 'vitest'

import {
  INTERN_MANUAL_STATUS_FORM_OPTIONS,
  INTERN_STATUS_ACTIVE,
  INTERN_STATUS_FILTER_OPTIONS,
  INTERN_STATUS_LEFT,
  INTERN_STATUS_OFFER,
  INTERN_TRAINING_OPTIONS,
} from '../../constants/internStatuses'

describe('internStatuses', () => {
  it('коды статусов совпадают с опциями фильтра', () => {
    const values = INTERN_STATUS_FILTER_OPTIONS.map((o) => o.value)
    expect(values).toContain(INTERN_STATUS_ACTIVE)
    expect(values).toContain(INTERN_STATUS_LEFT)
    expect(values).toContain(INTERN_STATUS_OFFER)
    expect(values[0]).toBe('')
  })

  it('типы обучения и форма ручного статуса не пустые', () => {
    expect(INTERN_TRAINING_OPTIONS.length).toBeGreaterThan(0)
    expect(INTERN_MANUAL_STATUS_FORM_OPTIONS[0]?.value).toBe('')
  })
})
