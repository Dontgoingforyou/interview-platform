import { describe, expect, it } from 'vitest'

import { SAD_INTERN_STATUS, SAD_INTERN_STATUS_OPTIONS } from '../../constants/sadInternStatuses'

describe('sadInternStatuses', () => {
  it('опции покрывают все коды статуса', () => {
    const values = SAD_INTERN_STATUS_OPTIONS.map((o) => o.value)
    expect(values).toEqual(Object.values(SAD_INTERN_STATUS))
  })
})
