import { describe, expect, it } from 'vitest'

import {
  buildDebtByMonthParams,
  parseDebtByMonthFromSearchParams,
} from '../../../utils/debts/debtByMonthParams'

describe('buildDebtByMonthParams', () => {
  it('пустой без фильтров', () => {
    expect(buildDebtByMonthParams({})).toEqual({})
  })

  it('передаёт диапазон и фильтр статуса', () => {
    expect(
      buildDebtByMonthParams({
        page: 2,
        month_from: 1,
        year_from: 2024,
        month_to: 6,
        year_to: 2025,
        payment_status_filter: 'paying',
      }),
    ).toEqual({
      page: 2,
      month_from: 1,
      year_from: 2024,
      month_to: 6,
      year_to: 2025,
      payment_status_filter: 'paying',
    })
  })
})

describe('parseDebtByMonthFromSearchParams', () => {
  it('дефолт page=1', () => {
    expect(parseDebtByMonthFromSearchParams(new URLSearchParams()).page).toBe(1)
  })

  it('читает валидные числа и игнорирует NaN', () => {
    const sp = new URLSearchParams(
      'page=3&month_from=2&year_from=2024&month_to=8&year_to=2025&payment_status_filter=searching',
    )
    expect(parseDebtByMonthFromSearchParams(sp)).toEqual({
      page: 3,
      month_from: 2,
      year_from: 2024,
      month_to: 8,
      year_to: 2025,
      payment_status_filter: 'searching',
    })

    const bad = parseDebtByMonthFromSearchParams(
      new URLSearchParams('page=0&month_from=x&year_from=y&month_to=z&year_to=w'),
    )
    expect(bad.page).toBe(1)
    expect(bad.month_from).toBeUndefined()
    expect(bad.year_from).toBeUndefined()
  })
})
