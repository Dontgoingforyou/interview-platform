import { describe, expect, it } from 'vitest'

import { DEBT_PAYMENT_STATUS_OPTIONS } from '../../constants/debtChoices'

describe('debtChoices', () => {
  it('payment status: searching/paying/unknown', () => {
    expect(DEBT_PAYMENT_STATUS_OPTIONS.map((o) => o.value)).toEqual([
      'searching',
      'paying',
      'unknown',
    ])
  })
})
