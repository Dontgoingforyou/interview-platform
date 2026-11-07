import { describe, expect, it } from 'vitest'

import { ABSENCE_STATUS_OPTIONS } from '../../constants/absenceStatuses'

describe('ABSENCE_STATUS_OPTIONS', () => {
  it('содержит ожидаемые коды статусов отсутствия', () => {
    expect(ABSENCE_STATUS_OPTIONS.map((o) => o.value)).toEqual([
      'болеет',
      'отпуск',
      'уехал',
      'другое',
    ])
  })

  it('у каждой опции непустая подпись', () => {
    for (const o of ABSENCE_STATUS_OPTIONS) {
      expect(o.label.trim().length).toBeGreaterThan(0)
    }
  })
})
